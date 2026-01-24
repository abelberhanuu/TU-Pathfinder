# Towson IS PathFinder

Towson IS PathFinder is a web-based degree planning tool built with **Python** and **Flask**.
It evaluates Information Systems program requirements and prerequisite relationships to generate valid, semester-by-semester course plans.

## Highlights

- Processes structured curriculum data with **Pandas** and **SQLAlchemy**-friendly inputs to validate requirements and build schedules.
- Implements rule-based planning logic across **70+ courses** spanning all IS tracks.
- Supports accurate degree progress tracking and on-time graduation planning for **4,000+ students**.

## Repository Layout

- `pathfinder/`: Flask application code, templates, and static assets.
- `courses.csv`, `prereqs.json`, `requirements.json`: Curriculum data consumed by the planner.
- `course_code,course_name,credits,category.csv`: Catalog data export used to build the course list.

## Quickstart

1. Change into the application directory:
   ```bash
   cd pathfinder
   ```
2. Install dependencies:
   ```bash
   pip install flask pandas sqlalchemy
   ```
3. Run the app:
   ```bash
   python app.py
   ```
4. Open `http://localhost:8000` in your browser.

For deeper project details (features, structure, and notes), see `pathfinder/README.md`.
