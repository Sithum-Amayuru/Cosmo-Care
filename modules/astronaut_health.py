"""Streamlit interfaces for Cosmo Care's astronaut health features.

DEMO ONLY. Do not enter real personal or medical information. This prototype
has no authentication, access controls, encryption, or durable private storage.
"""
from __future__ import annotations

import csv
import io
from datetime import date

import pandas as pd
import streamlit as st

from astro_agent import agent, bridge, exam_bridge

PROFILES_FILE = agent.DATA / "astronauts.json"
EXAMS_FILE = exam_bridge.EXAMS_FILE


def load_profiles():
    return agent.load_profiles()


def save_profiles(profiles):
    bridge.write_json(PROFILES_FILE, list(profiles.values()))


def split_tags(value):
    return [x.strip().lower().replace(" ", "_") for x in value.split(",") if x.strip()]


def profile_tab():
    profiles = load_profiles()
    st.subheader("Astronaut profiles")
    if profiles:
        rows = [{
            "ID": p["id"], "Display name": p["name"], "Age": p["age"],
            "Fitness": p["fitness_level"], "Mission days": p["mission_duration_days"],
            "Injuries": ", ".join(p.get("injuries", [])) or "None",
            "Dietary restrictions": ", ".join(p.get("dietary_restrictions", [])) or "None"
        } for p in profiles.values()]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        selected = st.selectbox("View profile", list(profiles),
                                format_func=lambda k: f"{k} — {profiles[k]['name']}")
        with st.expander("Profile details"):
            st.json(profiles[selected])
    else:
        st.info("No profiles registered yet.")

    st.divider()
    st.subheader("Register a demonstration astronaut")
    with st.form("astronaut_profile_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("Display name")
            age = st.number_input("Age (years)", min_value=18, max_value=80, value=30)
            sex = st.selectbox("Sex used by the supplied energy formula", ["female", "male"])
        with c2:
            height = st.number_input("Height (cm)", min_value=120.0, max_value=230.0, value=170.0)
            weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0)
            fitness = st.selectbox("Fitness level", ["low", "moderate", "high"])
        with c3:
            days = st.number_input("Mission duration (days)", min_value=1, max_value=1500, value=180)
            injuries = st.text_input("Injury tags (comma-separated)")
            restrictions = st.text_input("Dietary restrictions (comma-separated)")
        allergies = st.text_input("Allergy tags (comma-separated)")
        conditions = st.text_input("Medical conditions (demo only; comma-separated)")
        medications = st.text_input("Medications (demo only; comma-separated)")
        submitted = st.form_submit_button("Save profile", type="primary")
    if submitted:
        if not name.strip():
            st.error("Enter a display name.")
            return
        nums = [int(k[1:]) for k in profiles if k.startswith("A") and k[1:].isdigit()]
        uid = f"A{max(nums or [0]) + 1:03d}"
        profiles[uid] = {
            "id": uid, "name": name.strip(), "age": int(age), "sex": sex,
            "height_cm": float(height), "weight_kg": float(weight),
            "fitness_level": fitness, "injuries": split_tags(injuries),
            "dietary_restrictions": split_tags(restrictions),
            "allergies": split_tags(allergies), "medical_conditions": split_tags(conditions),
            "medications": split_tags(medications), "mission_duration_days": int(days)
        }
        save_profiles(profiles)
        st.success(f"Saved demonstration profile {uid}.")
        st.rerun()


