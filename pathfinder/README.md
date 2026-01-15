# Towson IS PathFinder

Towson IS PathFinder is a Flask web application that builds optimized semester-by-semester graduation plans for Towson University Information Systems students across every track (Data Analytics, Systems, Interface Design, and Business).

## Features

- Validates completed courses against the official curriculum input files.
- Evaluates prerequisites and displays advisory constraints (standing, GPA, consent).
- Builds an optimized plan that respects prerequisites, track rules, and credit caps.
- Summarizes remaining requirements by category.

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
