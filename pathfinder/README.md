# Towson IS PathFinder

Towson IS PathFinder is a Flask web application that builds optimized semester-by-semester graduation plans for Towson University Information Systems students across every track (Data Analytics, Systems, Interface Design, and Business).

## Features

- Validates completed courses against the official curriculum input files.
- Evaluates prerequisites and displays advisory constraints (standing, GPA, consent).
- Builds an optimized plan that respects prerequisites, track rules, and credit caps.
- Summarizes remaining requirements by category.
- Classifies each entered course as TU Core, major requirement, major elective, free elective, or unknown.
- Tracks TU Core completion (14 courses) and total credits (120 credits) without double counting.

## Project Structure

```
pathfinder/
  app.py
  planner.py
  courses.csv
  prereqs.json
  requirements.json
  templates/
    index.html
    results.html
  static/
    style.css
  README.md
```

## Running the App

1. Ensure Python 3.11 is available.
2. Install Flask:

```
pip install flask
```

3. Start the server:

```
python app.py
```

4. Visit `http://localhost:8000` in your browser.

## Data Sources

The planner reads three local data files:

- `courses.csv`: All course definitions, categories, and track tags.
- `prereqs.json`: Prerequisite logic and advisory constraints.
- `requirements.json`: Degree completion rules and track-specific requirements.

## Notes

- Constraint rules (standing, GPA, consent) are displayed as warnings but not enforced automatically.
- The optimizer favors courses that unlock downstream requirements and keeps semesters within the credit cap.
- Repeated courses must be marked as repeats to be accepted, and credits are only counted once. Duplicate entries in the same term are ignored.

## Course classification examples

Use these examples to sanity-check the labeling and credit counts. (Credits omitted are treated as 0 and labeled UNKNOWN.)

1. **Known major requirement (catalog core course)**  
   Input: `CIS 211`, 3 credits, not TU Core → Label: `MAJOR_REQUIREMENT`, TU Core: +0, Total credits: +3.
2. **Known major elective (catalog elective course)**  
   Input: `CIS 426`, 3 credits, not TU Core → Label: `MAJOR_ELECTIVE`, TU Core: +0, Total credits: +3.
3. **Missing-from-catalog course marked TU Core**  
   Input: `HIST 102`, 3 credits, TU Core checked → Label: `TU_CORE`, TU Core: +1, Total credits: +3.
4. **Missing-from-catalog course not marked TU Core**  
   Input: `HIST 102`, 3 credits, TU Core unchecked → Label: `FREE_ELECTIVE`, TU Core: +0, Total credits: +3.
5. **Course with missing credit value**  
   Input: `ENGL 102`, credits blank, TU Core unchecked → Label: `UNKNOWN`, TU Core: +0, Total credits: +0.
