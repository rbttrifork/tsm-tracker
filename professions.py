"""Profession crafting profitability analysis.

Supports multiple professions. Each profession has a list of recipes;
some professions support a "mastery" that adds +20% average output on
matching recipe categories (currently: Alchemy only).

Vendor-bought reagents (Imbued Vial, Rune Thread) and BoP reagents with
a fixed assumed cost (Primal Nether) bypass AH lookup via VENDOR_PRICES.
"""

from db import get_db
from tsm_parser import copper_to_gold_float
from config import TBC_ITEMS


# Items that are priced from a fixed cost rather than the auction house.
# Copper.
#   - Imbued Vial: 40s vendor price (alchemy supply vendors).
#   - Rune Thread: 50s vendor price (tailoring supply vendors).
#   - Primal Nether: BoP, but treated as a 50g flat cost for craft profitability.
VENDOR_PRICES = {
    18256: 4000,      # Imbued Vial — 40s
    14341: 5000,      # Rune Thread — 50s
    23572: 500000,    # Primal Nether — 50g (BoP, assumed cost)
}


# Per-profession mastery options. Key is the mastery value selected in UI;
# value is the set of recipe categories that get the +20% proc bonus.
MASTERY_BY_PROFESSION = {
    "alchemy": {
        "none":      set(),
        "potion":    {"potion"},
        "elixir":    {"elixir"},      # elixir mastery buffs elixirs + flasks (both tagged "elixir")
        "transmute": {"transmute"},
    },
    "leatherworking": {"none": set()},
    "tailoring":      {"none": set()},
}


# ------------------------------------------------------------------
# Recipes
# ------------------------------------------------------------------

ALCHEMY_RECIPES = [
    # --- Potions (Potion Mastery) ---
    {"id": "super_healing_potion",  "name": "Super Healing Potion",  "output_id": 22829, "output_qty": 1, "mastery_category": "potion",
     "inputs": [(22791, 2), (22785, 1), (18256, 1)]},                                       # 2 Netherbloom, 1 Felweed, 1 Imbued Vial
    {"id": "super_mana_potion",     "name": "Super Mana Potion",     "output_id": 22832, "output_qty": 1, "mastery_category": "potion",
     "inputs": [(22786, 2), (22785, 1), (18256, 1)]},                                       # 2 Dreaming Glory, 1 Felweed, 1 Imbued Vial
    {"id": "destruction_potion",    "name": "Destruction Potion",    "output_id": 22839, "output_qty": 1, "mastery_category": "potion",
     "inputs": [(22792, 2), (22791, 1), (18256, 1)]},                                       # 2 Nightmare Vine, 1 Netherbloom, 1 Imbued Vial
    {"id": "haste_potion",          "name": "Haste Potion",          "output_id": 22838, "output_qty": 1, "mastery_category": "potion",
     "inputs": [(22789, 2), (22791, 1), (18256, 1)]},                                       # 2 Terocone, 1 Netherbloom, 1 Imbued Vial
    {"id": "heroic_potion",         "name": "Heroic Potion",         "output_id": 22837, "output_qty": 1, "mastery_category": "potion",
     "inputs": [(22789, 2), (22790, 1), (18256, 1)]},                                       # 2 Terocone, 1 Ancient Lichen, 1 Imbued Vial
    {"id": "ironshield_potion",     "name": "Ironshield Potion",     "output_id": 22849, "output_qty": 1, "mastery_category": "potion",
     "inputs": [(22790, 2), (22573, 3), (18256, 1)]},                                       # 2 Ancient Lichen, 3 Mote of Earth, 1 Imbued Vial

    # --- Elixirs (Elixir Mastery) ---
    {"id": "elixir_major_agility",      "name": "Elixir of Major Agility",      "output_id": 22831, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(22789, 1), (22785, 2), (18256, 1)]},
    {"id": "elixir_major_strength",     "name": "Elixir of Major Strength",     "output_id": 22824, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(13465, 1), (22785, 1), (18256, 1)]},
    {"id": "elixir_major_firepower",    "name": "Elixir of Major Firepower",    "output_id": 22833, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(22574, 2), (22790, 1), (18256, 1)]},
    {"id": "elixir_major_shadow_power", "name": "Elixir of Major Shadow Power", "output_id": 22835, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(22790, 1), (22792, 1), (18256, 1)]},
    {"id": "elixir_major_frost_power",  "name": "Elixir of Major Frost Power",  "output_id": 22827, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(22578, 2), (22790, 1), (18256, 1)]},
    {"id": "adepts_elixir",             "name": "Adept's Elixir",               "output_id": 28103, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(13463, 1), (22785, 1), (18256, 1)]},
    {"id": "elixir_major_mageblood",    "name": "Elixir of Major Mageblood",    "output_id": 22840, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(22790, 1), (22791, 1), (18256, 1)]},
    {"id": "elixir_major_defense",      "name": "Elixir of Major Defense",      "output_id": 22834, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(22790, 3), (22789, 1), (18256, 1)]},
    {"id": "elixir_major_fortitude",    "name": "Elixir of Major Fortitude",    "output_id": 32062, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(22787, 2), (22785, 1), (18256, 1)]},
    {"id": "elixir_draenic_wisdom",     "name": "Elixir of Draenic Wisdom",     "output_id": 32067, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(22785, 1), (22789, 1), (18256, 1)]},
    {"id": "elixir_ironskin",           "name": "Elixir of Ironskin",           "output_id": 32068, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(22790, 1), (22787, 1), (18256, 1)]},

    # --- Flasks (Elixir Mastery) — all share: 7 primary herb + 3 Mana Thistle + 1 Fel Lotus + 1 Imbued Vial ---
    {"id": "flask_relentless_assault",  "name": "Flask of Relentless Assault",  "output_id": 22861, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(22789, 7), (22793, 3), (22794, 1), (18256, 1)]},
    {"id": "flask_mighty_restoration",  "name": "Flask of Mighty Restoration",  "output_id": 22853, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(22786, 7), (22793, 3), (22794, 1), (18256, 1)]},
    {"id": "flask_pure_death",          "name": "Flask of Pure Death",          "output_id": 22866, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(22792, 7), (22793, 3), (22794, 1), (18256, 1)]},
    {"id": "flask_blinding_light",      "name": "Flask of Blinding Light",      "output_id": 22854, "output_qty": 1, "mastery_category": "elixir",
     "inputs": [(22791, 7), (22793, 3), (22794, 1), (18256, 1)]},
]


