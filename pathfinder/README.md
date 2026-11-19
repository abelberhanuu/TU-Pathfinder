# PathFinder application details

For installation and dependency setup, see the [repository README](../README.md).

## Workflow

1. Choose one of four configured IS tracks.
2. Enter completed courses, their credits, terms, and TU Core/repeat flags.
3. Choose a semester credit cap; the form clamps it to **12–21 credits**.
4. View eligible courses, remaining requirement groups, a proposed semester plan, and advisory warnings.

## Data flow

`courses.csv → Pandas → SQLAlchemy / in-memory SQLite → Course records → prerequisite and requirement rules → Flask results`

The database is recreated in memory when the catalog is loaded. This implementation uses SQLite locally; PostgreSQL is not required to run the application.

## Outputs

| Output | Meaning |
| --- | --- |
| Eligible courses | Needed courses whose configured course-prerequisite checks pass |
| Semester plan | A heuristic ordering under the selected credit cap |
| Remaining requirements | Required courses, elective choices, and track groups still missing |
| Course classifications | Major requirement, major elective, TU Core, free elective, or unknown |
| Credit summary | Counted credits and TU Core course count |
| Warnings | Duplicates, missing credits, and advisory standing/GPA/consent conditions |

## Example checks

These are documented scenarios to try manually, not an automated test report.

| Input | Expected classification or behavior |
| --- | --- |
| `CIS 211`, 3 credits | `MAJOR_REQUIREMENT` |
| `CIS 426`, 3 credits | `MAJOR_ELECTIVE` |
| `HIST 102`, 3 credits, TU Core checked | `TU_CORE`; increments TU Core count |
| `HIST 102`, 3 credits, TU Core unchecked | `FREE_ELECTIVE` |
| Course with missing credits | `UNKNOWN`; counts zero credits |
| Same course entered twice in the same term | Second entry contributes zero credits |
| Course repeated in another term | Credits counted only once |

## Files used at runtime

- [courses.csv](courses.csv): 72 catalog entries, including courses and constraint/eligibility markers.
- [prereqs.json](prereqs.json): course prerequisites and advisory conditions.
- [requirements.json](requirements.json): common requirements and four tracks.
- [planner.py](planner.py): data access, classification, and scheduling logic.
- [app.py](app.py): form handling and result construction.

## Interpretation

The configured degree targets are 120 credits and 14 TU Core courses. Missing or outdated rules can change results. The interface is a planning aid; verify decisions against the applicable catalog and academic advising.

The scheduler is heuristic. It favors downstream prerequisite unlocks and respects its numeric credit cap, but does not model actual course offerings or establish an optimal graduation date.