def customisation_ui(uid):
    st.subheader("Personalise this astronaut's plan")
    st.caption("Changes apply only to this demo profile. Added entries are unverified examples.")
    kb = bridge.read_json(bridge.KB_FILE, [])
    custom = bridge.read_json(bridge.CUSTOM_FILE, {})
    entry = bridge.get_entry(custom, uid)
    label_to_item = {f"{r['id']} — {r['name']} ({r['category']})": r for r in kb}
    with st.form(f"hide_items_{uid}"):
        hidden_labels = st.multiselect(
            "Hide shared items for this astronaut", list(label_to_item),
            default=[label for label, item in label_to_item.items() if item["id"] in entry["hide"]]
        )
        save_hidden = st.form_submit_button("Save hidden-item settings")
    if save_hidden:
        entry["hide"] = [label_to_item[x]["id"] for x in hidden_labels]
        custom[uid] = entry
        bridge.write_json(bridge.CUSTOM_FILE, custom)
        st.success("Personalisation settings saved.")

    with st.form(f"add_custom_item_{uid}"):
        category = st.selectbox("Add a custom item", ["exercise", "diet"], key=f"custom_category_{uid}")
        name = st.text_input("Item name", key=f"custom_name_{uid}")
        zones = st.multiselect("Mission zones", bridge.VALID_ZONES,
                               default=bridge.VALID_ZONES, key=f"custom_zones_{uid}")
        if category == "exercise":
            target = st.text_input("Target / purpose", key=f"custom_target_{uid}")
            frequency = st.text_input("Frequency", key=f"custom_frequency_{uid}")
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=600,
                                        value=15, key=f"custom_duration_{uid}")
            contraindications = st.text_input("Contraindication tags", key=f"custom_contra_{uid}")
        else:
            reason = st.text_input("Reason", key=f"custom_reason_{uid}")
            notes = st.text_input("Notes", key=f"custom_notes_{uid}")
            excludes = st.text_input("Excluded dietary tags", key=f"custom_excludes_{uid}")
            allergens = st.text_input("Allergen tags", key=f"custom_allergens_{uid}")
            requires = st.text_input("Required dietary tags", key=f"custom_requires_{uid}")
        add = st.form_submit_button("Add to this astronaut's plan")
    if add:
        if not name.strip() or not zones:
            st.error("Enter a name and select at least one mission zone.")
        else:
            current = entry.setdefault("add", [])
            prefix = "ex" if category == "exercise" else "diet"
            item_id = f"{uid}-{prefix}-{len(current)+1:02d}"
            if category == "exercise":
                item = {
                    "id": item_id, "category": category, "name": name.strip(), "zones": zones,
                    "target": [x.strip() for x in target.split(",") if x.strip()],
                    "frequency": frequency.strip(), "duration_min": int(duration),
                    "contraindications": split_tags(contraindications),
                    "source": "UNVERIFIED USER-ADDED DEMO ITEM"
                }
            else:
                item = {
                    "id": item_id, "category": category, "name": name.strip(), "zones": zones,
                    "reason": reason.strip(), "notes": notes.strip(),
                    "excludes_restrictions": split_tags(excludes),
                    "allergen_tags": split_tags(allergens),
                    "requires_restrictions": split_tags(requires),
                    "source": "UNVERIFIED USER-ADDED DEMO ITEM"
                }
            current.append(item)
            entry["add"] = current
            custom[uid] = entry
            bridge.write_json(bridge.CUSTOM_FILE, custom)
            st.success(f"Added {item_id}.")

    saved = bridge.read_json(bridge.CUSTOM_FILE, {}).get(uid, {})
    if saved.get("add"):
        st.dataframe(pd.DataFrame(saved["add"]), use_container_width=True, hide_index=True)


