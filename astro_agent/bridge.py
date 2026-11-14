"""Bridge: edit the diet/exercise library and customise plans per astronaut.

Does not change agent.py. It edits the data files, and can show a plan
that includes each astronaut's custom items.

  data/knowledge_base.json  shared library (everyone sees these)
  data/custom_items.json    per-astronaut extras, hidden items and changes

Usage:
    python bridge.py                          menu
    python bridge.py plan A001 400            plan including A001's customisations
    python bridge.py plan A002 384400 --surface

Keep agent.py, add_astronaut.py and bridge.py in the same folder.
"""
import argparse
import json
import shutil
from pathlib import Path

import agent
from add_astronaut import ask_text, ask_number, ask_choice, ask_list, known_keywords

DATA = Path(__file__).parent / "data"
KB_FILE = DATA / "knowledge_base.json"
CUSTOM_FILE = DATA / "custom_items.json"

VALID_ZONES = ["earth", "leo", "cislunar", "deep_space", "lunar_surface", "mars_surface"]

# field name -> kind of input
FIELDS = {
    "exercise": {
        "name": "text", "zones": "zones", "target": "words",
        "frequency": "text", "duration_min": "int",
        "contraindications": "tags", "source": "opt",
    },
    "diet": {
        "name": "text", "zones": "zones", "reason": "text", "notes": "opt",
        "excludes_restrictions": "tags", "allergen_tags": "tags",
        "requires_restrictions": "tags", "source": "opt",
    },
}
# fields that can be changed for one astronaut only (safety fields are excluded)
OVERRIDABLE = {
    "exercise": ["name", "frequency", "duration_min"],
    "diet": ["name", "reason", "notes"],
}


# ---------- file handling ----------
def read_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def write_json(path, data):
    """Save with a .bak copy of the previous version."""
    if path.exists():
        shutil.copy(path, path.with_name(path.name + ".bak"))
    path.write_text(json.dumps(data, indent=2) + "\n")


# ---------- input helpers ----------
def ask_zones():
    while True:
        raw = input(f"Zones [{', '.join(VALID_ZONES)}]\n"
                    "  (comma separated, or 'all'): ").strip().lower()
        if raw == "all":
            return list(VALID_ZONES)
        zones = [z.strip() for z in raw.split(",") if z.strip()]
        if zones and all(z in VALID_ZONES for z in zones):
            return zones
        print(f"  Use only: {', '.join(VALID_ZONES)}")


def ask_words(label):
    raw = input(f"{label}\n  (comma separated, or 'none'): ").strip()
    if raw.lower() in ("", "none"):
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def ask_value(field, kind):
    inj, res, allg = known_keywords()
    hints = {"contraindications": inj, "excludes_restrictions": res,
             "requires_restrictions": res, "allergen_tags": allg}
    label = field.replace("_", " ").capitalize()
    if kind == "text":
        return ask_text(f"{label}: ")
    if kind == "opt":
        return input(f"{label} (optional): ").strip()
    if kind == "int":
        return ask_number(f"{label}: ", 1, 600, int)
    if kind == "zones":
        return ask_zones()
    if kind == "words":
        return ask_words(label)
    return ask_list(label, hints.get(field, []))


def collect_record(category, record_id, default_source):
    rec = {"id": record_id, "category": category}
    for field, kind in FIELDS[category].items():
        rec[field] = ask_value(field, kind)
    if not rec["source"]:
        rec["source"] = default_source
    return rec


# ---------- shared library ----------
def find(kb, rid):
    return next((r for r in kb if r["id"] == rid or r["id"] == rid.lower()), None)


def next_global_id(kb, category):
    prefix = "ex" if category == "exercise" else "diet"
    nums = [int(r["id"].split("_")[1]) for r in kb
            if r["id"].startswith(prefix + "_") and r["id"].split("_")[1].isdigit()]
    return f"{prefix}_{(max(nums) + 1 if nums else 1):03d}"


def list_items(kb):
    for category in ("exercise", "diet"):
        print(f"\n{category.upper()}")
        for r in kb:
            if r["category"] == category:
                print(f"  {r['id']:9s} {r['name']}   [{', '.join(r['zones'])}]")


def pick_item(kb):
    while True:
        rid = input("Item ID (or 'cancel'): ").strip()
        if rid.lower() == "cancel":
            return None
        rec = find(kb, rid)
        if rec:
            return rec
        print("  Unknown ID.")


