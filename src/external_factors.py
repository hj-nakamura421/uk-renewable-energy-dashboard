from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd
import requests

ONS_CPI_URL = (
    "https://www.ons.gov.uk/economy/inflationandpriceindices/"
    "timeseries/d7g7/mm23/data"
)
ONS_CONSTRUCTION_OPI_URL = (
    "https://www.ons.gov.uk/file?uri=%2Fbusinessindustryandtrade%2F"
    "constructionindustry%2Fdatasets%2Finterimconstructionoutputpriceindices%2F"
    "current%2Fbulletindataset9.xlsx"
)
BOE_BANK_RATE_URL = (
    "https://www.bankofengland.co.uk/boeapps/database/"
    "_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/2014&"
    "Dateto=31/Dec/2030&SeriesCodes=IUDBEDR&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N"
)


@dataclass(frozen=True)
class ExternalSource:
    field: str
    name: str
    url: str
    licence: str
    note: str


SOURCES = (
    ExternalSource(
        field="cpi_annual_pct",
        name="ONS Consumer Prices Index annual rate",
        url=ONS_CPI_URL,
        licence="Open Government Licence v3.0",
        note="Headline CPI is context; construction-specific inflation is more decision-relevant.",
    ),
    ExternalSource(
        field="construction_opi_annual_pct",
        name="ONS infrastructure Construction Output Price Index",
        url=ONS_CONSTRUCTION_OPI_URL,
        licence="Open Government Licence v3.0",
        note="Latest published vintage; historical values may contain later revisions.",
    ),
    ExternalSource(
        field="bank_rate_pct",
        name="Bank of England official Bank Rate",
        url=BOE_BANK_RATE_URL,
        licence="Bank of England database terms",
        note="Monthly value uses the final published daily observation in each month.",
    ),
)


def _request(url: str, *, timeout: int = 45) -> requests.Response:
    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": (
                "UK-Renewable-Forecasting-Research/2.0 "
                "(https://github.com/hj-nakamura421)"
            )
        },
    )
    response.raise_for_status()
    return response


def fetch_ons_cpi() -> pd.DataFrame:
    payload = _request(ONS_CPI_URL).json()
    rows = payload.get("months", [])
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("ONS CPI response did not contain monthly observations.")
    frame["date"] = pd.to_datetime(
        frame["year"].astype(str) + " " + frame["month"].astype(str),
        format="%Y %B",
        errors="coerce",
    )
    frame["cpi_annual_pct"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame[["date", "cpi_annual_pct"]].dropna().sort_values("date")


def fetch_bank_rate() -> pd.DataFrame:
    response = _request(BOE_BANK_RATE_URL)
    frame = pd.read_csv(StringIO(response.text))
    if "DATE" not in frame.columns or "IUDBEDR" not in frame.columns:
        raise RuntimeError("Bank of England response did not contain expected columns.")
    frame["date"] = pd.to_datetime(frame["DATE"], format="%d %b %Y", errors="coerce")
    frame["bank_rate_pct"] = pd.to_numeric(frame["IUDBEDR"], errors="coerce")
    frame = frame.dropna(subset=["date", "bank_rate_pct"]).sort_values("date")
    return (
        frame.set_index("date")["bank_rate_pct"]
        .resample("MS")
        .last()
        .ffill()
        .rename_axis("date")
        .reset_index()
    )


def _parse_ons_months(values: pd.Series) -> pd.Series:
    year = values.astype(str).str.extract(r"^(\d{4})", expand=False).ffill()
    month = values.astype(str).str.extract(r"([A-Za-z]{3})$", expand=False)
    return pd.to_datetime(year + " " + month, format="%Y %b", errors="coerce")


def fetch_construction_opi() -> pd.DataFrame:
    response = _request(ONS_CONSTRUCTION_OPI_URL, timeout=90)
    raw = pd.read_excel(BytesIO(response.content), sheet_name="New work", header=None)
    if len(raw) < 8:
        raise RuntimeError("ONS construction price workbook was unexpectedly short.")
    header_row = raw.index[
        raw.iloc[:, 0].astype(str).str.strip().eq("Time period")
    ]
    if len(header_row) != 1:
        raise RuntimeError("Could not locate the ONS construction price table header.")
    header_index = int(header_row[0])
    frame = raw.iloc[header_index + 1 :].copy()
    frame.columns = raw.iloc[header_index].astype(str).str.strip()
    infrastructure_index = next(
        column
        for column in frame.columns
        if column.startswith("Infrastructure") and "index" in column
    )
    infrastructure_annual = next(
        column
        for column in frame.columns
        if column.startswith("Infrastructure") and "12 months" in column
    )
    result = pd.DataFrame(
        {
            "date": _parse_ons_months(frame["Time period"]),
            "construction_opi_index": pd.to_numeric(
                frame[infrastructure_index], errors="coerce"
            ),
            "construction_opi_annual_pct": pd.to_numeric(
                frame[infrastructure_annual], errors="coerce"
            ),
        }
    )
    return result.dropna(subset=["date"]).sort_values("date")


def build_external_context() -> tuple[pd.DataFrame, dict]:
    cpi = fetch_ons_cpi()
    bank = fetch_bank_rate()
    construction = fetch_construction_opi()
    first_date = min(frame["date"].min() for frame in (cpi, bank, construction))
    last_date = max(frame["date"].max() for frame in (cpi, bank, construction))
    months = pd.DataFrame({"date": pd.date_range(first_date, last_date, freq="MS")})
    context = months.merge(cpi, on="date", how="left")
    context = context.merge(bank, on="date", how="left")
    context = context.merge(construction, on="date", how="left")
    context = context.sort_values("date")
    for column in (
        "cpi_annual_pct",
        "bank_rate_pct",
        "construction_opi_index",
        "construction_opi_annual_pct",
    ):
        context[column] = context[column].ffill()
    metadata = {
        "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "latest_month": str(context["date"].max().date()),
        "sources": [asdict(source) for source in SOURCES],
        "warnings": [
            "External context is not used as a trained model feature while only a small "
            "number of independent REPD snapshots are available.",
            "Scenario impacts are transparent stress assumptions, not causal estimates.",
            "ONS construction history is the latest published vintage and may include revisions.",
        ],
    }
    return context, metadata


def refresh_external_context(
    output_path: Path,
    metadata_path: Path,
) -> pd.DataFrame:
    context, metadata = build_external_context()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    context.to_csv(output_path, index=False)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return context


def load_external_context(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    return frame.dropna(subset=["date"]).sort_values("date")
