"""Bridge for medical examination results.

Records exam results per astronaut, flags values outside the reference
ranges, and shows the flags next to the exercise/diet plan.

  data/exam_definitions.json   exam types, fields, units and reference ranges
  data/medical_exams.json      saved results (created on first save)

Does not change agent.py or bridge.py. All exam types are treated as
available, including the ones that are normally done on the ground.

Usage:
    python exam_bridge.py                        menu
    python exam_bridge.py import results.csv     import a CSV file
    python exam_bridge.py findings A001          out-of-range results for A001
    python exam_bridge.py plan A001 400          plan + exam findings
    python exam_bridge.py plan A002 384400 --surface

CSV columns: astronaut_id,exam,date,field,value   (date as YYYY-MM-DD)

Keep agent.py, add_astronaut.py, bridge.py and exam_bridge.py in one folder.
"""
import argparse
import csv
import json
from datetime import date, datetime
from pathlib import Path

import agent
import bridge
from add_astronaut import ask_number

HERE = Path(__file__).parent
DATA = HERE / "data"
DEFS_FILE = DATA / "exam_definitions.json"
EXAMS_FILE = DATA / "medical_exams.json"
TEMPLATE_FILE = HERE / "exam_import_template.csv"


# ---------- definitions ----------
def load_defs():
    if not DEFS_FILE.exists():
        raise SystemExit(
            "Missing file: exam_definitions.json\n"
            f"Copy it into this folder:  {DATA}\n"
            "(it must sit next to knowledge_base.json and astronauts.json)")
    exams = json.loads(DEFS_FILE.read_text(encoding="utf-8"))["exams"]
    if not exams:
        raise SystemExit(f"{DEFS_FILE} contains no exams.")
    return exams, {e["id"]: e for e in exams}


def field_map(exam):
    return {f["name"]: f for f in exam["fields"]}


def list_exams(exams):
    print("\nExam types:")
    for n, e in enumerate(exams, 1):
        print(f"  {n:2d}) {e['name']}\n      [{e['where']}]")


def pick_exam(exams):
    list_exams(exams)
    return exams[ask_number("Exam number: ", 1, len(exams), int) - 1]


# ---------- values ----------
def parse_value(field, raw):
    """Return (value, error_text)."""
    raw = str(raw).strip()
    kind = field["type"]
    if kind in ("number", "int"):
        try:
            value = float(raw)
        except ValueError:
            return None, "not a number"
        if kind == "int" and not value.is_integer():
            return None, "must be a whole number"
        if value.is_integer():
            value = int(value)          # show 150 instead of 150.0
        lo, hi = field.get("valid_min"), field.get("valid_max")
        if (lo is not None and value < lo) or (hi is not None and value > hi):
            return None, f"outside the possible range {lo} to {hi}"
        return value, None
    if kind == "choice":
        value = raw.lower()
        if value not in field["choices"]:
            return None, f"must be one of: {', '.join(field['choices'])}"
        return value, None
    return raw, None


def ask_field(field):
    unit = f" {field['unit']}" if field.get("unit") else ""
    hint = f" ({'/'.join(field['choices'])})" if field["type"] == "choice" else ""
    while True:
        raw = input(f"{field['label']}{unit}{hint} [Enter to skip]: ").strip()
        if not raw:
            return None
        value, err = parse_value(field, raw)
        if err:
            print(f"  {err}")
            continue
        return value


def ask_date():
    while True:
        raw = input("Date [YYYY-MM-DD, Enter for today]: ").strip()
        if not raw:
            return date.today().isoformat()
        if valid_date(raw):
            return raw
        print("  Use the format YYYY-MM-DD, for example 2026-11-14.")


def valid_date(text):
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# ---------- checking against reference ranges ----------
def check_field(field, value):
    """Return (flag or None, expected text)."""
    kind = field["type"]
    if kind in ("number", "int"):
        lo, hi = field.get("normal_min"), field.get("normal_max")
        unit = f" {field['unit']}" if field.get("unit") else ""
        if lo is not None and hi is not None:
            expected = f"{lo} to {hi}{unit}"
        elif lo is not None:
            expected = f"at least {lo}{unit}"
        elif hi is not None:
            expected = f"at most {hi}{unit}"
        else:
            return None, ""
        if lo is not None and value < lo:
            return "LOW", expected
        if hi is not None and value > hi:
            return "HIGH", expected
        return None, expected
    if kind == "choice":
        bad = field.get("abnormal", [])
        if value in bad:
            return "ABNORMAL", "not " + "/".join(bad)
        return None, ""
    normal = field.get("normal_values")
    if normal is not None and value.lower() not in normal:
        return "ABNORMAL", f"expected: {', '.join(normal)}"
    return None, ""