def add_shared():
    kb = read_json(KB_FILE, [])
    category = ask_choice("Type", ["exercise", "diet"])
    rec = collect_record(category, next_global_id(kb, category),
                         "ADDED BY USER - add a real source")
    kb.append(rec)
    write_json(KB_FILE, kb)
    print(f"\nAdded {rec['id']}: {rec['name']} (everyone with a matching zone sees it).")


def edit_shared():
    kb = read_json(KB_FILE, [])
    list_items(kb)
    rec = pick_item(kb)
    if rec is None:
        return
    fields = FIELDS[rec["category"]]
    while True:
        print(f"\n{rec['id']} current values:")
        for f in fields:
            print(f"  {f}: {rec.get(f)}")
        f = input("Field to change (or 'done'): ").strip().lower()
        if f == "done":
            break
        if f not in fields:
            print("  That is not a field name.")
            continue
        rec[f] = ask_value(f, fields[f])
    write_json(KB_FILE, kb)
    print(f"Saved {rec['id']}.")


def delete_shared():
    kb = read_json(KB_FILE, [])
    list_items(kb)
    rec = pick_item(kb)
    if rec is None:
        return
    if ask_choice(f"Really delete {rec['id']} ({rec['name']}) for everyone",
                  ["yes", "no"]) == "yes":
        kb.remove(rec)
        write_json(KB_FILE, kb)
        print("Deleted. The previous file is kept as knowledge_base.json.bak")
    else:
        print("Not deleted.")


# ---------- per-astronaut customisation ----------
def get_entry(custom, user_id):
    entry = custom.setdefault(user_id, {})
    entry.setdefault("add", [])
    entry.setdefault("hide", [])
    entry.setdefault("override", {})
    return entry


def describe(entry):
    lines = [f"  + added   {r['id']}  {r['name']} ({r['category']})"
             for r in entry.get("add", [])]
    lines += [f"  - hidden  {i}" for i in entry.get("hide", [])]
    lines += [f"  ~ changed {i}: " + ", ".join(f"{k}={v}" for k, v in ov.items())
              for i, ov in entry.get("override", {}).items()]
    return lines or ["  (no customisations)"]


def add_custom(user_id, entry):
    category = ask_choice("Type", ["exercise", "diet"])
    short = "ex" if category == "exercise" else "diet"
    taken = {r["id"] for r in entry["add"]}
    n = 1
    while f"{user_id}-{short}-{n:02d}" in taken:
        n += 1
    rec = collect_record(category, f"{user_id}-{short}-{n:02d}",
                         f"CUSTOM - set for {user_id}")
    entry["add"].append(rec)
    print(f"Added {rec['id']} for {user_id} only.")


def hide_shared(user_id, entry, kb):
    list_items(kb)
    rec = pick_item(kb)
    if rec is None:
        return False
    if rec["id"] in entry["hide"]:
        print("  Already hidden for this astronaut.")
        return False
    entry["hide"].append(rec["id"])
    print(f"{rec['id']} is now hidden for {user_id} only.")
    return True


def override_shared(user_id, entry, kb):
    list_items(kb)
    rec = pick_item(kb)
    if rec is None:
        return False
    allowed = OVERRIDABLE[rec["category"]]
    changed = False
    while True:
        f = input(f"Field to change for {user_id} [{', '.join(allowed)}] "
                  "(or 'done'): ").strip().lower()
        if f == "done":
            return changed
        if f not in allowed:
            print(f"  Choose from: {', '.join(allowed)}")
            continue
        value = ask_value(f, FIELDS[rec["category"]][f])
        entry["override"].setdefault(rec["id"], {})[f] = value
        changed = True


def remove_customisation(entry):
    options = ([("add", r["id"]) for r in entry["add"]]
               + [("hide", i) for i in entry["hide"]]
               + [("override", i) for i in entry["override"]])
    if not options:
        print("  Nothing to remove.")
        return False
    for n, (kind, rid) in enumerate(options, 1):
        print(f"  {n}) {kind}: {rid}")
    kind, rid = options[ask_number("Number to remove: ", 1, len(options), int) - 1]
    if kind == "add":
        entry["add"] = [r for r in entry["add"] if r["id"] != rid]
    elif kind == "hide":
        entry["hide"].remove(rid)
    else:
        del entry["override"][rid]
    print("Removed.")
    return True


