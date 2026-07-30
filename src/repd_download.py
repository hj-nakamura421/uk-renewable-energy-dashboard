from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

GOV_PAGE_URLS = (
    "https://www.gov.uk/government/publications/renewable-energy-planning-database-quarterly-extract",
    "https://www.gov.uk/government/publications/renewable-energy-planning-database-monthly-extract",
)
WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"
WAYBACK_WEB = "https://web.archive.org/web"
ALLOWED_SUFFIXES = {".csv", ".xlsx", ".xls"}


@dataclass(frozen=True)
class DownloadRecord:
    snapshot_date: str
    source_page: str
    asset_url: str
    local_file: str
    sha256: str
    source: str


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "UK-Renewable-Forecasting-Research/1.0 "
                "(+https://github.com/hj-nakamura421)"
            ),
            "Accept": "text/html,application/xhtml+xml,application/json,*/*",
        }
    )
    return session


def _get(session: requests.Session, url: str, *, timeout: int = 45) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt == 3:
                break
            time.sleep(2**attempt)
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def _suffix_from_url(url: str) -> str:
    path = urlparse(url).path.lower()
    for suffix in ALLOWED_SUFFIXES:
        if path.endswith(suffix):
            return suffix
    return ""


def _asset_score(url: str, text: str) -> int:
    value = f"{url} {text}".lower()
    score = 0
    if "repd" in value:
        score += 8
    if "renewable" in value and "planning" in value:
        score += 5
    if "database" in value or "publication" in value:
        score += 3
    if ".csv" in value:
        score += 4
    if ".xlsx" in value:
        score += 2
    if "summary" in value or "heat" in value or "hnpd" in value:
        score -= 10
    return score


def extract_best_asset(page_html: str, page_url: str) -> str | None:
    soup = BeautifulSoup(page_html, "lxml")
    candidates: list[tuple[int, str]] = []
    for link in soup.find_all("a", href=True):
        href = urljoin(page_url, link["href"])
        if _suffix_from_url(href) not in ALLOWED_SUFFIXES:
            continue
        text = " ".join(link.get_text(" ", strip=True).split())
        candidates.append((_asset_score(href, text), href))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _normalise_asset_url(url: str) -> str:
    match = re.search(r"https?://web\.archive\.org/web/\d+(?:id_)?/(https?://.+)", url)
    return match.group(1) if match else url


def discover_wayback_pages(
    session: requests.Session,
    *,
    start_year: int,
    end_year: int,
    frequency: str = "quarterly",
) -> list[tuple[str, str]]:
    captures: dict[str, tuple[str, str]] = {}
    collapse = "timestamp:6" if frequency == "monthly" else "timestamp:6"

    for page_url in GOV_PAGE_URLS:
        params = {
            "url": page_url,
            "output": "json",
            "filter": ["statuscode:200", "mimetype:text/html"],
            "from": str(start_year),
            "to": str(end_year),
            "fl": "timestamp,original",
            "collapse": collapse,
        }
        response = session.get(WAYBACK_CDX, params=params, timeout=60)
        response.raise_for_status()
        rows = response.json()
        if not rows:
            continue
        header, *data_rows = rows
        timestamp_idx = header.index("timestamp")
        original_idx = header.index("original")
        for row in data_rows:
            timestamp = row[timestamp_idx]
            original = row[original_idx]
            dt = datetime.strptime(timestamp[:8], "%Y%m%d")
            if frequency == "quarterly":
                quarter = (dt.month - 1) // 3 + 1
                key = f"{dt.year}-Q{quarter}"
            else:
                key = f"{dt.year}-{dt.month:02d}"
            current = captures.get(key)
            if current is None or timestamp > current[0]:
                captures[key] = (timestamp, original)

    return sorted(captures.values(), key=lambda item: item[0])


def _download_binary(
    session: requests.Session,
    url_candidates: Iterable[str],
) -> tuple[bytes, str]:
    errors: list[str] = []
    for url in url_candidates:
        try:
            response = _get(session, url, timeout=90)
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" in content_type and len(response.content) < 200_000:
                errors.append(f"{url}: returned HTML")
                continue
            return response.content, url
        except Exception as exc:  # noqa: BLE001 - report all candidate failures
            errors.append(f"{url}: {exc}")
    raise RuntimeError("; ".join(errors))


