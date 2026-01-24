# TU-Pathfinder

TU-Pathfinder is a repository for a Towson University Information Systems graduation planner.
It contains the Flask web application under `pathfinder/` along with the curriculum data files it uses to build optimized semester-by-semester plans.

## Contents

- `pathfinder/`: Flask app, templates, and static assets.
- `courses.csv`, `prereqs.json`, `requirements.json`: Curriculum data consumed by the planner.
- `course_code,course_name,credits,category.csv`: Catalog data export used to build the course list.

## Getting Started

1. Change into the application directory:
   ```
   cd pathfinder
   ```
2. Install dependencies:
   ```
   pip install flask
   ```
3. Run the app:
   ```
   python app.py
   ```
4. Open `http://localhost:8000` in your browser.

For more detailed information about features and project structure, see `pathfinder/README.md`.
