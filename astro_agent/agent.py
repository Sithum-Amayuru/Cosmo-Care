"""Astronaut health guidance agent - DEMO.

Pipeline: profile + distance -> zone -> retrieve -> personalise -> flags -> report.
All logic is deterministic. An LLM can optionally be added at the end
(see explain_with_llm) to turn the plan into friendly text.

Usage:
    python agent.py A001 400
    python agent.py A002 54000000
    python agent.py A002 384400 --surface
    python agent.py                      (no arguments: asks you questions)
"""
import argparse
import json
from pathlib import Path

DATA = Path(__file__).parent / "data"

ACTIVITY_FACTOR = {"low": 1.4, "moderate": 1.6, "high": 1.8}


# ---------- loading ----------
def load_profiles():
    return {p["id"]: p for p in json.loads((DATA / "astronauts.json").read_text())}


def load_kb():
    return json.loads((DATA / "knowledge_base.json").read_text())


# ---------- step 1: distance -> zone ----------
def resolve_zone(distance_km: float, on_surface: bool = False) -> str:
    if distance_km < 0:
        raise ValueError("distance must be >= 0")
    if distance_km < 100:
        return "earth"
    if distance_km < 2000:
        return "leo"
    if distance_km < 450_000:
        return "lunar_surface" if on_surface else "cislunar"
    return "mars_surface" if on_surface else "deep_space"


# ---------- step 2: health metrics ----------
def bmi(p):
    return p["weight_kg"] / (p["height_cm"] / 100) ** 2


def daily_energy_kcal(p):
    """Mifflin-St Jeor BMR x activity factor. Demo estimate only."""
    s = 5 if p["sex"] == "male" else -161
    bmr = 10 * p["weight_kg"] + 6.25 * p["height_cm"] - 5 * p["age"] + s
    return round(bmr * ACTIVITY_FACTOR[p["fitness_level"]])


# ---------- step 3: retrieval + personalisation ----------
def personalise(kb, zone, p):
    exercises, diet = [], []
    injuries = set(p["injuries"])
    restrictions = set(p["dietary_restrictions"])
    allergies = set(p["allergies"])

    for rec in kb:
        if zone not in rec["zones"]:
            continue
        if rec["category"] == "exercise":
            if injuries & set(rec["contraindications"]):
                continue
            exercises.append(rec)
        else:
            if restrictions & set(rec.get("excludes_restrictions", [])):
                continue
            if allergies & set(rec.get("allergen_tags", [])):
                continue
            needs = rec.get("requires_restrictions")
            if needs and not (restrictions & set(needs)):
                continue
            diet.append(rec)
    return exercises, diet


# ---------- step 4: safety flags ----------
def safety_flags(p, zone):
    flags = []
    b = bmi(p)
    if b < 18.5 or b >= 30:
        flags.append(f"BMI {b:.1f} outside normal range - flight surgeon review")
    if p["injuries"]:
        flags.append(f"Injury on record ({', '.join(p['injuries'])}) - "
                     "exercise list filtered, surgeon to approve plan")
    if p["allergies"]:
        flags.append(f"Allergies ({', '.join(p['allergies'])}) - "
                     "allergen items removed from diet list")
    if p["mission_duration_days"] > 365 and zone in ("deep_space", "mars_surface"):
        flags.append("Long deep-space mission - radiation and isolation "
                     "monitoring plan required")
    return flags


# ---------- step 5 (optional): LLM explanation ----------
def explain_with_llm(plan_text: str) -> str:
    """Placeholder. Send plan_text to an LLM with the instruction:
    'Explain and format this plan. Do not add exercises, doses or advice.'"""
    return plan_text


# ---------- report ----------
def build_report(p, distance_km, zone):
    kb = load_kb()
    exercises, diet = personalise(kb, zone, p)
    lines = [
        f"=== Health plan for {p['name']} ({p['id']}) ===",
        f"Distance: {distance_km:,.0f} km -> zone: {zone}",
        f"Profile: {p['age']}y {p['sex']}, {p['height_cm']} cm, {p['weight_kg']} kg, "
        f"BMI {bmi(p):.1f}, fitness {p['fitness_level']}",
        f"Mission length: {p['mission_duration_days']} days",
        f"Estimated energy need: ~{daily_energy_kcal(p)} kcal/day (demo estimate)",
        "",
        "EXERCISE",
    ]
    lines += [f"  - {e['name']}: {e['frequency']}, {e['duration_min']} min "
              f"[{e['id']}, source: {e['source']}]" for e in exercises] or ["  (none)"]
    lines += ["", "DIET"]
    lines += [f"  - {d['name']}: {d['reason']} "
              f"[{d['id']}, source: {d['source']}]" for d in diet] or ["  (none)"]
    lines += ["", "FLAGS FOR FLIGHT SURGEON"]
    lines += [f"  ! {f}" for f in safety_flags(p, zone)] or ["  (none)"]
    lines += ["", "DEMO ONLY - not medical advice. Data entries are placeholders."]
    return explain_with_llm("\n".join(lines))


# ---------- command line ----------
def ask_interactively(profiles):
    """Used when the program is started with no arguments (e.g. PyCharm Run)."""
    print("Available astronauts:", ", ".join(profiles))
    astronaut_id = input("Astronaut ID: ").strip()
    distance_km = float(input("Distance from Earth in km: ").strip())
    surface = input("On a Moon/Mars surface? (y/n): ").strip().lower() == "y"
    return astronaut_id, distance_km, surface


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("astronaut_id", nargs="?")
    ap.add_argument("distance_km", nargs="?", type=float)
    ap.add_argument("--surface", action="store_true",
                    help="astronaut is on a planetary surface, not in transit/orbit")
    args = ap.parse_args()

    profiles = load_profiles()
    if args.astronaut_id is None or args.distance_km is None:
        astronaut_id, distance_km, surface = ask_interactively(profiles)
    else:
        astronaut_id, distance_km, surface = (
            args.astronaut_id, args.distance_km, args.surface)

    if astronaut_id not in profiles:
        raise SystemExit(f"Unknown astronaut. Choose from: {', '.join(profiles)}")
    zone = resolve_zone(distance_km, surface)
    print(build_report(profiles[astronaut_id], distance_km, zone))


if __name__ == "__main__":
    main()
