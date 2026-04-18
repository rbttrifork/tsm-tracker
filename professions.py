"""Profession crafting profitability analysis.

Proof of concept: Alchemy.

Mastery rules (TBC):
  - Potion Master:   ~20% proc for +1 on Potion crafts.
  - Elixir Master:   ~20% proc for +1 on Elixir AND Flask crafts.
  - Transmute Master: ~20% proc for +1 on Transmute crafts.
  A proc averages out to a 1.20x output multiplier over many crafts.

Recipes are TBC Alchemy recipes verified against warcraft.wiki.gg /
wowpedia / Wowhead TBC. Imbued Vial is a vendor-bought reagent; its
cost is sourced from VENDOR_PRICES below, never from the AH.
"""

from db import get_db
from tsm_parser import copper_to_gold_float
from config import TBC_ITEMS


# Items that are always vendor-bought — bypass AH price lookup.
# Values are copper. (Imbued Vial: 40 silver at alchemy supply vendors.)
VENDOR_PRICES = {
    18256: 4000,   # Imbued Vial — 40s
}


# Mastery categories a recipe can belong to
MASTERY_CATEGORIES = ("potion", "elixir", "transmute")

# Mastery the player can select, and which recipe categories the +20% applies to.
# (Elixir Master buffs both flasks and elixirs — both sit under "elixir" here.)
MASTERY_APPLIES_TO = {
    "none": set(),
    "potion": {"potion"},
    "elixir": {"elixir"},
    "transmute": {"transmute"},
}


