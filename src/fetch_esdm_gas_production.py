#!/usr/bin/env python3
"""Fetch Indonesia ESDM daily gas production from the public homepage.

The ESDM homepage currently server-renders the latest EMR Highlight card.
This script extracts the Gas Production actual/target/date and appends it
as one row per date to data/esdm_indonesia_daily_gas_production.csv.
"""

from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://www.esdm.go.id/en"
OUTPUT_CSV = Path("data/esdm_indonesia_daily_gas_production.csv")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
}


@dataclass(frozen=True)
class GasProductionRecord:
    date: str
    indicator: str
    actual: int
    target: int
    unit: str
    source_url: str
    fetched_at_utc: str


def _to_int(value: str) -> int:
    return int(value.replace(",", "").replace(".", ""))


def _normalise_date(value: str) -> str:
    # Example input: "20 May 2026" -> "2026-05-20"
    dt = datetime.strptime(value.strip(), "%d %B %Y")
    return dt.date().isoformat()


def fetch_homepage_text() -> str:
    response = requests.get(SOURCE_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.get_text("\n", strip=True)


def parse_gas_production(text: str) -> GasProductionRecord:
    # The homepage card is expected to look like:
    # Gas Production \n 6,402 \n MMSCFD \n 5,508 \n MMSCFD \n 20 May 2026
    pattern = re.compile(
        r"Gas Production\s*"
        r"([\d,.]+)\s*MMSCFD\s*"
        r"([\d,.]+)\s*MMSCFD\s*"
        r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        flags=re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        snippet = text[:2000]
        raise RuntimeError(
            "Gas Production card not found. The website layout may have changed. "
            f"First 2000 chars of page text:\n{snippet}"
        )

    actual_raw, target_raw, date_raw = match.groups()
    return GasProductionRecord(
        date=_normalise_date(date_raw),
        indicator="Gas Production",
        actual=_to_int(actual_raw),
        target=_to_int(target_raw),
        unit="MMSCFD",
        source_url=SOURCE_URL,
        fetched_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )


def read_existing_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "date",
        "indicator",
        "actual",
        "target",
        "unit",
        "source_url",
        "fetched_at_utc",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def upsert_record(path: Path, record: GasProductionRecord) -> bool:
    rows = read_existing_rows(path)
    record_dict = {k: str(v) for k, v in asdict(record).items()}

    replaced = False
    changed = False
    new_rows: list[dict[str, str]] = []

    for row in rows:
        if row.get("date") == record.date and row.get("indicator") == record.indicator:
            replaced = True
            if row != record_dict:
                new_rows.append(record_dict)
                changed = True
            else:
                new_rows.append(row)
        else:
            new_rows.append(row)

    if not replaced:
        new_rows.append(record_dict)
        changed = True

    new_rows.sort(key=lambda r: (r.get("date", ""), r.get("indicator", "")))

    if changed:
        write_rows(path, new_rows)

    return changed


def main() -> None:
    text = fetch_homepage_text()
    record = parse_gas_production(text)
    changed = upsert_record(OUTPUT_CSV, record)

    print(asdict(record))
    if changed:
        print(f"Updated {OUTPUT_CSV}")
    else:
        print("No CSV change; latest record already exists with identical values.")


if __name__ == "__main__":
    main()
