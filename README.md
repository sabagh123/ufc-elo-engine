# UFC Elo Engine

A transparent Python project that reconstructs UFC fighter ratings by
processing completed fights in chronological order.

The project intentionally starts with ordinary Elo instead of machine
learning. That gives us a baseline that is easy to explain, test, and improve.

## Current status

Version `0.1` contains:

- a UFCStats event-page scraper;
- a normalized CSV format for fight history;
- a basic Elo engine with a starting rating of `1500` and `K = 32`;
- support for wins, losses, draws, and no contests;
- CSV ranking output;
- automated tests for the scraper, CSV pipeline, and rating mathematics.

The scraper and the rating engine are separate on purpose:

```text
UFCStats pages -> normalized fights.csv -> Elo engine -> rankings.csv
```

If the source website changes, we fix the scraper without rewriting the Elo
math. If we improve the Elo model, we do not need to scrape the data again.

## Data source

The scraper targets the
[UFCStats completed-events index](http://ufcstats.com/statistics/events/completed?page=all).
That index includes historical event pages going back to UFC 1. Each completed
event page provides the event date, fighters, result, weight class, method,
round, and time.

Before running a full scrape or redistributing a complete dataset, check the
site's current terms and robots rules. The code identifies itself, restricts
requests to the UFCStats domain, and waits one second between event requests.
Do not reduce that delay aggressively.

Generated raw data is ignored by Git so that thousands of copied records are
not automatically committed to this repository.

## Project structure

```text
ufc-elo-engine/
├── data/
│   ├── raw/                  # Generated scrape output (not committed)
│   └── sample_fights.csv     # Small fictional dataset for a safe test run
├── outputs/                  # Generated ranking files
├── scripts/
│   ├── build_rankings.py
│   └── scrape_fights.py
├── src/ufc_elo/
│   ├── csv_io.py
│   ├── engine.py
│   ├── models.py
│   └── scraper.py
├── tests/
├── pyproject.toml
└── README.md
```

## One-time setup on Windows

You do not need to create another project folder manually if you use GitHub
Desktop. Cloning creates the folder for you.

Install:

1. [Python](https://www.python.org/downloads/)
2. [Visual Studio Code](https://code.visualstudio.com/)
3. [GitHub Desktop](https://desktop.github.com/)

Then:

1. Open GitHub Desktop and sign in.
2. Select **File -> Clone repository**.
3. Choose `sabagh123/ufc-elo-engine`.
4. Pick a normal location such as `Documents/GitHub`.
5. Click **Clone**.
6. In GitHub Desktop, click **Open in Visual Studio Code**.

The folder opened in VS Code is your local copy. GitHub holds the online copy.

Open the VS Code terminal with **Terminal -> New Terminal**, then run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev]"
pytest
```

If PowerShell blocks the activation script, you can skip activation and use
the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
```

## Run the Elo engine with sample data

The sample data uses fictional fighter names. It verifies the whole local
pipeline without depending on a website:

```powershell
python scripts/build_rankings.py
```

That writes:

```text
outputs/rankings.csv
```

You can also change the model settings:

```powershell
python scripts/build_rankings.py --k-factor 24 --minimum-fights 1
```

## Test the scraper carefully

Start with only the oldest event:

```powershell
python scripts/scrape_fights.py --max-events 1
```

The output is written to:

```text
data/raw/ufc_fights.csv
```

Open that file and confirm that the names, result, and event information look
correct before requesting every event.

After validation, a full run is:

```powershell
python scripts/scrape_fights.py
```

Then calculate ratings from the scraped file:

```powershell
python scripts/build_rankings.py `
  --input data/raw/ufc_fights.csv `
  --output outputs/ufc_rankings.csv
```

## Fight CSV schema

| Column | Meaning |
|---|---|
| `event_date` | ISO date such as `1993-11-12` |
| `event_name` | UFC event title |
| `fight_id` | UFCStats fight identifier |
| `fighter_a` | First fighter shown by the source |
| `fighter_b` | Second fighter shown by the source |
| `result` | `fighter_a_win`, `fighter_b_win`, `draw`, or `no_contest` |
| `weight_class` | Bout division from the event page |
| `method` | Decision, submission, KO/TKO, or other listed method |
| `round` | Ending round |
| `time` | Ending time in the round |

Only `event_date`, both fighter names, and `result` are required by the first
Elo model. The remaining columns give later versions room to test additional
ideas without rescraping.

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

- `R_A` and `R_B` are the fighters' ratings before the fight;
- `S_A` is `1` for a win, `0` for a loss, or `0.5` for a draw;
- `K` is `32` by default;
- every new fighter starts at `1500`;
- a no contest changes the record but not either rating.

For two new fighters, the winner gains 16 points and the loser loses 16:

```text
Winner: 1516
Loser:  1484
```

## Important limitations

The first ranking is a baseline, not an official UFC ranking and not proof that
one fighter would beat another today.

- Early UFC and modern UFC operated under different formats and divisions.
- One global rating mixes weight classes.
- Inactive and retired fighters stay in the historical table.
- Every rated result uses the same K-factor.
- Margin, method, round, and opponent preparation time are ignored.
- Fighters debut at 1500 even when they enter with very different experience.
- A name change or duplicate source identity could split one fighter's record.

Those are useful research questions for later versions, but adding subjective
bonuses before measuring the baseline would make the project harder to defend.

## How collaboration will work

`main` should remain the stable version. New work goes into a branch and a
draft pull request:

1. Create a branch for one feature.
2. Change and test the code.
3. Commit the change.
4. Push the branch to GitHub.
5. Open a draft pull request.
6. Review **Files changed** and the test results.
7. Merge only when the change makes sense.

When a pull request is merged online, open GitHub Desktop and click
**Fetch origin**, then **Pull origin**. That downloads the newest `main` branch
to your local folder.

Useful requests for future work include:

```text
Add weight-class-specific ratings on a new branch, test them, and open a draft
pull request. Do not merge it.
```

```text
Inspect the scraper failure, explain the cause, and propose a fix without
changing main.
```

## Roadmap

- Validate the scraper against a small set of live historical events.
- Generate the complete chronological fight CSV.
- Add data-quality checks for duplicate fights and unknown outcomes.
- Compare one global Elo table with division-specific tables.
- Add rating history and rankings for any selected date.
- Evaluate prediction accuracy on fights that occur later in time.
- Tune the K-factor using historical validation rather than guesswork.
- Add a small Streamlit dashboard only after the data and model are reliable.

## License

The source code is available under the MIT License. Source data remains subject
to the source website's applicable terms.
