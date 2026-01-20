from typing import List, Tuple

from flask import Flask, render_template, request

from planner import (
    CourseEntry,
    build_plan,
    evaluate_course_entries,
    load_courses,
    load_prereqs,
    load_requirements,
    normalize_course_code,
    required_course_set,
)

app = Flask(__name__)


def clamp_credits(value: int, minimum: int = 12, maximum: int = 21) -> int:
    return max(minimum, min(maximum, value))


def parse_course_entries(form: dict) -> Tuple[List[CourseEntry], List[dict]]:
    entries: List[CourseEntry] = []
    entry_forms: List[dict] = []
    count = int(form.get("course_row_count", 0))
    for index in range(count):
        code_raw = form.get(f"course_code_{index}", "").strip()
        credits_raw = form.get(f"course_credits_{index}", "").strip()
        term = form.get(f"course_term_{index}", "").strip()
        is_tu_core = form.get(f"course_is_tu_core_{index}") == "on"
        is_repeat = form.get(f"course_is_repeat_{index}") == "on"

        if not code_raw and not credits_raw and not term:
            continue

        credits_value = None
        if credits_raw:
            try:
                credits_value = int(credits_raw)
            except ValueError:
                credits_value = None

        normalized_code = normalize_course_code(code_raw) if code_raw else ""
        entry_forms.append(
            {
                "code": code_raw,
                "credits": credits_raw,
                "term": term,
                "is_tu_core": is_tu_core,
                "is_repeat": is_repeat,
            }
        )

        if normalized_code:
            entries.append(
                CourseEntry(
                    code=normalized_code,
                    credits=credits_value,
                    term=term,
                    is_tu_core=is_tu_core,
                    is_repeat=is_repeat,
                )
            )

    return entries, entry_forms


def build_course_entry_rows(entry_forms: List[dict], minimum_rows: int = 3) -> List[dict]:
    rows = list(entry_forms)
    while len(rows) < minimum_rows:
        rows.append(
            {"code": "", "credits": "", "term": "", "is_tu_core": False, "is_repeat": False}
        )
    return rows


def build_result(track: str, max_credits: int, course_entries: List[CourseEntry], mode: str) -> dict:
    courses = load_courses()
    prereqs = load_prereqs()
    requirements = load_requirements()

    completed = {entry.code for entry in course_entries if entry.code in courses}

    plan_data = build_plan(track, completed, max_credits)
    required_courses = required_course_set(track, requirements)
    entry_results = evaluate_course_entries(course_entries, courses, required_courses)

    # Build display warnings (constraints are displayed but not enforced)
    warnings = []
    for warning in plan_data.get("constraint_warnings", []):
        details = []
        if warning.get("constraints"):
            details.append(", ".join(warning["constraints"]))
        if warning.get("notes"):
            details.append(" ".join(warning["notes"]))
        if details:
            warnings.append(f"{warning.get('course', 'Course')}: {' | '.join(details)}")

    warnings.extend(entry_results.get("warnings", []))
    if entry_results.get("has_unknown"):
        warnings.append("Some courses are labeled UNKNOWN. Add credits or update TU Core flag.")
    if entry_results.get("tu_core_completed", 0) < 14:
        warnings.append("TU Core requirement not met yet (14 courses required).")
    if entry_results.get("total_credits_completed", 0) < 120:
        warnings.append("Total credits requirement not met yet (120 credits required).")

    # Build eligible list with prereq strings for UI
    eligible = []
    for code in plan_data.get("eligible_courses", []):
        prereq_rules = prereqs.get(code, {})
        prereq_list = []
        if prereq_rules.get("all"):
            prereq_list.append(f"All of: {', '.join(prereq_rules['all'])}")
        if prereq_rules.get("any"):
            prereq_list.append(f"One of: {', '.join(prereq_rules['any'])}")

        c = courses.get(code)
        eligible.append(
            {
                "code": code,
                "name": c.name if c else code,
                "credits": c.credits if c else 0,
                "prereqs": prereq_list,
            }
        )

    # Build semester-by-semester plan for UI
    plan = []
    for idx, semester in enumerate(plan_data.get("plan", {}).get("semesters", []), start=1):
        sem_courses = []
        for course_code in semester.get("courses", []):
            c = courses.get(course_code)
            sem_courses.append(
                {
                    "code": course_code,
                    "name": c.name if c else course_code,
                    "credits": c.credits if c else 0,
                }
            )
        plan.append(
            {
                "name": f"Semester {idx}",
                "credits": semester.get("credits", 0),
                "courses": sem_courses,
            }
        )

    # Remaining requirements summary for UI
    remaining_requirements = []
    for group in plan_data.get("summary", []):
        missing = []
        if group.get("type") == "choose_1_pair_from":
            if group.get("remaining"):
                missing = [" + ".join(pair) for pair in group["remaining"]]
        else:
            missing = group.get("remaining", [])
        remaining_requirements.append({"group": group.get("name", "Requirement"), "missing": missing})

    # If user only wants eligible courses, keep plan but template can hide it
    return {
        "track": track,
        "max_credits": max_credits,
        "mode": mode,
        "warnings": warnings,
        "eligible": eligible,
        "plan": plan,
        "remaining_requirements": remaining_requirements,
        "course_entries": entry_results.get("evaluations", []),
        "tu_core_completed": entry_results.get("tu_core_completed", 0),
        "total_credits_completed": entry_results.get("total_credits_completed", 0),
    }


@app.route("/", methods=["GET", "POST"])
def index():
    tracks = ["Data Analytics", "Systems", "Interface Design", "Business"]

    # defaults
    result = None
    course_entries = []
    track = "Data Analytics"
    mode = "plan"
    max_credits = 18
    course_entry_rows = build_course_entry_rows([])

    if request.method == "POST":
        track = request.form.get("track", track)
        mode = request.form.get("mode", mode)
        max_credits = clamp_credits(int(request.form.get("max_credits", max_credits)))

        course_entries, entry_forms = parse_course_entries(request.form)
        course_entry_rows = build_course_entry_rows(entry_forms)

        result = build_result(track, max_credits, course_entries, mode)

    return render_template(
        "index.html",
        tracks=tracks,
        result=result,
        selected_track=track,
        selected_mode=mode,
        max_credits=max_credits,
        course_entry_rows=course_entry_rows,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