LEATHERWORKING_RECIPES = [
    # --- Leg Armors ---
    {"id": "cobrahide_leg_armor",   "name": "Cobrahide Leg Armor",   "output_id": 29533, "output_qty": 1, "mastery_category": "leg_armor",
     "inputs": [(23793, 4), (29539, 2), (22451, 4)]},                                       # 4 Heavy Knothide, 2 Cobra Scales, 4 Primal Air
    {"id": "clefthide_leg_armor",   "name": "Clefthide Leg Armor",   "output_id": 29534, "output_qty": 1, "mastery_category": "leg_armor",
     "inputs": [(25708, 8), (23793, 4), (22452, 4)]},                                       # 8 Thick Clefthoof, 4 Heavy Knothide, 4 Primal Earth
    {"id": "nethercobra_leg_armor", "name": "Nethercobra Leg Armor", "output_id": 29535, "output_qty": 1, "mastery_category": "leg_armor",
     "inputs": [(22451, 8), (23793, 4), (29539, 4), (23572, 1)]},                           # 8 Primal Air, 4 Heavy Knothide, 4 Cobra Scales, 1 Primal Nether
    {"id": "nethercleft_leg_armor", "name": "Nethercleft Leg Armor", "output_id": 29536, "output_qty": 1, "mastery_category": "leg_armor",
     "inputs": [(25708, 16), (22452, 8), (23793, 4), (23572, 1)]},                          # 16 Thick Clefthoof, 8 Primal Earth, 4 Heavy Knothide, 1 Primal Nether

    # --- Fel Leather Set (Leather, Shadow-themed) ---
    {"id": "fel_leather_gloves",    "name": "Fel Leather Gloves",    "output_id": 25684, "output_qty": 1, "mastery_category": "fel_leather",
     "inputs": [(23793, 6), (25707, 6), (22456, 6), (14341, 3)]},                           # 6 Heavy Knothide, 6 Fel Hide, 6 Primal Shadow, 3 Rune Thread
    {"id": "fel_leather_boots",     "name": "Fel Leather Boots",     "output_id": 25686, "output_qty": 1, "mastery_category": "fel_leather",
     "inputs": [(23793, 10), (25707, 8), (22456, 8), (14341, 3)]},                          # 10 Heavy Knothide, 8 Fel Hide, 8 Primal Shadow, 3 Rune Thread
    {"id": "fel_leather_leggings",  "name": "Fel Leather Leggings",  "output_id": 25685, "output_qty": 1, "mastery_category": "fel_leather",
     "inputs": [(23793, 10), (25707, 10), (22456, 10), (14341, 3)]},                        # 10 Heavy Knothide, 10 Fel Hide, 10 Primal Shadow, 3 Rune Thread

    # --- Felstalker Set (Mail) ---
    {"id": "felstalker_bracers",    "name": "Felstalker Bracers",    "output_id": 29521, "output_qty": 1, "mastery_category": "felstalker",
     "inputs": [(23793, 6), (25707, 6), (25699, 6), (22451, 4), (14341, 2)]},               # 6 Heavy Knothide, 6 Fel Hide, 6 Crystal-Infused, 4 Primal Air, 2 Rune Thread
    {"id": "felstalker_breastplate","name": "Felstalker Breastplate","output_id": 29520, "output_qty": 1, "mastery_category": "felstalker",
     "inputs": [(23793, 10), (25699, 8), (22451, 8), (25707, 4), (14341, 2)]},              # 10 Heavy Knothide, 8 Crystal-Infused, 8 Primal Air, 4 Fel Hide, 2 Rune Thread
    {"id": "felstalker_belt",       "name": "Felstalker Belt",       "output_id": 29519, "output_qty": 1, "mastery_category": "felstalker",
     "inputs": [(25699, 8), (23793, 6), (22451, 6), (25707, 4), (14341, 2)]},               # 8 Crystal-Infused, 6 Heavy Knothide, 6 Primal Air, 4 Fel Hide, 2 Rune Thread
]


