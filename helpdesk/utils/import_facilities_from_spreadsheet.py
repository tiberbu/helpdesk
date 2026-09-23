"""
Import TaifaCare HMIS live facilities into HD Facility.

Creates missing HD Subcounty records first, then imports HD Facility records
linked to the correct HD County and HD Subcounty records.

Run with:
    bench --site support.tiberbu.app execute \
        helpdesk.utils.import_facilities_from_spreadsheet.run
"""

import re
import frappe


RAW_DATA_PATH = "/tmp/facility_data.txt"

# Spreadsheet county name → HD County document name
COUNTY_MAP = {
    "elgeyo marakwet": "Elgeyo-Marakwet",
    "taita taveta": "Taita-Taveta",
    "tharaka nithi": "Tharaka-Nithi",
    "trans nzoia": "Trans-Nzoia",
    "homa bay": "Homa Bay",
    "tana river": "Tana River",
    "west pokot": "West Pokot",
    "uasin gishu": "Uasin Gishu",
    "murang'a": "Murang'a",
    "muranga": "Murang'a",
    "kisii": "Kisii",
    "nyamira": "Nyamira",
    "laikipia": "Laikipia",
    "isiolo": "Isiolo",
}


def _normalize_county(name: str) -> str:
    lower = name.strip().lower()
    if lower in COUNTY_MAP:
        return COUNTY_MAP[lower]
    return name.strip().title()


