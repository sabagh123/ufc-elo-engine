# UFC Elo Engine

A transparent Python project that reconstructs UFC fighter ratings by
processing completed fights in chronological order.

The first version intentionally uses ordinary Elo rather than machine
learning. This gives the project an explainable, testable baseline before any
subjective bonuses or more complicated models are considered.

## Current status

Version `0.1` contains:

- a normalized fight-history CSV schema;
- a converter for the TidyTuesday 2026-07-07 `ufc_fights.csv` dataset;
- a basic Elo engine with a starting rating of `1500` and `K = 32`;
- support for wins, losses, draws, and no contests;
- stable event, fight, and optional fighter IDs;
- explicit bout order for early same-day tournaments;
- CSV ranking output;
- automated tests for imports, chronology, CSV handling, and Elo mathematics.

The pipeline is:

```text
reusable source CSV -> normalized fights.csv -> Elo engine -> rankings.csv
```

## Why the project does not scrape UFCStats

UFCStats links to the current [UFC Terms of
Use](https://www.ufc.com/terms), which prohibit automated page-scraping,
robots, and spiders. This repository therefore does not automatically request
UFCStats pages.

For a portfolio project, using a published reusable dataset is more defensible
than ignoring a source site's rules. The import layer remains separate from
the Elo engine, so a different properly licensed dataset can be added later
without changing the rating mathematics.

The currently supported input is the `ufc_fights.csv` file published for
[TidyTuesday 2026-07-07](https://github.com/rfordatascience/tidytuesday/tree/main/data/2026/2026-07-07).
TidyTuesday explicitly provides direct download instructions and encourages
people to create and share analyses. Always retain the source attribution and
recheck the applicable data terms before redistributing a source dataset.

Generated source and normalized data remain ignored by Git. The project code,
small fictional sample, and tests can be public without automatically
republishing thousands of third-party records.

## Project structure

```text
ufc-elo-engine/
├── data/
│   ├── raw/                  # Downloaded/generated files (not committed)
│   └── sample_fights.csv     # Small fictional test dataset
├── outputs/                  # Generated rankings (not committed)
├── scripts/
│   ├── build_rankings.py
│   └── import_fights.py
├── src/ufc_elo/
│   ├── csv_io.py
│   ├── data_import.py
│   ├── engine.py
│   └── models.py
├── tests/
├── pyproject.toml
└── README.md
```

## One-time setup on Windows

Install:

1. [Python](https://www.python.org/downloads/)
2. [Visual Studio Code](https://code.visualstudio.com/)
3. [GitHub Desktop](https://desktop.github.com/)

Clone the repository in GitHub Desktop, then open it in VS Code. Open
**Terminal -> New Terminal** and run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
```

Using the virtual environment's Python directly avoids PowerShell activation
policy problems.

## Run the fictional sample

```powershell
.\.venv\Scripts\python.exe scripts\build_rankings.py
```

This reads `data/sample_fights.csv` and writes:

```text
outputs/rankings.csv
```

You can also change the model settings:

```powershell
.\.venv\Scripts\python.exe scripts\build_rankings.py `
  --k-factor 24 `
  --minimum-fights 1
```

## Import historical fight data

1. Open the [TidyTuesday UFC data
   page](https://github.com/rfordatascience/tidytuesday/tree/main/data/2026/2026-07-07).
2. Download `ufc_fights.csv`.
3. Put it in `data/raw/` as `tidytuesday_ufc_fights.csv`.
4. Run:

```powershell
.\.venv\Scripts\python.exe scripts\import_fights.py `
  --input data/raw/tidytuesday_ufc_fights.csv
```

The importer:

- validates the expected source columns;
- normalizes win, loss, draw, and no-contest values;
- derives stable event and fight identifiers;
- reverses each main-event-first event group;
- assigns explicit `bout_order` values;
- detects duplicate fight IDs;
- writes `data/raw/ufc_fights.csv`.

Then generate the historical rankings:

```powershell
.\.venv\Scripts\python.exe scripts\build_rankings.py `
  --input data/raw/ufc_fights.csv `
  --output outputs/ufc_rankings.csv
```

The TidyTuesday source does not provide stable fighter profile IDs in its fight
table. The engine therefore falls back to exact fighter names for that source.
Its normalized schema already supports fighter IDs when a future source
provides them.

## Normalized fight schema

| Column | Meaning |
|---|---|
| `event_date` | ISO event date |
| `event_name` | Event title |
| `event_id` | Stable event identifier |
| `bout_order` | Opening bout is 1, then increases |
| `fight_id` | Stable fight identifier |
| `fighter_a_id` | Optional stable source ID |
| `fighter_a` | First fighter display name |
| `fighter_b_id` | Optional stable source ID |
| `fighter_b` | Second fighter display name |
| `result` | Normalized result from fighter A's view |
| `weight_class` | Bout division/category |
| `method` | Listed result method |
| `round` | Ending round |
| `time` | Ending time in the round |
| `source_url` | Auditable source reference |

`bout_order` matters because early UFC events used same-night tournaments. A
fighter's second match must not be rated before their first match.

## Elo model

Fighter A's expected score is:

```text
E_A = 1 / (1 + 10 ^ ((R_B - R_A) / 400))
```

The rating update is:

```text
R_A_new = R_A + K * (S_A - E_A)
```

Where:

- `R_A` and `R_B` are pre-fight ratings;
- `S_A` is `1` for a win, `0` for a loss, or `0.5` for a draw;
- `K` is `32` by default;
- every new fighter starts at `1500`;
- a no contest changes the displayed record but not either rating.

For two new fighters, the winner gains 16 points and the loser loses 16:

```text
Winner: 1516
Loser:  1484
```

## Important limitations

This is an analytical baseline, not an official UFC ranking and not proof that
one fighter would defeat another today.

- One global rating mixes weight classes.
- Inactive and retired fighters remain in the historical table.
- Every rated result uses the same K-factor.
- Method, round, and margin are intentionally ignored.
- Fighters debut at 1500 even when they enter with different experience.
- Name-based identity can split aliases until a source provides fighter IDs.
- Historical source data may contain corrections or omissions.

These limitations should be measured before adding more complicated rules.

## GitHub workflow

`main` remains the stable branch. New work belongs in a feature branch and a
draft pull request:

1. Make and test a focused change.
2. Commit it to the feature branch.
3. Push the branch.
4. Review the draft pull request's **Files changed** and checks.
5. Merge only after the code and data assumptions have been verified.

After a pull request is merged, switch to `main` in GitHub Desktop, click
**Fetch origin**, and then **Pull origin**.

## Roadmap

- Validate the TidyTuesday import on UFC 1 and several modern events.
- Add a data-quality report for duplicates, missing values, and aliases.
- Generate the first full historical Elo ranking.
- Compare global Elo with division-specific ratings.
- Add rating history and rankings for a selected date.
- Evaluate prediction accuracy on later fights.
- Tune the K-factor using historical validation.
- Add a small dashboard after the data and model are reliable.

## License

The project source code is available under the MIT License. Third-party source
data remains subject to its own terms and attribution requirements.