TAILORING_RECIPES = [
    # --- Spellthreads (rare tier — no Primal Nether) ---
    {"id": "silver_spellthread",    "name": "Silver Spellthread",    "output_id": 24277, "output_qty": 1, "mastery_category": "spellthread",
     "inputs": [(14341, 1), (21886, 5)]},                                                   # 1 Rune Thread, 5 Primal Life
    {"id": "mystic_spellthread",    "name": "Mystic Spellthread",    "output_id": 24273, "output_qty": 1, "mastery_category": "spellthread",
     "inputs": [(14341, 1), (22457, 5)]},                                                   # 1 Rune Thread, 5 Primal Mana

    # --- Spellthreads (epic tier) ---
    {"id": "golden_spellthread",    "name": "Golden Spellthread",    "output_id": 24276, "output_qty": 1, "mastery_category": "spellthread",
     "inputs": [(21886, 10), (23572, 1), (14341, 1)]},                                      # 10 Primal Life, 1 Primal Nether, 1 Rune Thread
    {"id": "runic_spellthread",     "name": "Runic Spellthread",     "output_id": 24274, "output_qty": 1, "mastery_category": "spellthread",
     "inputs": [(22457, 10), (23572, 1), (14341, 1)]},                                      # 10 Primal Mana, 1 Primal Nether, 1 Rune Thread

    # --- Spellstrike set (Cloth, Spellfire spec material input) ---
    {"id": "spellstrike_hood",      "name": "Spellstrike Hood",      "output_id": 24266, "output_qty": 1, "mastery_category": "spellstrike",
     "inputs": [(24271, 10), (23571, 5), (23572, 1)]},                                      # 10 Spellcloth (id 24271), 5 Primal Might, 1 Primal Nether
    {"id": "spellstrike_pants",     "name": "Spellstrike Pants",     "output_id": 24267, "output_qty": 1, "mastery_category": "spellstrike",
     "inputs": [(24271, 10), (23571, 5), (23572, 1)]},                                      # 10 Spellcloth (id 24271), 5 Primal Might, 1 Primal Nether

    # --- Whitemend set (Cloth, Mooncloth material input) ---
    {"id": "whitemend_hood",        "name": "Whitemend Hood",        "output_id": 24264, "output_qty": 1, "mastery_category": "whitemend",
     "inputs": [(21845, 10), (23571, 5), (23572, 1)]},                                      # 10 Primal Mooncloth, 5 Primal Might, 1 Primal Nether
    {"id": "whitemend_pants",       "name": "Whitemend Pants",       "output_id": 24262, "output_qty": 1, "mastery_category": "whitemend",
     "inputs": [(21845, 10), (23571, 5), (23572, 1)]},                                      # 10 Primal Mooncloth, 5 Primal Might, 1 Primal Nether
]


PROFESSION_RECIPES = {
    "alchemy":         ALCHEMY_RECIPES,
    "leatherworking":  LEATHERWORKING_RECIPES,
    "tailoring":       TAILORING_RECIPES,
}


# ------------------------------------------------------------------
# Pricing helpers
# ------------------------------------------------------------------

