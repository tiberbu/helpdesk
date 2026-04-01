"""
Shared Kenya seed data module.

Provides the KENYA_DATA list and team-creation helpers used by both:
  - Migration patches (helpdesk/patches/v1_county/seed_kenya_teams.py)
  - The after_install hook (helpdesk/setup/install.py)

Safe to import at module level; no Frappe calls happen at import time.
"""

import frappe

# ---------------------------------------------------------------------------
# Kenya administrative data: 47 counties and their sub-counties
# Source: IEBC / KNBS official gazetted boundaries
# ---------------------------------------------------------------------------
KENYA_DATA = [
    ("Mombasa", ["Changamwe", "Jomvu", "Kisauni", "Likoni", "Mvita", "Nyali"]),
    ("Kwale", ["Kinango", "Lungalunga", "Matuga", "Msambweni"]),
    (
        "Kilifi",
        ["Ganze", "Kaloleni", "Kilifi North", "Kilifi South", "Magarini", "Malindi", "Rabai"],
    ),
    ("Tana River", ["Bura", "Galole", "Garsen"]),
    ("Lamu", ["Lamu East", "Lamu West"]),
    ("Taita-Taveta", ["Mwatate", "Taveta", "Voi", "Wundanyi"]),
    (
        "Garissa",
        [
            "Balambala",
            "Daadab",
            "Fafi",
            "Garissa Township",
            "Hulugho",
            "Ijara",
            "Lagdera",
        ],
    ),
    ("Wajir", ["Eldas", "Tarbaj", "Wajir East", "Wajir North", "Wajir South", "Wajir West"]),
    (
        "Mandera",
        ["Banissa", "Lafey", "Mandera East", "Mandera North", "Mandera South", "Mandera West"],
    ),
    ("Marsabit", ["Laisamis", "Moyale", "North Horr", "Saku"]),
    ("Isiolo", ["Garbatulla", "Isiolo", "Merti"]),
    (
        "Meru",
        [
            "Buuri",
            "Igembe Central",
            "Igembe North",
            "Igembe South",
            "Imenti Central",
            "Imenti North",
            "Imenti South",
            "Tigania East",
            "Tigania West",
        ],
    ),
    (
        "Tharaka-Nithi",
        ["Chuka/Igambangombe", "Maara", "Tharaka North", "Tharaka South"],
    ),
    (
        "Embu",
        ["Embu East", "Embu North", "Embu West", "Manyatta", "Mbeere North", "Mbeere South"],
    ),
    (
        "Kitui",
        [
            "Kitui Central",
            "Kitui East",
            "Kitui Rural",
            "Kitui South",
            "Kitui West",
            "Mwingi Central",
            "Mwingi North",
            "Mwingi West",
        ],
    ),
    (
        "Machakos",
        [
            "Kathiani",
            "Machakos Town",
            "Masinga",
            "Matungulu",
            "Mavoko",
            "Mwala",
            "Yatta",
        ],
    ),
    ("Makueni", ["Kaiti", "Kibwezi East", "Kibwezi West", "Kilome", "Makueni", "Mbooni"]),
    ("Nyandarua", ["Kinangop", "Kipipiri", "Ndaragwa", "Ol Kalou", "Ol Joro Orok"]),
    (
        "Nyeri",
        [
            "Kieni East",
            "Kieni West",
            "Mathira East",
            "Mathira West",
            "Mukurweini",
            "Nyeri Town",
            "Tetu",
        ],
    ),
    ("Kirinyaga", ["Gichugu", "Kirinyaga Central", "Mwea East", "Mwea West", "Ndia"]),
    (
        "Muranga",
        [
            "Gatanga",
            "Kahuro",
            "Kandara",
            "Kangema",
            "Kigumo",
            "Kiharu",
            "Mathioya",
            "Muranga South",
        ],
    ),
    (
        "Kiambu",
        [
            "Gatundu North",
            "Gatundu South",
            "Githunguri",
            "Kabete",
            "Kiambaa",
            "Kiambu",
            "Kikuyu",
            "Lari",
            "Limuru",
            "Ruiru",
            "Thika Town",
        ],
    ),
    (
        "Turkana",
        [
            "Kibish",
            "Loima",
            "Turkana Central",
            "Turkana East",
            "Turkana North",
            "Turkana South",
            "Turkana West",
        ],
    ),
    ("West Pokot", ["Central Pokot", "North Pokot", "Pokot South", "West Pokot"]),
    ("Samburu", ["Samburu East", "Samburu North", "Samburu West"]),
    (
        "Trans-Nzoia",
        ["Cherangany", "Endebess", "Kiminini", "Kwanza", "Trans-Nzoia East", "Trans-Nzoia West"],
    ),
    ("Uasin Gishu", ["Ainabkoi", "Kapseret", "Kesses", "Moiben", "Soy", "Turbo"]),
    ("Elgeyo-Marakwet", ["Keiyo North", "Keiyo South", "Marakwet East", "Marakwet West"]),
    ("Nandi", ["Aldai", "Chesumei", "Emgwen", "Mosop", "Nandi Hills", "Tindiret"]),
    (
        "Baringo",
        ["Baringo Central", "Baringo North", "Baringo South", "Eldama Ravine", "Mogotio", "Tiaty"],
    ),
    (
        "Laikipia",
        ["Laikipia Central", "Laikipia East", "Laikipia North", "Laikipia West", "Nyahururu"],
    ),
    (
        "Nakuru",
        [
            "Bahati",
            "Gilgil",
            "Kuresoi North",
            "Kuresoi South",
            "Molo",
            "Naivasha",
            "Nakuru Town East",
            "Nakuru Town West",
            "Njoro",
            "Rongai",
            "Subukia",
        ],
    ),
    (
        "Narok",
        ["Emurua Dikirr", "Kilgoris", "Narok East", "Narok North", "Narok South", "Narok West"],
    ),
    (
        "Kajiado",
        [
            "Isinya",
            "Kajiado Central",
            "Kajiado East",
            "Kajiado North",
            "Kajiado West",
            "Loitokitok",
            "Mashuuru",
        ],
    ),
    (
        "Kericho",
        ["Ainamoi", "Belgut", "Bureti", "Kipkelion East", "Kipkelion West", "Soin-Sigowet"],
    ),
    ("Bomet", ["Bomet Central", "Bomet East", "Chepalungu", "Konoin", "Sotik"]),
    (
        "Kakamega",
        [
            "Butere",
            "Ikolomani",
            "Khwisero",
            "Likuyani",
            "Lugari",
            "Lurambi",
            "Matungu",
            "Mumias East",
            "Mumias West",
            "Navakholo",
            "Shinyalu",
        ],
    ),
    ("Vihiga", ["Emuhaya", "Hamisi", "Luanda", "Sabatia", "Vihiga"]),
    (
        "Bungoma",
        [
            "Bumula",
            "Kabuchai",
            "Kanduyi",
            "Kimilili",
            "Mt Elgon",
            "Sirisia",
            "Tongaren",
            "Webuye East",
            "Webuye West",
        ],
    ),
    ("Busia", ["Budalangi", "Butula", "Funyula", "Nambale", "Teso North", "Teso South"]),
    ("Siaya", ["Alego-Usonga", "Bondo", "Gem", "Rarieda", "Ugenya", "Ugunja"]),
    (
        "Kisumu",
        [
            "Kisumu Central",
            "Kisumu East",
            "Kisumu West",
            "Muhoroni",
            "Nyakach",
            "Nyando",
            "Seme",
        ],
    ),
    (
        "Homa Bay",
        [
            "Homabay Town",
            "Kabondo Kasipul",
            "Karachuonyo",
            "Kasipul",
            "Mbita",
            "Ndhiwa",
            "Rangwe",
            "Suba North",
            "Suba South",
        ],
    ),
    (
        "Migori",
        [
            "Awendo",
            "Kuria East",
            "Kuria West",
            "Mabera",
            "Ntimaru",
            "Rongo",
            "Suna East",
            "Suna West",
            "Uriri",
        ],
    ),
    (
        "Kisii",
        [
            "Bobasi",
            "Bomachoge Borabu",
            "Bomachoge Chache",
            "Bonchari",
            "Kitutu Chache North",
            "Kitutu Chache South",
            "Kitutu Masaba",
            "Nyamache",
            "South Mugirango",
        ],
    ),
    ("Nyamira", ["Borabu", "Manga", "Masaba North", "Nyamira North", "Nyamira South"]),
    (
        "Nairobi",
        [
            "Dagoretti North",
            "Dagoretti South",
            "Embakasi Central",
            "Embakasi East",
            "Embakasi North",
            "Embakasi South",
            "Embakasi West",
            "Kamukunji",
            "Kasarani",
            "Kibra",
            "Langata",
            "Makadara",
            "Mathare",
            "Njiru",
            "Roysambu",
            "Ruaraka",
            "Starehe",
            "Westlands",
        ],
    ),
]