def customise_menu(user_id):
    while True:
        kb = read_json(KB_FILE, [])
        custom = read_json(CUSTOM_FILE, {})
        entry = get_entry(custom, user_id)
        print(f"\n--- Customise plan for {user_id} ---")
        print("1) Add a custom exercise or diet item (this astronaut only)")
        print("2) Hide a shared item for this astronaut")
        print("3) Change a shared item for this astronaut")
        print("4) Remove one customisation")
        print("5) Show this astronaut's customisations")
        print("6) Back")
        choice = input("Choose: ").strip()
        changed = False
        if choice == "1":
            add_custom(user_id, entry)
            changed = True
        elif choice == "2":
            changed = hide_shared(user_id, entry, kb)
        elif choice == "3":
            changed = override_shared(user_id, entry, kb)
        elif choice == "4":
            changed = remove_customisation(entry)
        elif choice == "5":
            print("\n".join(describe(entry)))
        elif choice == "6":
            return
        else:
            print("Please choose 1-6.")
        if changed:
            write_json(CUSTOM_FILE, custom)


# ---------- merged plan ----------
def merged_kb(user_id):
    """Shared library with this astronaut's hides, changes and extras applied."""
    entry = read_json(CUSTOM_FILE, {}).get(user_id, {})
    hidden = set(entry.get("hide", []))
    overrides = entry.get("override", {})
    out = []
    for rec in read_json(KB_FILE, []):
        if rec["id"] in hidden:
            continue
        if rec["id"] in overrides:
            rec = {**rec, **overrides[rec["id"]],
                   "source": f"{rec['source']} | customised for {user_id}"}
        out.append(rec)
    return out + entry.get("add", [])


def show_plan(user_id, distance_km, surface):
    profiles = agent.load_profiles()
    zone = agent.resolve_zone(distance_km, surface)
    kb = merged_kb(user_id)
    original = agent.load_kb
    agent.load_kb = lambda: kb          # agent.py itself is not modified
    try:
        print()
        print(agent.build_report(profiles[user_id], distance_km, zone))
    finally:
        agent.load_kb = original
    entry = read_json(CUSTOM_FILE, {}).get(user_id, {})
    print(f"\nCustomisations applied for {user_id}:")
    print("\n".join(describe(entry)))


# ---------- menu ----------
def pick_user(profiles):
    print("Astronauts:")
    for p in profiles.values():
        print(f"  {p['id']}  {p['name']}")
    while True:
        uid = input("Astronaut ID (or 'cancel'): ").strip().upper()
        if uid == "CANCEL":
            return None
        if uid in profiles:
            return uid
        print("  Unknown ID.")


def plan_from_menu(profiles):
    uid = pick_user(profiles)
    if uid is None:
        return
    distance_km = ask_number("Distance from Earth in km: ", 0, 1e10)
    surface = False
    if distance_km >= 100:
        surface = input("On a Moon/Mars surface? (y/n): ").strip().lower() == "y"
    show_plan(uid, distance_km, surface)


def menu():
    while True:
        profiles = agent.load_profiles()
        print("\n=== Diet and Exercise Bridge ===")
        print("1) List shared items")
        print("2) Add a shared item (everyone)")
        print("3) Edit a shared item (everyone)")
        print("4) Delete a shared item (everyone)")
        print("5) Customise for one astronaut")
        print("6) Show an astronaut's plan (with customisations)")
        print("7) Quit")
        choice = input("Choose: ").strip()
        if choice == "1":
            list_items(read_json(KB_FILE, []))
        elif choice == "2":
            add_shared()
        elif choice == "3":
            edit_shared()
        elif choice == "4":
            delete_shared()
        elif choice == "5":
            uid = pick_user(profiles)
            if uid:
                customise_menu(uid)
        elif choice == "6":
            plan_from_menu(profiles)
        elif choice == "7":
            return
        else:
            print("Please choose 1-7.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs="?")
    ap.add_argument("astronaut_id", nargs="?")
    ap.add_argument("distance_km", nargs="?", type=float)
    ap.add_argument("--surface", action="store_true")
    args = ap.parse_args()
    try:
        if args.command == "plan" and args.astronaut_id and args.distance_km is not None:
            if args.astronaut_id not in agent.load_profiles():
                raise SystemExit("Unknown astronaut ID.")
            show_plan(args.astronaut_id, args.distance_km, args.surface)
        else:
            menu()
    except (KeyboardInterrupt, EOFError):
        print("\nStopped.")


if __name__ == "__main__":
    main()
