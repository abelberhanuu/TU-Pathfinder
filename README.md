# Towson IS PathFinder

A Python/Flask decision-support application that translates curriculum requirements and prerequisite rules into eligible-course lists and semester-by-semester plans.

## Technical contribution

- **Data processing:** Pandas loads the course CSV; SQLAlchemy writes and reads the catalog through an in-memory SQLite database.
- **Decision logic:** prerequisite checks, track requirements, elective choices, and credit limits guide course eligibility and scheduling.
- **Reporting:** the web interface displays remaining requirements, course classifications, completed-credit totals, warnings, and a proposed plan.

## Scope and outcome

The checked-in data contains **72 catalog entries**, including course records and eligibility/standing markers, and **4 configured tracks**: Data Analytics, Systems, Interface Design, and Business.

The application makes curriculum rules inspectable and produces a proposed plan from user-entered course history. Its interface checks progress against configured targets of **14 TU Core courses** and **120 total credits**. These are application settings, not a guarantee of academic eligibility or graduation.

There are no measured adoption, time-savings, or accuracy results attached to this repository.

## Run locally

Use a fresh Python environment; Python 3.11+ is the documented target.

```bash
git clone https://github.com/abelberhanuu/TU-Pathfinder.git
cd TU-Pathfinder
python -m venv .venv
```

Activate it:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1
```

Install the runtime dependencies and start the local development server:

```bash
python -m pip install -r requirements.txt
cd pathfinder
python app.py
```

Open **http://localhost:8000**. The checked-in entry point enables Flask debugging and binds to all interfaces; use it on a trusted development machine.

## Repository map

| Path | Purpose |
| --- | --- |
| [pathfinder/app.py](pathfinder/app.py) | Flask route, form parsing, and presentation data |
| [pathfinder/planner.py](pathfinder/planner.py) | Data loading, classification, prerequisites, and planning |
| [pathfinder/courses.csv](pathfinder/courses.csv) | Active catalog input |
| [pathfinder/prereqs.json](pathfinder/prereqs.json) | Active prerequisite and advisory rules |
| [pathfinder/requirements.json](pathfinder/requirements.json) | Active common and track-specific requirements |
| [pathfinder/templates/](pathfinder/templates/) | Web interface |
| [requirements.txt](requirements.txt) | Runtime dependencies |

The running planner reads data inside `pathfinder/`. Root-level data exports are separate from those active inputs.

## Limits and interpretation

- Standing, GPA, consent, and similar constraints are displayed as advisory warnings; they are not automatically enforced.
- Course ordering uses a heuristic that favors courses unlocking downstream requirements. It does not prove a globally optimal schedule.
- Results depend on the local data files and do not account for live course availability, advisor exceptions, or every catalog year.
- The source tree currently includes committed virtual-environment artifacts. The new ignore rules prevent new untracked artifacts from being added; they do not remove files already tracked.

See [application details and example checks](pathfinder/README.md) for the workflow and output interpretation.
