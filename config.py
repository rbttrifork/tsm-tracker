"""Configuration and TBC item definitions for TSM Price Tracker."""

import os

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "tsm_tracker.db"))

APPDATA_LUA_PATH = r"D:\Games\World of Warcraft\_anniversary_\Interface\AddOns\TradeSkillMaster_AppHelper\AppData.lua"
BACKUP_DIR = r"C:\Users\Bruger\AppData\Roaming\TradeSkillMaster\TSMApplication\Backups"
BACKUP_ACCOUNT_PREFIX = "KENTHSOLEM-Anniversary_"

# --- Deployment mode ---
# Set DEPLOYMENT_MODE=cloud on the cloud host to disable local-only features
DEPLOYMENT_MODE = os.environ.get("DEPLOYMENT_MODE", "local")  # "local" or "cloud"

# --- Push API key (cloud mode) ---
# Set TSM_PUSH_API_KEY on both local (pusher.py) and cloud (app.py) to the same secret
PUSH_API_KEY = os.environ.get("TSM_PUSH_API_KEY", "")

# --- Cloud URL (for pusher.py) ---
CLOUD_URL = os.environ.get("TSM_CLOUD_URL", "")  # e.g. "https://your-app.railway.app"

# --- Realm ---
REALM = "Spineshatter-Horde"
REGION = "Fresh-EU"

# --- Raid days (0=Monday, 6=Sunday) ---
RAID_DAYS = [2, 3]  # Wednesday, Thursday

# --- Buy-low threshold ---
BUY_LOW_THRESHOLD = 0.15  # 15% below rolling average