def _team_name(county: str, sub_county: str = None) -> str:
    """Return the canonical HD Team name for a county or sub-county."""
    if sub_county:
        return f"{sub_county} Sub-County Team"
    return f"{county} County Team"


def _create_team(
    team_name: str, support_level: str, territory: str, parent_team: str = None
) -> None:
    """Insert an HD Team document if it does not already exist."""
    if frappe.db.exists("HD Team", team_name):
        return
    doc = frappe.get_doc(
        {
            "doctype": "HD Team",
            "team_name": team_name,
            "support_level": support_level,
            "territory": territory,
            "is_group": 1 if not parent_team else 0,
            "parent_team": parent_team,
        }
    )
    doc.insert(ignore_permissions=True)


def seed_kenya_teams() -> None:
    """
    Create HD Team entries for the full Kenya administrative hierarchy.

    Creates:
      - 1 National Support Team  (L2 - National)
      - 1 Engineering Team       (L3 - Engineering)
      - 47 County teams          (L1 - County)
      - ~304 Sub-County teams    (L0 - Sub-County, parented to county team)

    Idempotent — safe to call multiple times.
    """
    # 1. Top-level support teams
    _create_team(
        team_name="National Support Team",
        support_level="L2 - National",
        territory="Kenya",
    )
    _create_team(
        team_name="Engineering Team",
        support_level="L3 - Engineering",
        territory="Kenya",
    )

    # 2. County teams (L1)
    for county, sub_counties in KENYA_DATA:
        county_team = _team_name(county)
        _create_team(
            team_name=county_team,
            support_level="L1 - County",
            territory=county,
            parent_team="National Support Team",
        )

        # 3. Sub-County teams (L0), parented to the county team
        for sc in sub_counties:
            _create_team(
                team_name=_team_name(county, sc),
                support_level="L0 - Sub-County",
                territory=sc,
                parent_team=county_team,
            )

    frappe.db.commit()  # nosemgrep
