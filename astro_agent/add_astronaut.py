"""Add astronauts to data/astronauts.json by answering questions.

Separate from agent.py - run this first, then run agent.py with the new ID.

Usage:
    python add_astronaut.py
"""
import json
from pathlib import Path

DATA = Path(__file__).parent / "data"
PROFILE_FILE = DATA / "astronauts.json"
KB_FILE = DATA / "knowledge_base.json"


# ---------- file handling ----------
def load_profiles():
    if not PROFILE_FILE.exists():
        return []
    return json.loads(PROFILE_FILE.read_text())


def save_profiles(profiles):
    DATA.mkdir(exist_ok=True)
    PROFILE_FILE.write_text(json.dumps(profiles, indent=2) + "\n")


def known_keywords():
    """Words in the knowledge base that can actually filter a plan."""
    injuries, restrictions, allergens = set(), set(), set()
    if KB_FILE.exists():
        for r in json.loads(KB_FILE.read_text()):
            injuries |= set(r.get("contraindications", []))
            restrictions |= set(r.get("excludes_restrictions", []))
            restrictions |= set(r.get("requires_restrictions", []))
            allergens |= set(r.get("allergen_tags", []))
    return sorted(injuries), sorted(restrictions), sorted(allergens)


def next_id(profiles):
    nums = [int(p["id"][1:]) for p in profiles if p["id"][1:].isdigit()]
    return f"A{(max(nums) + 1 if nums else 1):03d}"


# ---------- input helpers ----------
def ask_text(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("  Please enter a value.")


def ask_number(prompt, low, high, cast=float):
    while True:
        try:
            value = cast(input(prompt).strip())
        except ValueError:
            print("  Please enter a number.")
            continue
        if low <= value <= high:
            return value
        print(f"  Value must be between {low} and {high}.")


def ask_choice(prompt, options):
    while True:
        value = input(f"{prompt} ({'/'.join(options)}): ").strip().lower()
        if value in options:
            return value
        print(f"  Choose one of: {', '.join(options)}")


def ask_list(prompt, known):
    """Comma-separated list. Type 'none' or press Enter for an empty list."""
    hint = f" [known: {', '.join(known)}]" if known else ""
    raw = input(f"{prompt}{hint}\n  (comma separated, or 'none'): ").strip().lower()
    if raw in ("", "none", "no", "n/a"):
        return []
    items = [x.strip().replace(" ", "_") for x in raw.split(",") if x.strip()]
    unknown = [x for x in items if known and x not in known]
    if unknown:
        print(f"  Note: {', '.join(unknown)} is not in the knowledge base yet, "
              "so it is saved but will not filter any items.")
    return items


# ---------- main flow ----------
def ask_profile(profiles):
    injuries_known, restrictions_known, allergens_known = known_keywords()
    return {
        "id": next_id(profiles),
        "name": ask_text("Name: "),
        "age": ask_number("Age (years): ", 18, 80, int),
        "sex": ask_choice("Sex", ["female", "male"]),
        "height_cm": ask_number("Height (cm): ", 120, 230),
        "weight_kg": ask_number("Weight (kg): ", 30, 200),
        "fitness_level": ask_choice("Fitness level", ["low", "moderate", "high"]),
        "injuries": ask_list("Injuries", injuries_known),
        "dietary_restrictions": ask_list("Dietary restrictions", restrictions_known),
        "allergies": ask_list("Allergies", allergens_known),
        "medical_conditions": ask_list("Medical conditions", []),
        "medications": ask_list("Medications", []),
        "mission_duration_days": ask_number("Mission duration (days): ", 1, 1500, int),
    }


def show_summary(p):
    bmi = p["weight_kg"] / (p["height_cm"] / 100) ** 2
    print("\n--- Check the details ---")
    print(f"ID: {p['id']}   Name: {p['name']}")
    print(f"{p['age']}y {p['sex']}, {p['height_cm']} cm, {p['weight_kg']} kg "
          f"(BMI {bmi:.1f}), fitness {p['fitness_level']}")
    for label, key in [("Injuries", "injuries"),
                       ("Dietary restrictions", "dietary_restrictions"),
                       ("Allergies", "allergies"),
                       ("Medical conditions", "medical_conditions"),
                       ("Medications", "medications")]:
        print(f"{label}: {', '.join(p[key]) or 'none'}")
    print(f"Mission: {p['mission_duration_days']} days")


def main():
    profiles = load_profiles()
    print(f"Existing astronauts: {', '.join(p['id'] for p in profiles) or 'none'}")
    try:
        while True:
            print("\n=== New astronaut ===")
            profile = ask_profile(profiles)
            show_summary(profile)
            if input("\nSave this profile? (y/n): ").strip().lower() == "y":
                profiles.append(profile)
                save_profiles(profiles)
                print(f"Saved as {profile['id']}. "
                      f"Run:  python agent.py {profile['id']} 400")
            else:
                print("Not saved.")
            if input("\nAdd another astronaut? (y/n): ").strip().lower() != "y":
                break
    except (KeyboardInterrupt, EOFError):
        print("\nStopped. Nothing half-entered was saved.")


if __name__ == "__main__":
    main()