def download_historical_repd(
    output_dir: Path,
    *,
    start_year: int = 2014,
    end_year: int | None = None,
    frequency: str = "quarterly",
    include_current: bool = True,
) -> list[DownloadRecord]:
    end_year = end_year or datetime.now().year
    output_dir.mkdir(parents=True, exist_ok=True)
    session = _session()
    records: list[DownloadRecord] = []
    seen_hashes: set[str] = set()

    try:
        pages = discover_wayback_pages(
            session,
            start_year=start_year,
            end_year=end_year,
            frequency=frequency,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Wayback discovery failed: {exc}")
        pages = []

    for index, (timestamp, original_page) in enumerate(pages, start=1):
        archived_page = f"{WAYBACK_WEB}/{timestamp}id_/{original_page}"
        try:
            html = _get(session, archived_page, timeout=60).text
            asset_url = extract_best_asset(html, original_page)
            if not asset_url:
                print(f"[{index}/{len(pages)}] No REPD asset found for {timestamp}")
                continue

            original_asset = _normalise_asset_url(asset_url)
            archived_asset = f"{WAYBACK_WEB}/{timestamp}id_/{original_asset}"
            content, used_url = _download_binary(session, [original_asset, archived_asset])
            digest = hashlib.sha256(content).hexdigest()
            if digest in seen_hashes:
                continue
            seen_hashes.add(digest)

            suffix = _suffix_from_url(original_asset) or ".xlsx"
            snapshot_date = datetime.strptime(timestamp[:8], "%Y%m%d").date().isoformat()
            filename = f"{snapshot_date}_repd{suffix}"
            path = output_dir / filename
            path.write_bytes(content)
            records.append(
                DownloadRecord(
                    snapshot_date=snapshot_date,
                    source_page=archived_page,
                    asset_url=used_url,
                    local_file=str(path),
                    sha256=digest,
                    source="wayback-official-govuk",
                )
            )
            print(f"[{index}/{len(pages)}] Downloaded {filename}")
            time.sleep(0.3)
        except Exception as exc:  # noqa: BLE001
            print(f"[{index}/{len(pages)}] Skipped {timestamp}: {exc}")

    if include_current:
        for page_url in GOV_PAGE_URLS:
            try:
                response = _get(session, page_url)
                asset_url = extract_best_asset(response.text, page_url)
                if not asset_url:
                    continue
                content, used_url = _download_binary(session, [asset_url])
                digest = hashlib.sha256(content).hexdigest()
                if digest in seen_hashes:
                    break
                suffix = _suffix_from_url(asset_url) or ".csv"
                snapshot_date = datetime.now().date().isoformat()
                path = output_dir / f"{snapshot_date}_repd_latest{suffix}"
                path.write_bytes(content)
                records.append(
                    DownloadRecord(
                        snapshot_date=snapshot_date,
                        source_page=page_url,
                        asset_url=used_url,
                        local_file=str(path),
                        sha256=digest,
                        source="official-govuk-current",
                    )
                )
                print(f"Downloaded current REPD file: {path.name}")
                break
            except Exception as exc:  # noqa: BLE001
                print(f"Current-page download failed for {page_url}: {exc}")

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps([asdict(record) for record in records], indent=2),
        encoding="utf-8",
    )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Download historical REPD snapshots.")
    parser.add_argument("--output", type=Path, default=Path("data/raw/repd"))
    parser.add_argument("--start-year", type=int, default=2014)
    parser.add_argument("--end-year", type=int, default=datetime.now().year)
    parser.add_argument("--frequency", choices=["quarterly", "monthly"], default="quarterly")
    args = parser.parse_args()

    records = download_historical_repd(
        args.output,
        start_year=args.start_year,
        end_year=args.end_year,
        frequency=args.frequency,
    )
    print(f"Saved {len(records)} unique snapshots to {args.output}")


if __name__ == "__main__":
    main()
