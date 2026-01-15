from flask import Flask, render_template, request

from planner import build_plan, load_courses, parse_completed, validate_completed


app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    courses = load_courses()
    return render_template("index.html", courses=courses, tracks=["Data Analytics", "Systems", "Interface Design", "Business"])


@app.route("/plan", methods=["POST"])
def plan():
    track = request.form.get("track", "Data Analytics")
    max_credits = int(request.form.get("max_credits", 18))
    completed_raw = request.form.get("completed", "")

    completed_list = parse_completed(completed_raw)
    courses = load_courses()
    completed, unknown = validate_completed(courses, completed_list)

    plan_data = build_plan(track, completed, max_credits)

    completed_count = len(completed)
    remaining_required = plan_data["plan"]["remaining_needed"]

    return render_template(
        "results.html",
        track=track,
        max_credits=max_credits,
        completed_raw=completed_raw,
        completed=sorted(completed),
        completed_count=completed_count,
        remaining_required=remaining_required,
        unknown=unknown,
        plan=plan_data["plan"],
        summary=plan_data["summary"],
        eligible_courses=plan_data["eligible_courses"],
        constraint_warnings=plan_data["constraint_warnings"],
        courses=plan_data["courses"],
        requirements=plan_data["requirements"],
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
