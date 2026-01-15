from flask import Flask, render_template, request

from planner import (
    build_plan,
    load_courses,
    load_prereqs,
    parse_completed,
    validate_completed,
)

app = Flask(__name__)


def clamp_credits(value: int, minimum: int = 12, maximum: int = 21) -> int:
    return max(minimum, min(maximum, value))


def build_result(track: str, max_credits: int, completed_raw: str, mode: str) -> dict:
    courses = load_courses()
    prereqs = load_prereqs()

    completed_list = parse_completed(completed_raw)
    completed, unknown = validate_completed(courses, completed_list)

    plan_data = build_plan(track, completed, max_credits)

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
        "unknown": unknown,
        "warnings": warnings,
        "eligible": eligible,
        "plan": plan,
        "remaining_requirements": remaining_requirements,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    tracks = ["Data Analytics", "Systems", "Interface Design", "Business"]

    # defaults
    result = None
    completed_raw = ""
    track = "Data Analytics"
    mode = "plan"
    max_credits = 18

    if request.method == "POST":
        track = request.form.get("track", track)
        mode = request.form.get("mode", mode)
        completed_raw = request.form.get("completed", "")
        max_credits = clamp_credits(int(request.form.get("max_credits", max_credits)))

        result = build_result(track, max_credits, completed_raw, mode)

    return render_template(
        "index.html",
        tracks=tracks,
        result=result,
        selected_track=track,
        selected_mode=mode,
        completed_raw=completed_raw,
        max_credits=max_credits,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
