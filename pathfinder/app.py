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

    warnings = []
    for warning in plan_data["constraint_warnings"]:
        details = []
        if warning["constraints"]:
            details.append(", ".join(warning["constraints"]))
        if warning["notes"]:
            details.append(" ".join(warning["notes"]))
        if details:
            warnings.append(f"{warning['course']}: {' | '.join(details)}")

    eligible = []
    for code in plan_data["eligible_courses"]:
        prereq_rules = prereqs.get(code, {})
        prereq_list = []
        if prereq_rules.get("all"):
            prereq_list.append(f"All of: {', '.join(prereq_rules['all'])}")
        if prereq_rules.get("any"):
            prereq_list.append(f"One of: {', '.join(prereq_rules['any'])}")
        eligible.append(
            {
                "code": code,
                "name": courses[code].name,
                "credits": courses[code].credits,
                "prereqs": prereq_list,
            }
        )

    plan = []
    for index, semester in enumerate(plan_data["plan"]["semesters"], start=1):
        plan.append(
            {
                "name": f"Semester {index}",
                "credits": semester["credits"],
                "courses": [
                    {
                        "code": course_code,
                        "name": courses[course_code].name,
                        "credits": courses[course_code].credits,
                    }
                    for course_code in semester["courses"]
                ],
            }
        )

    remaining_requirements = []
    for group in plan_data["summary"]:
        missing = []
        if group["type"] == "choose_1_pair_from":
            if group["remaining"]:
                missing = [" + ".join(pair) for pair in group["remaining"]]
        else:
            missing = group["remaining"]
        remaining_requirements.append({"group": group["name"], "missing": missing})

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
        tracks=["Data Analytics", "Systems", "Interface Design", "Business"],
        result=result,
        selected_track=track,
        selected_mode=mode,
        completed_raw=completed_raw,
        max_credits=max_credits,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