# --- TBC Item Database ---
# Format: item_id -> (name, category, icon)
# Categories: primal, flask, elixir, potion, food, gem, enchanting, herb, ore, cloth, leather, other
TBC_ITEMS = {
    # Primals
    21884: ("Primal Fire", "primal", "inv_elemental_primal_fire"),
    21885: ("Primal Water", "primal", "inv_elemental_primal_water"),
    22451: ("Primal Air", "primal", "inv_elemental_primal_air"),
    22452: ("Primal Earth", "primal", "inv_elemental_primal_earth"),
    22456: ("Primal Shadow", "primal", "inv_elemental_primal_shadow"),
    22457: ("Primal Mana", "primal", "inv_elemental_primal_mana"),
    21886: ("Primal Life", "primal", "inv_elemental_primal_life"),

    # Motes
    22574: ("Mote of Fire", "primal", "inv_elemental_mote_fire01"),
    22578: ("Mote of Water", "primal", "inv_elemental_mote_water01"),
    22573: ("Mote of Earth", "primal", "inv_elemental_mote_earth01"),
    22572: ("Mote of Air", "primal", "inv_elemental_mote_air01"),
    22577: ("Mote of Shadow", "primal", "inv_elemental_mote_shadow01"),
    22576: ("Mote of Mana", "primal", "inv_elemental_mote_mana"),
    22575: ("Mote of Life", "primal", "inv_elemental_mote_life01"),

    # Flasks
    22861: ("Flask of Relentless Assault", "flask", "inv_potion_116"),
    22853: ("Flask of Mighty Restoration", "flask", "inv_potion_118"),
    22866: ("Flask of Pure Death", "flask", "inv_potion_115"),
    22854: ("Flask of Blinding Light", "flask", "inv_potion_117"),
    13512: ("Flask of Supreme Power", "flask", "inv_potion_41"),
    13511: ("Flask of Distilled Wisdom", "flask", "inv_potion_97"),
    13510: ("Flask of the Titans", "flask", "inv_potion_62"),

    # Elixirs - Battle
    22831: ("Elixir of Major Agility", "elixir", "inv_potion_127"),
    22835: ("Elixir of Major Shadow Power", "elixir", "inv_potion_145"),
    22824: ("Elixir of Major Strength", "elixir", "inv_potion_147"),
    22833: ("Elixir of Major Firepower", "elixir", "inv_potion_146"),
    22827: ("Elixir of Major Frost Power", "elixir", "inv_potion_148"),
    28103: ("Adept's Elixir", "elixir", "inv_potion_96"),

    # Elixirs - Guardian
    22834: ("Elixir of Major Defense", "elixir", "inv_potion_122"),
    32062: ("Elixir of Major Fortitude", "elixir", "inv_potion_158"),
    32067: ("Elixir of Draenic Wisdom", "elixir", "inv_potion_155"),
    32068: ("Elixir of Ironskin", "elixir", "inv_potion_159"),
    22840: ("Elixir of Major Mageblood", "elixir", "inv_potion_151"),
    22830: ("Elixir of the Searching Eye", "elixir", "inv_potion_135"),

    # Potions
    22832: ("Super Mana Potion", "potion", "inv_potion_137"),
    22829: ("Super Healing Potion", "potion", "inv_potion_131"),
    22839: ("Destruction Potion", "potion", "inv_potion_107"),
    22828: ("Ironshield Potion", "potion", "inv_potion_109"),
    22838: ("Haste Potion", "potion", "inv_potion_108"),
    22849: ("Heroic Potion", "potion", "inv_potion_133"),

    # Food Buffs
    33052: ("Fisherman's Feast", "food", "inv_misc_food_88_ravagernuggets"),
    27667: ("Spicy Crawdad", "food", "inv_misc_fish_16"),
    27657: ("Blackened Basilisk", "food", "inv_misc_food_86_basilisk"),
    27666: ("Golden Fish Sticks", "food", "inv_misc_fish_18"),
    27659: ("Grilled Mudfish", "food", "inv_misc_food_65"),
    27658: ("Roasted Clefthoof", "food", "inv_misc_food_60"),
    27655: ("Ravager Dog", "food", "inv_misc_food_53"),
    27660: ("Talbuk Steak", "food", "inv_misc_food_84_roastclefthoof"),
    27664: ("Crunchy Serpent", "food", "inv_misc_food_78"),

    # Raw Fish / Cooking Mats
    27422: ("Barbed Gill Trout", "food", "inv_misc_fish_37"),
    27425: ("Spotted Feltail", "food", "inv_misc_fish_39"),
    27429: ("Huge Spotted Feltail", "food", "inv_misc_fish_34"),
    27435: ("Figluster's Mudfish", "food", "inv_misc_fish_41"),
    27437: ("Icefin Bluefish", "food", "inv_misc_fish_23"),
    27438: ("Golden Darter", "food", "inv_misc_fish_36"),
    27439: ("Furious Crawdad", "food", "inv_misc_fish_14"),

    # Gems - Red
    24027: ("Living Ruby", "gem", "inv_jewelcrafting_livingruby_03"),
    24028: ("Crimson Spinel", "gem", "inv_jewelcrafting_livingruby_03"),  # actually T6 gem
    24030: ("Runed Living Ruby", "gem", "inv_jewelcrafting_livingruby_03"),

    # Gems - Orange
    24032: ("Noble Topaz", "gem", "inv_jewelcrafting_dawnstone_03"),

    # Gems - Yellow
    24036: ("Dawnstone", "gem", "inv_jewelcrafting_livingruby_03"),

    # Gems - Blue
    24039: ("Star of Elune", "gem", "inv_jewelcrafting_starofelune_03"),

    # Gems - Green
    24048: ("Talasite", "gem", "inv_jewelcrafting_dawnstone_03"),

    # Gems - Purple
    24054: ("Nightseye", "gem", "inv_jewelcrafting_nightseye_03"),

    # Enchanting Mats
    22449: ("Large Prismatic Shard", "enchanting", "inv_enchant_shardprismaticlarge"),
    22450: ("Void Crystal", "enchanting", "inv_enchant_voidcrystal"),
    22445: ("Arcane Dust", "enchanting", "inv_enchant_dustarcane"),
    22446: ("Greater Planar Essence", "enchanting", "inv_enchant_essencearcanelarge"),
    22447: ("Lesser Planar Essence", "enchanting", "inv_enchant_essencearcanesmall"),
    22448: ("Small Prismatic Shard", "enchanting", "inv_enchant_shardprismaticsmall"),

    # Herbs
    22785: ("Felweed", "herb", "inv_misc_herb_felweed"),
    22786: ("Dreaming Glory", "herb", "inv_misc_herb_dreamingglory"),
    22787: ("Ragveil", "herb", "inv_misc_herb_ragveil"),
    22788: ("Flame Cap", "herb", "inv_misc_herb_flamecap"),
    22789: ("Terocone", "herb", "inv_misc_herb_terrocone"),
    22790: ("Ancient Lichen", "herb", "inv_misc_herb_ancientlichen"),
    22791: ("Netherbloom", "herb", "inv_misc_herb_netherbloom"),
    22792: ("Nightmare Vine", "herb", "inv_misc_herb_nightmarevine"),
    22793: ("Mana Thistle", "herb", "inv_misc_herb_manathistle"),
    22794: ("Fel Lotus", "herb", "inv_misc_herb_fellotus"),

    # Ores & Bars
    23424: ("Fel Iron Ore", "ore", "inv_ore_feliron"),
    23425: ("Adamantite Ore", "ore", "inv_ore_adamantium"),
    23426: ("Khorium Ore", "ore", "inv_ore_khorium"),
    23445: ("Fel Iron Bar", "ore", "inv_ingot_feliron"),
    23446: ("Adamantite Bar", "ore", "inv_ingot_10"),
    23449: ("Khorium Bar", "ore", "inv_ingot_09"),
    23447: ("Eternium Bar", "ore", "inv_ingot_11"),
    23448: ("Felsteel Bar", "ore", "inv_ingot_felsteel"),
    23573: ("Hardened Adamantite Bar", "ore", "inv_ingot_adamantite"),

    # Cloth & Leather
    21877: ("Netherweave Cloth", "cloth", "inv_fabric_netherweave"),
    21842: ("Bolt of Imbued Netherweave", "cloth", "inv_fabric_netherweave_bolt_imbued"),
    21845: ("Primal Mooncloth", "cloth", "inv_fabric_moonrag_primal"),
    21844: ("Bolt of Soulcloth", "cloth", "inv_fabric_soulcloth_bolt"),
    21840: ("Bolt of Netherweave", "cloth", "inv_fabric_netherweave_bolt"),
    25707: ("Knothide Leather", "leather", "inv_misc_leatherscrap_13"),
    25708: ("Thick Knothide Leather", "leather", "inv_misc_leatherscrap_14"),
    29548: ("Nether Dragonscales", "leather", "inv_misc_monsterscales_10"),

    # Misc Crafting
    23571: ("Primal Nether", "other", "spell_nature_lightningoverload"),
    23572: ("Nether Vortex", "other", "inv_elemental_primal_nether"),
}

# All categories for UI filtering
CATEGORIES = [
    ("primal", "Primals & Motes"),
    ("flask", "Flasks"),
    ("elixir", "Elixirs"),
    ("potion", "Potions"),
    ("food", "Food & Cooking"),
    ("gem", "Gems"),
    ("enchanting", "Enchanting"),
    ("herb", "Herbs"),
    ("ore", "Ores & Bars"),
    ("cloth", "Cloth"),
    ("leather", "Leather"),
    ("other", "Other"),
]
