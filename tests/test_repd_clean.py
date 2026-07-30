from __future__ import annotations

from pathlib import Path

from src.repd_clean import read_snapshot


def test_csv_content_with_xlsx_extension_is_detected(tmp_path: Path) -> None:
    disguised = tmp_path / "2026-01-01_repd.xlsx"
    disguised.write_text(
        "Ref ID,Site Name,Technology Type,Installed Capacity (MWelec),"
        "Development Status,Region\n"
        "1,Example Solar,Solar Photovoltaics,10,Planning,North West\n",
        encoding="utf-8",
    )
    frame = read_snapshot(disguised)
    assert len(frame) == 1
    assert frame.loc[0, "Site Name"] == "Example Solar"