def findings_for_record(exam, rec):
    out = []
    fields = field_map(exam)
    for name, value in rec["values"].items():
        if name not in fields:
            continue
        flag, expected = check_field(fields[name], value)
        if flag:
            unit = f" {fields[name]['unit']}" if fields[name].get("unit") else ""
            out.append({"exam": exam["name"], "label": fields[name]["label"],
                        "value": f"{value}{unit}", "flag": flag,
                        "expected": expected, "date": rec["date"],
                        "review": exam["review"]})
    return out


def latest_by_exam(records):
    latest = {}
    for r in records:
        cur = latest.get(r["exam"])
        if cur is None or r["date"] >= cur["date"]:
            latest[r["exam"]] = r
    return latest


# ---------- saving ----------
def save_record(uid, rec):
    data = bridge.read_json(EXAMS_FILE, {})
    data.setdefault(uid, []).append(rec)
    bridge.write_json(EXAMS_FILE, data)


def record_exam(profiles):
    exams, _ = load_defs()
    uid = bridge.pick_user(profiles)
    if uid is None:
        return
    exam = pick_exam(exams)
    print(f"\n--- {exam['name']} for {uid} ---")
    when = ask_date()
    values = {}
    for field in exam["fields"]:
        value = ask_field(field)
        if value is not None:
            values[field["name"]] = value
    if not values:
        print("No values entered - nothing saved.")
        return
    notes = input("Notes (optional): ").strip()
    rec = {"exam": exam["id"], "date": when, "values": values, "notes": notes}
    save_record(uid, rec)
    print(f"\nSaved {exam['name']} for {uid} on {when}.")
    found = findings_for_record(exam, rec)
    if found:
        print("Out-of-range in this result:")
        print_finding_lines(found)
    else:
        print("All entered values are within the reference ranges.")


# ---------- CSV import and template ----------
def import_csv(path):
    exams, by_id = load_defs()
    profiles = agent.load_profiles()
    data = bridge.read_json(EXAMS_FILE, {})
    groups, errors, blank = {}, [], 0
    needed = {"astronaut_id", "exam", "date", "field", "value"}
    try:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            headers = {h.strip() for h in (reader.fieldnames or [])}
            if not needed <= headers:
                print(f"The CSV needs these columns: {', '.join(sorted(needed))}")
                return
            for n, row in enumerate(reader, start=2):
                row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
                if not row["value"]:
                    blank += 1
                    continue
                uid, eid = row["astronaut_id"].upper(), row["exam"].lower()
                if uid not in profiles:
                    errors.append(f"line {n}: unknown astronaut {uid}")
                elif eid not in by_id:
                    errors.append(f"line {n}: unknown exam '{eid}'")
                elif not valid_date(row["date"]):
                    errors.append(f"line {n}: bad date '{row['date']}'")
                elif row["field"] not in field_map(by_id[eid]):
                    errors.append(f"line {n}: '{row['field']}' is not a field of {eid}")
                else:
                    value, err = parse_value(field_map(by_id[eid])[row["field"]],
                                             row["value"])
                    if err:
                        errors.append(f"line {n}: {row['field']} {err}")
                    else:
                        key = (uid, eid, row["date"])
                        groups.setdefault(key, {})[row["field"]] = value
    except OSError as exc:
        print(f"Could not open the file: {exc}")
        return

    added = duplicates = 0
    for (uid, eid, when), values in groups.items():
        existing = data.get(uid, [])
        if any(r["exam"] == eid and r["date"] == when and r["values"] == values
               for r in existing):
            duplicates += 1
            continue
        data.setdefault(uid, []).append(
            {"exam": eid, "date": when, "values": values,
             "notes": f"imported from {Path(path).name}"})
        added += 1
    if added:
        bridge.write_json(EXAMS_FILE, data)
    print(f"\nImported {added} exam result(s). "
          f"Duplicates skipped: {duplicates}. Empty rows ignored: {blank}. "
          f"Rows with problems: {len(errors)}.")
    for e in errors[:10]:
        print(f"  ! {e}")
    if len(errors) > 10:
        print(f"  ... and {len(errors) - 10} more")


def make_template(profiles):
    uid = bridge.pick_user(profiles)
    if uid is None:
        return
    exams, _ = load_defs()
    when = ask_date()
    with open(TEMPLATE_FILE, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["astronaut_id", "exam", "date", "field", "value"])
        for e in exams:
            for f in e["fields"]:
                writer.writerow([uid, e["id"], when, f["name"], ""])
    print(f"\nTemplate written to: {TEMPLATE_FILE}")
    print("Fill in the 'value' column (leave blank to skip), then import it.")


