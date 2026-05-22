# ESDM Indonesia Daily Gas Production

Daily tracker for Indonesia ESDM homepage **Gas Production** values.

The scraper reads the public ESDM English homepage, extracts the latest server-rendered **Gas Production** card, and appends or updates one row per date in:

```text
data/esdm_indonesia_daily_gas_production.csv
```

## Output schema

| Column | Description |
|---|---|
| `date` | Reported ESDM card date in `YYYY-MM-DD` format |
| `indicator` | `Gas Production` |
| `actual` | Actual gas production value |
| `target` | Target gas production value |
| `unit` | `MMSCFD` |
| `source_url` | Source page URL |
| `fetched_at_utc` | Timestamp when the scraper ran |

## Run locally

```bash
pip install -r requirements.txt
python src/fetch_esdm_gas_production.py
```

## GitHub Actions schedule

The workflow runs daily at **02:00 UTC**, which is **10:00 Asia/Singapore**.

It can also be run manually from the GitHub Actions tab via `workflow_dispatch`.

## Important limitation

The current public homepage exposes the latest Gas Production card only. It does not expose a confirmed public historical endpoint in the static HTML. Therefore, this tracker collects history prospectively by saving the daily homepage value each time the workflow runs.