# Alchemy recipes. mastery_category determines which mastery grants the +20%.
# inputs = list of (item_id, quantity).
#
# Reagents verified against warcraft.wiki.gg / wowpedia / wowhead TBC (Apr 2026).
# Vial costs excluded — vendor-bought (Crystal/Imbued Vial ~5s each).
ALCHEMY_RECIPES = [
    # --- Potions (Potion Mastery) ---
    {
        "id": "super_healing_potion",
        "name": "Super Healing Potion",
        "output_id": 22829,
        "output_qty": 1,
        "mastery_category": "potion",
        "inputs": [(22791, 2), (22785, 1), (18256, 1)],  # 2 Netherbloom, 1 Felweed, 1 Imbued Vial
    },
    {
        "id": "super_mana_potion",
        "name": "Super Mana Potion",
        "output_id": 22832,
        "output_qty": 1,
        "mastery_category": "potion",
        "inputs": [(22786, 2), (22785, 1), (18256, 1)],  # 2 Dreaming Glory, 1 Felweed, 1 Imbued Vial
    },
    {
        "id": "destruction_potion",
        "name": "Destruction Potion",
        "output_id": 22839,
        "output_qty": 1,
        "mastery_category": "potion",
        "inputs": [(22792, 2), (22791, 1), (18256, 1)],  # 2 Nightmare Vine, 1 Netherbloom, 1 Imbued Vial
    },
    {
        "id": "haste_potion",
        "name": "Haste Potion",
        "output_id": 22838,
        "output_qty": 1,
        "mastery_category": "potion",
        "inputs": [(22789, 2), (22791, 1), (18256, 1)],  # 2 Terocone, 1 Netherbloom, 1 Imbued Vial
    },
    {
        "id": "heroic_potion",
        "name": "Heroic Potion",
        "output_id": 22837,  # Wowhead-correct ID (was 22849 prior to audit)
        "output_qty": 1,
        "mastery_category": "potion",
        "inputs": [(22789, 2), (22790, 1), (18256, 1)],  # 2 Terocone, 1 Ancient Lichen, 1 Imbued Vial
    },
    {
        "id": "ironshield_potion",
        "name": "Ironshield Potion",
        "output_id": 22849,  # Wowhead-correct ID (was 22828 prior to audit)
        "output_qty": 1,
        "mastery_category": "potion",
        "inputs": [(22790, 2), (22573, 3), (18256, 1)],  # 2 Ancient Lichen, 3 Mote of Earth, 1 Imbued Vial
    },

    # --- Elixirs (Elixir Mastery) ---
    {
        "id": "elixir_major_agility",
        "name": "Elixir of Major Agility",
        "output_id": 22831,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(22789, 1), (22785, 2), (18256, 1)],  # 1 Terocone, 2 Felweed, 1 Imbued Vial
    },
    {
        "id": "elixir_major_strength",
        "name": "Elixir of Major Strength",  # aka Onslaught Elixir
        "output_id": 22824,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(13465, 1), (22785, 1), (18256, 1)],  # 1 Mountain Silversage, 1 Felweed, 1 Imbued Vial
    },
    {
        "id": "elixir_major_firepower",
        "name": "Elixir of Major Firepower",
        "output_id": 22833,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(22574, 2), (22790, 1), (18256, 1)],  # 2 Mote of Fire, 1 Ancient Lichen, 1 Imbued Vial
    },
    {
        "id": "elixir_major_shadow_power",
        "name": "Elixir of Major Shadow Power",
        "output_id": 22835,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(22790, 1), (22792, 1), (18256, 1)],  # 1 Ancient Lichen, 1 Nightmare Vine, 1 Imbued Vial
    },
    {
        "id": "elixir_major_frost_power",
        "name": "Elixir of Major Frost Power",
        "output_id": 22827,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(22578, 2), (22790, 1), (18256, 1)],  # 2 Mote of Water, 1 Ancient Lichen, 1 Imbued Vial
    },
    {
        "id": "adepts_elixir",
        "name": "Adept's Elixir",
        "output_id": 28103,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(13463, 1), (22785, 1), (18256, 1)],  # 1 Dreamfoil, 1 Felweed, 1 Imbued Vial
    },
    {
        "id": "elixir_major_mageblood",
        "name": "Elixir of Major Mageblood",
        "output_id": 22840,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(22790, 1), (22791, 1), (18256, 1)],  # 1 Ancient Lichen, 1 Netherbloom, 1 Imbued Vial
    },
    {
        "id": "elixir_major_defense",
        "name": "Elixir of Major Defense",
        "output_id": 22834,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(22790, 3), (22789, 1), (18256, 1)],  # 3 Ancient Lichen, 1 Terocone, 1 Imbued Vial
    },
    {
        "id": "elixir_major_fortitude",
        "name": "Elixir of Major Fortitude",
        "output_id": 32062,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(22787, 2), (22785, 1), (18256, 1)],  # 2 Ragveil, 1 Felweed, 1 Imbued Vial
    },
    {
        "id": "elixir_draenic_wisdom",
        "name": "Elixir of Draenic Wisdom",
        "output_id": 32067,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(22785, 1), (22789, 1), (18256, 1)],  # 1 Felweed, 1 Terocone, 1 Imbued Vial
    },
    {
        "id": "elixir_ironskin",
        "name": "Elixir of Ironskin",
        "output_id": 32068,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(22790, 1), (22787, 1), (18256, 1)],  # 1 Ancient Lichen, 1 Ragveil, 1 Imbued Vial
    },

    # --- Flasks (Elixir Mastery) ---
    # All TBC flasks share the formula: 7 primary herb + 3 Mana Thistle + 1 Fel Lotus.
    {
        "id": "flask_relentless_assault",
        "name": "Flask of Relentless Assault",
        "output_id": 22861,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(22789, 7), (22793, 3), (22794, 1), (18256, 1)],  # 7 Terocone, 3 Mana Thistle, 1 Fel Lotus, 1 Imbued Vial
    },
    {
        "id": "flask_mighty_restoration",
        "name": "Flask of Mighty Restoration",
        "output_id": 22853,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(22786, 7), (22793, 3), (22794, 1), (18256, 1)],  # 7 Dreaming Glory, 3 Mana Thistle, 1 Fel Lotus, 1 Imbued Vial
    },
    {
        "id": "flask_pure_death",
        "name": "Flask of Pure Death",
        "output_id": 22866,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(22792, 7), (22793, 3), (22794, 1), (18256, 1)],  # 7 Nightmare Vine, 3 Mana Thistle, 1 Fel Lotus, 1 Imbued Vial
    },
    {
        "id": "flask_blinding_light",
        "name": "Flask of Blinding Light",
        "output_id": 22854,
        "output_qty": 1,
        "mastery_category": "elixir",
        "inputs": [(22791, 7), (22793, 3), (22794, 1), (18256, 1)],  # 7 Netherbloom, 3 Mana Thistle, 1 Fel Lotus, 1 Imbued Vial
    },
]


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


def analyze_alchemy(mastery="none"):
    """Compute per-craft economics for every Alchemy recipe.

    mastery: "none" | "potion" | "elixir" | "transmute"

    Returns a list of dicts with input cost, output value, profit and margin.
    Missing prices are reported as None so the UI can surface them.
    """
    if mastery not in MASTERY_APPLIES_TO:
        mastery = "none"
    buffed_cats = MASTERY_APPLIES_TO[mastery]

    conn = get_db()
    results = []

    try:
        for recipe in ALCHEMY_RECIPES:
            out_meta = _item_meta(recipe["output_id"])
            out_price, out_source = _latest_price(conn, recipe["output_id"])

            # Ingredient cost
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

    # Sort: known-profit recipes first (best profit at top), then unknowns.
    def sort_key(r):
        if r["profit_copper"] is None:
            return (1, 0)
        return (0, -r["profit_copper"])

    results.sort(key=sort_key)
    return results