def _normalize_sc(name: str) -> str:
    """Strip 'Sub County' suffix and normalise whitespace/case for matching."""
    name = name.lower().strip()
    name = re.sub(r"\bsub[\s\-]county\b", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _sc_display_name(raw: str) -> str:
    """Build a clean title-cased display name from raw spreadsheet subcounty."""
    name = re.sub(r"\bsub[\s\-]county\b", "", raw, flags=re.I).strip()
    name = re.sub(r"\s+", " ", name).strip()
    # Title-case but preserve known acronyms
    return name.title()


def _parse_facilities() -> list[dict]:
    """Parse the raw spreadsheet paste into a list of facility dicts."""
    with open(RAW_DATA_PATH) as f:
        raw = f.read()
    facilities = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = re.split(r" {4,}", line)
        if len(parts) < 6 or not parts[0].isdigit():
            continue
        county = parts[1].strip()
        subcounty = parts[2].strip()
        facility_name = parts[3].strip()
        reg_no = parts[4].strip()
        go_live = parts[5].strip()
        if go_live == "Yes" and facility_name and county:
            facilities.append(
                {
                    "county": county,
                    "subcounty": subcounty,
                    "facility_name": facility_name,
                    "reg_no": reg_no or None,
                }
            )
    return facilities


def _build_sc_index() -> dict[tuple[str, str], str]:
    """Return {(county_lower, sc_name_lower_stripped): sc_doc_name}."""
    rows = frappe.db.sql(
        "SELECT name, subcounty_name, county FROM `tabHD Subcounty`",
        as_dict=True,
    )
    index = {}
    for r in rows:
        key = (r.county.lower(), r.subcounty_name.lower().strip().rstrip("."))
        index[key] = r.name
    return index


def _build_county_index() -> dict[str, str]:
    rows = frappe.db.sql("SELECT name FROM `tabHD County`", as_dict=True)
    return {r.name.lower(): r.name for r in rows}


def _resolve_sc(county_doc: str, sc_norm: str, sc_index: dict) -> str | None:
    ck = county_doc.lower()
    # Exact match
    sc = sc_index.get((ck, sc_norm))
    if sc:
        return sc
    # Trailing dot stripped
    sc = sc_index.get((ck, sc_norm.rstrip(".")))
    if sc:
        return sc
    # Substring containment
    for (ck2, sk), dn in sc_index.items():
        if ck2 == ck and (sc_norm in sk or sk in sc_norm):
            return dn
    return None


def _ensure_subcounty(county_doc: str, sc_raw: str, sc_index: dict) -> str:
    """Return an existing or newly-created HD Subcounty doc name."""
    sc_norm = _normalize_sc(sc_raw)
    existing = _resolve_sc(county_doc, sc_norm, sc_index)
    if existing:
        return existing

    display = _sc_display_name(sc_raw)
    # Document name pattern: {county}-{subcounty_name} (lowercase)
    doc_name = f"{county_doc}-{display}"

    if frappe.db.exists("HD Subcounty", doc_name):
        # Add to index so subsequent lookups hit the cache
        sc_index[(county_doc.lower(), display.lower())] = doc_name
        return doc_name

    doc = frappe.get_doc(
        {
            "doctype": "HD Subcounty",
            "subcounty_name": display,
            "county": county_doc,
        }
    )
    doc.insert(ignore_permissions=True)
    sc_index[(county_doc.lower(), display.lower())] = doc.name
    return doc.name


def _facility_type(name: str) -> str:
    lower = name.lower()
    if "dispensary" in lower:
        return "Dispensary"
    if "health centre" in lower or "health center" in lower:
        return "Health Centre"
    if "hospital" in lower:
        return "Hospital"
    if "clinic" in lower:
        return "Clinic"
    if "maternity" in lower:
        return "Maternity Home"
    if "nursing" in lower:
        return "Nursing Home"
    if "medical centre" in lower or "medical center" in lower:
        return "Medical Centre"
    return "Health Centre"


def run():
    """Import live TaifaCare facilities. Idempotent — safe to re-run."""
    facilities = _parse_facilities()
    county_index = _build_county_index()
    sc_index = _build_sc_index()

    created = 0
    already_exists = 0
    no_county = 0
    errors = 0
    new_sc_created = 0
    unmatched_counties: set[str] = set()

    # Pre-count how many subcounties exist before we start
    sc_before = frappe.db.count("HD Subcounty")

    for i, fac in enumerate(facilities):
        # --- Resolve county ---
        county_doc = _normalize_county(fac["county"])
        if county_doc.lower() not in county_index:
            unmatched_counties.add(fac["county"])
            no_county += 1
            continue
        county_doc = county_index[county_doc.lower()]

        # --- Resolve / create subcounty ---
        sc_doc_name = _ensure_subcounty(county_doc, fac["subcounty"], sc_index)

        # --- Create facility ---
        facility_name = fac["facility_name"]
        if frappe.db.exists("HD Facility", facility_name):
            already_exists += 1
            continue

        reg_no = fac["reg_no"]
        try:
            doc = frappe.get_doc(
                {
                    "doctype": "HD Facility",
                    "facility_name": facility_name,
                    "facility_code": reg_no,
                    "facility_type": _facility_type(facility_name),
                    "status": "Active",
                    "ownership": "Government",
                    "county": county_doc,
                    "subcounty": sc_doc_name,
                }
            )
            doc.insert(ignore_permissions=True)
            created += 1
        except Exception as e:
            err_str = str(e)
            # Duplicate facility_code — retry without it so facility is not lost
            if "facility_code" in err_str and "Duplicate" in err_str:
                try:
                    doc2 = frappe.get_doc(
                        {
                            "doctype": "HD Facility",
                            "facility_name": facility_name,
                            "facility_type": _facility_type(facility_name),
                            "status": "Active",
                            "ownership": "Government",
                            "county": county_doc,
                            "subcounty": sc_doc_name,
                        }
                    )
                    doc2.insert(ignore_permissions=True)
                    created += 1
                    print(f"  WARN duplicate reg_no {reg_no} skipped for: {facility_name}")
                except Exception as e2:
                    print(f"  ERROR [{facility_name}]: {e2}")
                    errors += 1
            else:
                print(f"  ERROR [{facility_name}]: {e}")
                errors += 1

        if (created + already_exists) % 500 == 0 and (created + already_exists) > 0:
            frappe.db.commit()
            print(f"  ... {created} created, {already_exists} already existed")

    frappe.db.commit()

    sc_after = frappe.db.count("HD Subcounty")
    new_sc_created = sc_after - sc_before

    print("\n" + "=" * 60)
    print("FACILITY IMPORT COMPLETE")
    print("=" * 60)
    print(f"  Facilities created:      {created}")
    print(f"  Already existed:         {already_exists}")
    print(f"  Skipped (no county):     {no_county}")
    print(f"  Errors:                  {errors}")
    print(f"  Total processed:         {len(facilities)}")
    print(f"  New subcounties created: {new_sc_created}")

    if unmatched_counties:
        print(f"\nUnmatched county names ({len(unmatched_counties)}):")
        for c in sorted(unmatched_counties):
            print(f"  '{c}'")