def planner_tab():
    profiles = load_profiles()
    st.subheader("Mission-specific health planning")
    if not profiles:
        st.info("Register a demonstration profile first.")
        return
    uid = st.selectbox("Astronaut", list(profiles),
                       format_func=lambda k: f"{k} — {profiles[k]['name']}", key="planner_astronaut")
    c1, c2 = st.columns(2)
    with c1:
        distance = st.number_input("Distance from Earth (km)", min_value=0.0,
                                    value=400.0, step=100.0)
    with c2:
        surface = st.checkbox("On a Moon or Mars surface")
    if st.button("Generate demonstration plan", type="primary"):
        try:
            p = profiles[uid]
            zone = agent.resolve_zone(distance, surface)
            exercises, diet = agent.personalise(bridge.merged_kb(uid), zone, p)
            st.session_state["cosmo_health_plan"] = {
                "uid": uid, "zone": zone, "bmi": agent.bmi(p),
                "energy": agent.daily_energy_kcal(p), "exercises": exercises,
                "diet": diet, "flags": agent.safety_flags(p, zone)
            }
        except Exception as exc:
            st.error(f"Could not generate plan: {exc}")
    result = st.session_state.get("cosmo_health_plan")
    if result and result["uid"] == uid:
        st.markdown(f"**Mission zone:** `{result['zone']}`")
        a, b = st.columns(2)
        a.metric("Calculated BMI", f"{result['bmi']:.1f}")
        b.metric("Estimated energy", f"{result['energy']:,} kcal/day")
        st.caption("These are simple demonstration calculations, not astronaut medical assessments or prescribed targets.")
        st.subheader("Exercise library matches")
        if result["exercises"]:
            st.dataframe(pd.DataFrame(result["exercises"]), use_container_width=True, hide_index=True)
        else:
            st.info("No exercise entries matched.")
        st.subheader("Diet library matches")
        if result["diet"]:
            st.dataframe(pd.DataFrame(result["diet"]), use_container_width=True, hide_index=True)
        else:
            st.info("No diet entries matched.")
        if result["flags"]:
            for flag in result["flags"]:
                st.warning(flag)
        if any("PLACEHOLDER" in str(x.get("source", "")).upper()
               for x in result["exercises"] + result["diet"]):
            st.warning("Some library sources are placeholders. These entries are unverified examples, not evidence-based recommendations.")
        st.info("The planner filters a demonstration library; it does not produce a medically approved exercise or nutrition prescription.")
    customisation_ui(uid)


def exam_field_widget(field, key):
    kind = field["type"]
    label = field["label"] + (f" ({field['unit']})" if field.get("unit") else "")
    if kind == "choice":
        return st.selectbox(label, field["choices"], key=key)
    if kind == "int":
        lo, hi = int(field.get("valid_min", 0)), int(field.get("valid_max", 100))
        return st.number_input(label, min_value=lo, max_value=hi, value=lo, step=1, key=key)
    if kind == "number":
        lo = float(field.get("valid_min", -1000000))
        hi = float(field.get("valid_max", 1000000))
        value = float(field.get("normal_min", lo))
        return st.number_input(label, min_value=lo, max_value=hi, value=value, key=key)
    return st.text_input(label, key=key)


def examination_tab():
    profiles = load_profiles()
    exams, by_id = exam_bridge.load_defs()
    st.subheader("Record a medical examination")
    if not profiles:
        st.info("Register a demonstration profile first.")
        return
    uid = st.selectbox("Astronaut", list(profiles),
                       format_func=lambda k: f"{k} — {profiles[k]['name']}", key="exam_astronaut")
    exam = st.selectbox("Examination", exams, format_func=lambda e: e["name"], key="exam_type")
    st.caption(f"{exam['where']} | Suggested review: {exam['review']}")
    with st.form("exam_record_form"):
        exam_date = st.date_input("Examination date", value=date.today())
        values = {}
        columns = st.columns(2)
        for index, field in enumerate(exam["fields"]):
            with columns[index % 2]:
                values[field["name"]] = exam_field_widget(
                    field, f"exam_{exam['id']}_{field['name']}"
                )
        notes = st.text_area("Notes (optional)")
        save = st.form_submit_button("Save examination record", type="primary")
    if save:
        record = {"exam": exam["id"], "date": exam_date.isoformat(),
                  "values": values, "notes": notes.strip()}
        data = bridge.read_json(EXAMS_FILE, {})
        data.setdefault(uid, []).append(record)
        bridge.write_json(EXAMS_FILE, data)
        st.success("Demonstration examination record saved.")
        found = exam_bridge.findings_for_record(exam, record)
        if found:
            st.warning("The configured demonstration rules flagged values for professional review.")
            st.dataframe(pd.DataFrame(found), use_container_width=True, hide_index=True)
        else:
            st.info("No flags were produced by the demo rules. This is not a medical clearance.")


