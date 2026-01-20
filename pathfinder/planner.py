import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


DATA_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Course:
    code: str
    name: str
    credits: int
    category: str
    track: Optional[str]


@dataclass(frozen=True)
class CourseEntry:
    code: str
    credits: Optional[int]
    term: str
    is_tu_core: bool
    is_repeat: bool


def normalize_course_code(raw: str) -> str:
    return " ".join(raw.strip().upper().split())


def load_courses() -> Dict[str, Course]:
    courses_path = DATA_DIR / "courses.csv"
    courses: Dict[str, Course] = {}
    with courses_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            code = normalize_course_code(row["course_code"])
            raw_track = row["track"].strip()
            track = None if raw_track.lower() in {"", "all", "none"} else raw_track
            courses[code] = Course(
                code=code,
                name=row["course_name"].strip(),
                credits=int(row["credits"]),
                category=row["category"].strip(),
                track=track,
            )
    return courses


def catalog_flags(course: Course) -> Tuple[bool, bool]:
    category = course.category.strip().lower()
    is_core = category in {"is core", "core", "required"} or category.endswith("core")
    is_elective = "elective" in category
    return is_core, is_elective


def required_course_set(track: str, requirements: Dict[str, object]) -> Set[str]:
    groups = requirement_groups(track, requirements)
    return set(groups["required_courses"])


def classify_course_entry(
    entry: CourseEntry,
    courses: Dict[str, Course],
    required_courses: Set[str],
) -> str:
    if entry.credits is None:
        return "UNKNOWN"

    catalog_course = courses.get(entry.code)
    if catalog_course:
        is_core, is_elective = catalog_flags(catalog_course)
        if is_core:
            return "MAJOR_REQUIREMENT"
        if is_elective or catalog_course.track is not None:
            return "MAJOR_ELECTIVE"
        if entry.code in required_courses:
            return "MAJOR_REQUIREMENT"
        return "UNKNOWN"

    if entry.is_tu_core:
        return "TU_CORE"
    return "FREE_ELECTIVE"


def evaluate_course_entries(
    entries: List[CourseEntry],
    courses: Dict[str, Course],
    required_courses: Set[str],
) -> Dict[str, object]:
    evaluations = []
    warnings = []
    seen_term_courses: Set[Tuple[str, str]] = set()
    seen_courses: Set[str] = set()
    total_credits_completed = 0
    tu_core_completed = 0
    has_unknown = False

    for entry in entries:
        label = classify_course_entry(entry, courses, required_courses)
        counted = True
        counted_credits = entry.credits or 0
        notes = []

        if entry.credits is None:
            notes.append("Missing credits; counted as 0.")

        term_key = (entry.code, entry.term)
        if term_key in seen_term_courses:
            counted = False
            counted_credits = 0
            notes.append("Duplicate in same term; not counted.")
        else:
            seen_term_courses.add(term_key)

        if counted:
            if entry.code in seen_courses:
                if entry.is_repeat:
                    counted = False
                    counted_credits = 0
                    notes.append("Repeat course; credits counted once.")
                else:
                    counted = False
                    counted_credits = 0
                    notes.append("Duplicate course; mark as repeat to keep it.")
            else:
                seen_courses.add(entry.code)

        if label == "UNKNOWN":
            has_unknown = True

        if counted:
            total_credits_completed += counted_credits
            if label == "TU_CORE":
                tu_core_completed += 1

        evaluations.append(
            {
                "code": entry.code,
                "term": entry.term,
                "credits": entry.credits,
                "is_tu_core": entry.is_tu_core,
                "is_repeat": entry.is_repeat,
                "label": label,
                "counted": counted,
                "counted_credits": counted_credits,
                "notes": notes,
            }
        )

        for note in notes:
            warnings.append(f"{entry.code}: {note}")

    return {
        "evaluations": evaluations,
        "warnings": warnings,
        "tu_core_completed": tu_core_completed,
        "total_credits_completed": total_credits_completed,
        "has_unknown": has_unknown,
    }