def _latest_price(conn, item_id):
    """Return (copper_price, source). Vendor-priced items bypass the AH lookup."""
    if item_id in VENDOR_PRICES:
        return VENDOR_PRICES[item_id], "vendor"
    row = conn.execute(
        """SELECT market_value, min_buyout
           FROM price_snapshots
           WHERE item_id = ?
           ORDER BY snapshot_time DESC LIMIT 1""",
        (item_id,),
    ).fetchone()
    if not row:
        return None, None
    if row["market_value"] and row["market_value"] > 0:
        return row["market_value"], "market"
    if row["min_buyout"] and row["min_buyout"] > 0:
        return row["min_buyout"], "buyout"
    return None, None


def _item_meta(item_id):
    data = TBC_ITEMS.get(item_id)
    if not data:
        return {"name": f"Item {item_id}", "icon": None}
    icon = data[2] if len(data) > 2 else None
    return {"name": data[0], "icon": icon}


# ------------------------------------------------------------------
# Analysis
# ------------------------------------------------------------------

def analyze_profession(profession, mastery="none"):
    """Compute per-craft economics for every recipe in the given profession.

    profession: key of PROFESSION_RECIPES.
    mastery:    option from MASTERY_BY_PROFESSION[profession] (defaults to 'none').

    Returns a list of dicts. Missing prices surface as None so the UI can flag them.
    """
    recipes = PROFESSION_RECIPES.get(profession)
    if recipes is None:
        return []

    mastery_table = MASTERY_BY_PROFESSION.get(profession, {"none": set()})
    if mastery not in mastery_table:
        mastery = "none"
    buffed_cats = mastery_table[mastery]

    conn = get_db()
    results = []

    try:
        for recipe in recipes:
            out_meta = _item_meta(recipe["output_id"])
            out_price, out_source = _latest_price(conn, recipe["output_id"])

            total_input_cost = 0
            any_missing = False
            inputs_detail = []
            for item_id, qty in recipe["inputs"]:
                meta = _item_meta(item_id)
                price, source = _latest_price(conn, item_id)
                if price is None:
                    any_missing = True
                    line_cost = None
                else:
                    line_cost = price * qty
                    total_input_cost += line_cost
                inputs_detail.append({
                    "item_id": item_id,
                    "name": meta["name"],
                    "icon": meta["icon"],
                    "qty": qty,
                    "unit_price_copper": price,
                    "unit_price_gold": copper_to_gold_float(price) if price else None,
                    "line_cost_copper": line_cost,
                    "line_cost_gold": copper_to_gold_float(line_cost) if line_cost else None,
                    "price_source": source,
                })

            mastery_applies = recipe["mastery_category"] in buffed_cats
            multiplier = 1.20 if mastery_applies else 1.0
            effective_output = recipe["output_qty"] * multiplier

            if out_price and not any_missing:
                revenue = out_price * effective_output
                profit = revenue - total_input_cost
                margin_pct = (profit / total_input_cost) if total_input_cost > 0 else None
            else:
                revenue = None
                profit = None
                margin_pct = None

            results.append({
                "recipe_id": recipe["id"],
                "name": recipe["name"],
                "mastery_category": recipe["mastery_category"],
                "mastery_applies": mastery_applies,
                "base_output_qty": recipe["output_qty"],
                "effective_output_qty": effective_output,
                "output_item_id": recipe["output_id"],
                "output_name": out_meta["name"],
                "output_icon": out_meta["icon"],
                "output_unit_price_copper": out_price,
                "output_unit_price_gold": copper_to_gold_float(out_price) if out_price else None,
                "output_price_source": out_source,
                "inputs": inputs_detail,
                "input_cost_copper": total_input_cost if not any_missing else None,
                "input_cost_gold": copper_to_gold_float(total_input_cost) if not any_missing else None,
                "revenue_copper": int(revenue) if revenue is not None else None,
                "revenue_gold": copper_to_gold_float(revenue) if revenue is not None else None,
                "profit_copper": int(profit) if profit is not None else None,
                "profit_gold": copper_to_gold_float(profit) if profit is not None else None,
                "margin_pct": margin_pct,
                "has_missing_prices": any_missing or out_price is None,
            })
    finally:
        conn.close()

    def sort_key(r):
        if r["profit_copper"] is None:
            return (1, 0)
        return (0, -r["profit_copper"])

    results.sort(key=sort_key)
    return results


# Backward-compat alias for the original endpoint
def analyze_alchemy(mastery="none"):
    return analyze_profession("alchemy", mastery)