# ---------- viewing ----------
def print_finding_lines(found):
    for f in found:
        print(f"  ! {f['exam']} - {f['label']}: {f['value']} is {f['flag']} "
              f"(expected {f['expected']}) [{f['date']}] -> {f['review']}")


def print_findings(uid):
    exams, by_id = load_defs()
    latest = latest_by_exam(bridge.read_json(EXAMS_FILE, {}).get(uid, []))
    print(f"\nEXAM FINDINGS for {uid} (latest result of each exam)")
    found = []
    for e in exams:
        if e["id"] in latest:
            found += findings_for_record(e, latest[e["id"]])
    if found:
        print_finding_lines(found)
    else:
        print("  (no out-of-range results)" if latest
              else "  (no exam results on file)")
    print(f"  Exams on file: {len(latest)} of {len(exams)}")
    print("  Demo reference ranges - the flight surgeon decides what they mean.")


def show_history(uid):
    exams, by_id = load_defs()
    records = bridge.read_json(EXAMS_FILE, {}).get(uid, [])
    if not records:
        print(f"\nNo exam results on file for {uid}.")
        return
    order = {e["id"]: n for n, e in enumerate(exams)}
    print(f"\nEXAM HISTORY for {uid}")
    for r in sorted(records, key=lambda r: (r["date"], order.get(r["exam"], 99))):
        exam = by_id.get(r["exam"])
        if exam is None:
            continue
        fields = field_map(exam)
        print(f"\n  {r['date']}  {exam['name']}")
        for name, value in r["values"].items():
            f = fields.get(name)
            if f is None:
                continue
            flag, _ = check_field(f, value)
            unit = f" {f['unit']}" if f.get("unit") else ""
            mark = f"   <-- {flag}" if flag else ""
            print(f"      {f['label']}: {value}{unit}{mark}")
        if r.get("notes"):
            print(f"      Notes: {r['notes']}")


def plan_with_findings(uid, distance_km, surface):
    bridge.show_plan(uid, distance_km, surface)
    print_findings(uid)
    print("\nExam findings are shown next to the plan but do not change it "
          "automatically.\nIf the flight surgeon wants a change, make it with "
          "bridge.py (option 5).")


# ---------- menu ----------
def plan_from_menu(profiles):
    uid = bridge.pick_user(profiles)
    if uid is None:
        return
    distance_km = ask_number("Distance from Earth in km: ", 0, 1e10)
    surface = False
    if distance_km >= 100:
        surface = input("On a Moon/Mars surface? (y/n): ").strip().lower() == "y"
    plan_with_findings(uid, distance_km, surface)


def menu():
    while True:
        profiles = agent.load_profiles()
        print("\n=== Medical Exam Bridge ===")
        print("1) Record an exam result")
        print("2) Import results from a CSV file")
        print("3) Create a blank CSV template")
        print("4) View exam history for an astronaut")
        print("5) Show exam findings for an astronaut")
        print("6) Show plan with exam findings")
        print("7) List exam types")
        print("8) Quit")
        choice = input("Choose: ").strip()
        if choice == "1":
            record_exam(profiles)
        elif choice == "2":
            path = input("Path to the CSV file: ").strip().strip('"')
            import_csv(path)
        elif choice == "3":
            make_template(profiles)
        elif choice in ("4", "5"):
            uid = bridge.pick_user(profiles)
            if uid:
                (show_history if choice == "4" else print_findings)(uid)
        elif choice == "6":
            plan_from_menu(profiles)
        elif choice == "7":
            list_exams(load_defs()[0])
        elif choice == "8":
            return
        else:
            print("Please choose 1-8.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs="?")
    ap.add_argument("arg1", nargs="?")
    ap.add_argument("arg2", nargs="?")
    ap.add_argument("--surface", action="store_true")
    args = ap.parse_args()
    try:
        load_defs()                      # stop early if the definitions file is missing
        profiles = agent.load_profiles()
        if args.command == "import" and args.arg1:
            import_csv(args.arg1)
        elif args.command == "findings" and args.arg1:
            if args.arg1.upper() not in profiles:
                raise SystemExit("Unknown astronaut ID.")
            print_findings(args.arg1.upper())
        elif args.command == "plan" and args.arg1 and args.arg2:
            if args.arg1.upper() not in profiles:
                raise SystemExit("Unknown astronaut ID.")
            plan_with_findings(args.arg1.upper(), float(args.arg2), args.surface)
        else:
            menu()
    except (KeyboardInterrupt, EOFError):
        print("\nStopped.")


if __name__ == "__main__":
    main()