def load_prereqs() -> Dict[str, Dict[str, object]]:
    with (DATA_DIR / "prereqs.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def load_requirements() -> Dict[str, object]:
    with (DATA_DIR / "requirements.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_completed(raw: str) -> List[str]:
    if not raw:
        return []
    cleaned = raw.replace("\n", ",")
    parts = [normalize_course_code(part) for part in cleaned.split(",")]
    return [part for part in parts if part]


def validate_completed(courses: Dict[str, Course], completed: List[str]) -> Tuple[Set[str], List[str]]:
    known = set()
    unknown = []
    for code in completed:
        if code in courses:
            known.add(code)
        else:
            unknown.append(code)
    return known, unknown


def prereq_key(course_code: str, track: str, requirements: Dict[str, object]) -> str:
    if track == "Business":
        track_data = requirements["tracks"][track]
        elective_courses = set(track_data["electives"]["courses"])
        if course_code == "CIS 328" and course_code in elective_courses:
            return "CIS 328__BUSINESS_ELECTIVE"
    return course_code


def check_prereqs(
    course_code: str,
    completed: Set[str],
    prereqs: Dict[str, Dict[str, object]],
    track: str,
    requirements: Dict[str, object],
) -> Tuple[bool, List[str], List[str]]:
    key = prereq_key(course_code, track, requirements)
    rules = prereqs.get(key, {})
    unmet_constraints = list(rules.get("constraints", []))
    notes = []
    if "notes" in rules:
        notes.append(rules["notes"])

    if "all" in rules:
        if not all(req in completed for req in rules["all"]):
            return False, unmet_constraints, notes
    if "any" in rules:
        if not any(req in completed for req in rules["any"]):
            return False, unmet_constraints, notes
    return True, unmet_constraints, notes


def build_dependency_map(prereqs: Dict[str, Dict[str, object]]) -> Dict[str, Set[str]]:
    dependents: Dict[str, Set[str]] = {}
    for course, rules in prereqs.items():
        for key in ("all", "any"):
            for prereq in rules.get(key, []):
                dependents.setdefault(prereq, set()).add(course)
    return dependents


def missing_prereq_count(
    course_code: str,
    completed: Set[str],
    prereqs: Dict[str, Dict[str, object]],
    track: str,
    requirements: Dict[str, object],
) -> int:
    key = prereq_key(course_code, track, requirements)
    rules = prereqs.get(key, {})
    missing = 0
    if "all" in rules:
        missing += sum(1 for req in rules["all"] if req not in completed)
    if "any" in rules:
        if not any(req in completed for req in rules["any"]):
            missing += 1
    return missing


def extract_requirements(track: str, requirements: Dict[str, object]) -> Dict[str, object]:
    track_data = requirements["tracks"][track]
    return {
        "common": requirements["requirements_common"],
        "math": track_data["math"],
        "track_requirements": track_data["track_requirements"],
        "electives": track_data["electives"],
    }


def requirement_groups(track: str, requirements: Dict[str, object]) -> Dict[str, object]:
    extracted = extract_requirements(track, requirements)
    required_courses: Set[str] = set()
    one_of_groups: List[Set[str]] = []
    choose_n_groups: List[Dict[str, object]] = []
    pair_groups: List[List[List[str]]] = []

    def handle_requirement(req: Dict[str, object]):
        req_type = req["type"]
        if req_type == "all_of":
            required_courses.update(req["courses"])
        elif req_type == "one_of":
            one_of_groups.append(set(req["courses"]))
        elif req_type == "choose_n_from":
            choose_n_groups.append({"options": set(req["courses"]), "n": req["n"]})
        elif req_type == "choose_1_pair_from":
            pair_groups.append(req["pairs"])
        elif req_type == "all_of_plus_one_of":
            required_courses.update(req["all_of"])
            one_of_groups.append(set(req["one_of"]))

    for req in extracted["common"]:
        handle_requirement(req)
    handle_requirement(extracted["math"])
    for req in extracted["track_requirements"]:
        handle_requirement(req)
    handle_requirement(extracted["electives"])

    return {
        "required_courses": required_courses,
        "one_of_groups": one_of_groups,
        "choose_n_groups": choose_n_groups,
        "pair_groups": pair_groups,
    }


def summarize_requirements(track: str, requirements: Dict[str, object], completed: Set[str]) -> List[Dict[str, object]]:
    extracted = extract_requirements(track, requirements)
    summary: List[Dict[str, object]] = []

    def add_entry(name: str, req_type: str, completed_courses: List[str], remaining: List[str], needed: Optional[int] = None):
        summary.append(
            {
                "name": name,
                "type": req_type,
                "completed": completed_courses,
                "remaining": remaining,
                "needed": needed,
            }
        )

    def handle(req: Dict[str, object]):
        req_type = req["type"]
        if req_type == "all_of":
            courses = req["courses"]
            completed_courses = [c for c in courses if c in completed]
            remaining = [c for c in courses if c not in completed]
            add_entry(req["name"], req_type, completed_courses, remaining)
        elif req_type == "one_of":
            courses = req["courses"]
            completed_courses = [c for c in courses if c in completed]
            remaining = [c for c in courses if c not in completed]
            add_entry(req["name"], req_type, completed_courses, remaining, needed=0 if completed_courses else 1)
        elif req_type == "choose_n_from":
            courses = req["courses"]
            completed_courses = [c for c in courses if c in completed]
            remaining = [c for c in courses if c not in completed]
            needed = max(req["n"] - len(completed_courses), 0)
            add_entry(req["name"], req_type, completed_courses, remaining, needed=needed)
        elif req_type == "choose_1_pair_from":
            pairs = req["pairs"]
            completed_pairs = [pair for pair in pairs if all(course in completed for course in pair)]
            remaining_pairs = [pair for pair in pairs if pair not in completed_pairs]
            add_entry(req["name"], req_type, completed_pairs, remaining_pairs, needed=0 if completed_pairs else 1)
        elif req_type == "all_of_plus_one_of":
            all_courses = req["all_of"]
            completed_all = [c for c in all_courses if c in completed]
            remaining_all = [c for c in all_courses if c not in completed]
            add_entry(f"{req['name']} (all of)", "all_of", completed_all, remaining_all)
            one_courses = req["one_of"]
            completed_one = [c for c in one_courses if c in completed]
            remaining_one = [c for c in one_courses if c not in completed]
            add_entry(f"{req['name']} (one of)", "one_of", completed_one, remaining_one, needed=0 if completed_one else 1)

    for req in extracted["common"]:
        handle(req)
    handle(extracted["math"])
    for req in extracted["track_requirements"]:
        handle(req)
    handle(extracted["electives"])

    return summary


def plan_semesters(
    track: str,
    completed: Set[str],
    courses: Dict[str, Course],
    prereqs: Dict[str, Dict[str, object]],
    requirements: Dict[str, object],
    max_credits: int,
    min_credits: int = 15,
) -> Dict[str, object]:
    groups = requirement_groups(track, requirements)
    required_courses = groups["required_courses"]
    one_of_groups = groups["one_of_groups"]
    choose_n_groups = groups["choose_n_groups"]
    pair_groups = groups["pair_groups"]

    dependents = build_dependency_map(prereqs)

    selected_pairs: Dict[int, List[str]] = {}

    def is_one_of_satisfied(options: Set[str]) -> bool:
        return any(option in completed for option in options)

    def one_of_needed(options: Set[str]) -> List[str]:
        if is_one_of_satisfied(options):
            return []
        return [option for option in options if option not in completed]

    def choose_n_needed(group: Dict[str, object]) -> List[str]:
        options = group["options"]
        completed_count = sum(1 for option in options if option in completed)
        if completed_count >= group["n"]:
            return []
        return [option for option in options if option not in completed]

    def pair_needed(index: int, pairs: List[List[str]]) -> List[str]:
        for pair in pairs:
            if all(course in completed for course in pair):
                return []
        if index not in selected_pairs:
            best_pair = None
            best_score = None
            for pair in pairs:
                missing = sum(
                    missing_prereq_count(course, completed, prereqs, track, requirements)
                    for course in pair
                )
                unlock = sum(len(dependents.get(course, [])) for course in pair)
                score = (missing, -unlock)
                if best_score is None or score < best_score:
                    best_score = score
                    best_pair = pair
            if best_pair:
                selected_pairs[index] = best_pair
        return [course for course in selected_pairs.get(index, []) if course not in completed]

    def needed_candidates() -> Set[str]:
        needed: Set[str] = set(course for course in required_courses if course not in completed)
        for options in one_of_groups:
            needed.update(one_of_needed(options))
        for group in choose_n_groups:
            needed.update(choose_n_needed(group))
        for index, pairs in enumerate(pair_groups):
            needed.update(pair_needed(index, pairs))
        return needed

    def remaining_requirements_count() -> int:
        count = len([course for course in required_courses if course not in completed])
        for options in one_of_groups:
            if not is_one_of_satisfied(options):
                count += 1
        for group in choose_n_groups:
            options = group["options"]
            completed_count = sum(1 for option in options if option in completed)
            if completed_count < group["n"]:
                count += group["n"] - completed_count
        for pairs in pair_groups:
            if not any(all(course in completed for course in pair) for pair in pairs):
                count += 2
        return count

    def unlock_score(course_code: str) -> int:
        return len([dep for dep in dependents.get(course_code, []) if dep not in completed])

    semesters = []
    blocked_courses: Set[str] = set()

    while remaining_requirements_count() > 0:
        candidates = needed_candidates()
        eligible = []
        warnings: Dict[str, Dict[str, List[str]]] = {}
        for course in candidates:
            if course not in courses:
                continue
            is_ok, constraints, notes = check_prereqs(course, completed, prereqs, track, requirements)
            if is_ok:
                eligible.append(course)
            if constraints or notes:
                warnings[course] = {"constraints": constraints, "notes": notes}

        if not eligible:
            blocked_courses.update(candidates)
            break

        eligible.sort(key=lambda code: (-unlock_score(code), -courses[code].credits, code))
        semester_courses = []
        total_credits = 0
        for course in eligible:
            credits = courses[course].credits
            if total_credits + credits <= max_credits:
                semester_courses.append(course)
                total_credits += credits
            if total_credits >= max_credits:
                break

        if total_credits < min_credits:
            for course in eligible:
                if course in semester_courses:
                    continue
                credits = courses[course].credits
                if total_credits + credits <= max_credits:
                    semester_courses.append(course)
                    total_credits += credits
                if total_credits >= min_credits:
                    break

        if not semester_courses:
            blocked_courses.update(candidates)
            break

        semesters.append({"courses": semester_courses, "credits": total_credits})
        completed.update(semester_courses)

    remaining_needed = remaining_requirements_count()

    return {
        "semesters": semesters,
        "blocked_courses": sorted(blocked_courses),
        "remaining_needed": remaining_needed,
    }


def build_plan(track: str, completed: Set[str], max_credits: int) -> Dict[str, object]:
    courses = load_courses()
    prereqs = load_prereqs()
    requirements = load_requirements()

    plan_result = plan_semesters(
        track,
        set(completed),
        courses,
        prereqs,
        requirements,
        max_credits,
    )

    needed_courses = set()
    groups = requirement_groups(track, requirements)
    needed_courses.update([course for course in groups["required_courses"] if course not in completed])
    for options in groups["one_of_groups"]:
        if not any(course in completed for course in options):
            needed_courses.update(course for course in options if course not in completed)
    for group in groups["choose_n_groups"]:
        options = group["options"]
        completed_count = sum(1 for option in options if option in completed)
        if completed_count < group["n"]:
            needed_courses.update(option for option in options if option not in completed)
    for pairs in groups["pair_groups"]:
        if not any(all(course in completed for course in pair) for pair in pairs):
            for pair in pairs:
                needed_courses.update(course for course in pair if course not in completed)

    eligible_courses = []
    constraint_warnings = []
    for course in sorted(needed_courses):
        if course not in courses:
            continue
        is_ok, constraints, notes = check_prereqs(course, completed, prereqs, track, requirements)
        if is_ok:
            eligible_courses.append(course)
        if constraints or notes:
            constraint_warnings.append(
                {
                    "course": course,
                    "constraints": constraints,
                    "notes": notes,
                }
            )

    return {
        "courses": courses,
        "requirements": requirements,
        "eligible_courses": eligible_courses,
        "constraint_warnings": constraint_warnings,
        "plan": plan_result,
        "summary": summarize_requirements(track, requirements, completed),
    }