def history_tab():
    profiles = load_profiles()
    exams, by_id = exam_bridge.load_defs()
    st.subheader("Examination history")
    if not profiles:
        st.info("No profiles available.")
        return
    uid = st.selectbox("Astronaut", list(profiles),
                       format_func=lambda k: f"{k} — {profiles[k]['name']}", key="history_astronaut")
    records = bridge.read_json(EXAMS_FILE, {}).get(uid, [])
    if not records:
        st.info("No examination records for this profile.")
        return
    rows, findings = [], []
    for record in sorted(records, key=lambda r: r["date"]):
        exam = by_id.get(record["exam"])
        if not exam:
            continue
        rows.append({
            "Date": record["date"], "Examination": exam["name"],
            "Values": "; ".join(f"{k}: {v}" for k, v in record["values"].items()),
            "Notes": record.get("notes", "")
        })
        findings.extend(exam_bridge.findings_for_record(exam, record))
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.subheader("Findings from supplied demo rules")
    if findings:
        st.dataframe(pd.DataFrame(findings), use_container_width=True, hide_index=True)
    else:
        st.info("No findings were flagged. This does not establish that results are normal.")
    st.caption("The exam definitions explicitly label their reference ranges as demonstration values, not validated clinical limits.")
    st.download_button("Download examination history",
                       pd.DataFrame(rows).to_csv(index=False).encode("utf-8"),
                       file_name=f"{uid}_exam_history.csv", mime="text/csv")


def import_exam_csv_tab():
    profiles = load_profiles()
    exams, by_id = exam_bridge.load_defs()
    st.subheader("Import examination results from CSV")
    st.caption("Required columns: astronaut_id, exam, date, field, value. Use demonstration data only.")
    uploaded = st.file_uploader("Choose CSV file", type=["csv"], key="exam_csv_upload")
    if uploaded is None or not st.button("Validate and import CSV"):
        return
    reader = csv.DictReader(io.StringIO(uploaded.getvalue().decode("utf-8-sig")))
    required = {"astronaut_id", "exam", "date", "field", "value"}
    headers = {h.strip() for h in (reader.fieldnames or [])}
    if not required.issubset(headers):
        st.error("Missing CSV columns: " + ", ".join(sorted(required - headers)))
        return
    grouped, errors = {}, []
    for line, raw in enumerate(reader, start=2):
        row = {k.strip(): (v or "").strip() for k, v in raw.items() if k}
        if not row.get("value"):
            continue
        uid, eid = row["astronaut_id"].upper(), row["exam"].lower()
        if uid not in profiles:
            errors.append(f"Line {line}: unknown astronaut {uid}")
            continue
        if eid not in by_id:
            errors.append(f"Line {line}: unknown examination {eid}")
            continue
        try:
            date.fromisoformat(row["date"])
        except ValueError:
            errors.append(f"Line {line}: invalid date")
            continue
        fields = exam_bridge.field_map(by_id[eid])
        if row["field"] not in fields:
            errors.append(f"Line {line}: unknown field {row['field']}")
            continue
        value, error = exam_bridge.parse_value(fields[row["field"]], row["value"])
        if error:
            errors.append(f"Line {line}: {row['field']} {error}")
            continue
        grouped.setdefault((uid, eid, row["date"]), {})[row["field"]] = value
    data = bridge.read_json(EXAMS_FILE, {})
    added = duplicates = 0
    for (uid, eid, when), values in grouped.items():
        existing = data.get(uid, [])
        if any(r["exam"] == eid and r["date"] == when and r["values"] == values for r in existing):
            duplicates += 1
            continue
        data.setdefault(uid, []).append({
            "exam": eid, "date": when, "values": values,
            "notes": "Imported demonstration CSV"
        })
        added += 1
    if added:
        bridge.write_json(EXAMS_FILE, data)
    st.success(f"Imported {added} record(s); skipped {duplicates} duplicate(s).")
    if errors:
        st.warning(f"{len(errors)} row(s) need attention.")
        st.write(errors[:20])


def render_astronaut_health():
    st.header("Astronaut profiles, health planning and medical examinations")
    st.warning(
        "DEMONSTRATION ONLY — do not enter real personal or medical information. "
        "This prototype has no authentication, access controls, encryption or validated "
        "clinical decision support. JSON data saved on the hosting server may be lost "
        "when the app restarts or redeploys."
    )
    tabs = st.tabs(["Profiles", "Health planner", "Record examination",
                    "Examination history", "Import CSV"])
    with tabs[0]:
        profile_tab()
    with tabs[1]:
        planner_tab()
    with tabs[2]:
        examination_tab()
    with tabs[3]:
        history_tab()
    with tabs[4]:
        import_exam_csv_tab()
