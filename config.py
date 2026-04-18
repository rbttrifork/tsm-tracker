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

    # Potions — IDs verified via Wowhead TBC
    22832: ("Super Mana Potion", "potion", "inv_potion_137"),
    22829: ("Super Healing Potion", "potion", "inv_potion_131"),
    22839: ("Destruction Potion", "potion", "inv_potion_107"),
    22838: ("Haste Potion", "potion", "inv_potion_108"),
    22837: ("Heroic Potion", "potion", "inv_potion_133"),
    22849: ("Ironshield Potion", "potion", "inv_potion_109"),
    22828: ("Insane Strength Potion", "potion", "inv_potion_71"),

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

    # Raw Gems - Rare
    23436: ("Living Ruby", "gem", "inv_jewelcrafting_livingruby_01"),
    23439: ("Noble Topaz", "gem", "inv_jewelcrafting_nobletopaz_01"),
    23440: ("Dawnstone", "gem", "inv_jewelcrafting_dawnstone_01"),
    23438: ("Star of Elune", "gem", "inv_jewelcrafting_starofelune_01"),
    23437: ("Talasite", "gem", "inv_jewelcrafting_talasite_01"),
    23441: ("Nightseye", "gem", "inv_jewelcrafting_nightseye_01"),

    # Raw Gems - Epic
    32227: ("Crimson Spinel", "gem", "inv_jewelcrafting_crimsonspinel_01"),
    32229: ("Lionseye", "gem", "inv_jewelcrafting_lionseye_01"),
    32228: ("Empyrean Sapphire", "gem", "inv_jewelcrafting_empyreansapphire_01"),
    32231: ("Pyrestone", "gem", "inv_jewelcrafting_pyrestone_01"),
    32249: ("Seaspray Emerald", "gem", "inv_jewelcrafting_seasprayemerald_01"),
    32230: ("Shadowsong Amethyst", "gem", "inv_jewelcrafting_shadowsongamethyst_01"),

    # Cut Gems - Rare Red (Living Ruby)
    24027: ("Bold Living Ruby", "gem", "inv_jewelcrafting_livingruby_03"),
    24028: ("Delicate Living Ruby", "gem", "inv_jewelcrafting_livingruby_03"),
    24029: ("Teardrop Living Ruby", "gem", "inv_jewelcrafting_livingruby_03"),
    24030: ("Runed Living Ruby", "gem", "inv_jewelcrafting_livingruby_03"),

    # Cut Gems - Rare Yellow (Dawnstone)
    24047: ("Brilliant Dawnstone", "gem", "inv_jewelcrafting_dawnstone_03"),
    24048: ("Smooth Dawnstone", "gem", "inv_jewelcrafting_dawnstone_03"),
    24051: ("Rigid Dawnstone", "gem", "inv_jewelcrafting_dawnstone_03"),

    # Cut Gems - Rare Blue (Star of Elune)
    24033: ("Solid Star of Elune", "gem", "inv_jewelcrafting_starofelune_03"),
    24035: ("Sparkling Star of Elune", "gem", "inv_jewelcrafting_starofelune_03"),

    # Cut Gems - Rare Orange (Noble Topaz)
    24058: ("Inscribed Noble Topaz", "gem", "inv_jewelcrafting_nobletopaz_03"),
    24059: ("Potent Noble Topaz", "gem", "inv_jewelcrafting_nobletopaz_03"),
    24061: ("Glinting Noble Topaz", "gem", "inv_jewelcrafting_nobletopaz_03"),

    # Cut Gems - Rare Green (Talasite)
    24066: ("Radiant Talasite", "gem", "inv_jewelcrafting_talasite_03"),
    24067: ("Jagged Talasite", "gem", "inv_jewelcrafting_talasite_03"),

    # Cut Gems - Rare Purple (Nightseye)
    24054: ("Sovereign Nightseye", "gem", "inv_jewelcrafting_nightseye_03"),
    24055: ("Shifting Nightseye", "gem", "inv_jewelcrafting_nightseye_03"),

    # Cut Gems - Epic Red (Crimson Spinel)
    32193: ("Bold Crimson Spinel", "gem", "inv_jewelcrafting_crimsonspinel_02"),
    32194: ("Delicate Crimson Spinel", "gem", "inv_jewelcrafting_crimsonspinel_02"),
    32196: ("Runed Crimson Spinel", "gem", "inv_jewelcrafting_crimsonspinel_02"),

    # Cut Gems - Epic Yellow (Lionseye)
    32204: ("Brilliant Lionseye", "gem", "inv_jewelcrafting_lionseye_02"),
    32205: ("Smooth Lionseye", "gem", "inv_jewelcrafting_lionseye_02"),
    32206: ("Rigid Lionseye", "gem", "inv_jewelcrafting_lionseye_02"),

    # Cut Gems - Epic Blue (Empyrean Sapphire)
    32200: ("Solid Empyrean Sapphire", "gem", "inv_jewelcrafting_empyreansapphire_02"),

    # Cut Gems - Epic Orange (Pyrestone)
    32217: ("Inscribed Pyrestone", "gem", "inv_jewelcrafting_pyrestone_02"),
    32220: ("Glinting Pyrestone", "gem", "inv_jewelcrafting_pyrestone_02"),

    # Cut Gems - Epic Purple (Shadowsong Amethyst)
    32211: ("Sovereign Shadowsong Amethyst", "gem", "inv_jewelcrafting_shadowsongamethyst_02"),
    32212: ("Shifting Shadowsong Amethyst", "gem", "inv_jewelcrafting_shadowsongamethyst_02"),

    # Enchanting Mats
    22449: ("Large Prismatic Shard", "enchanting", "inv_enchant_shardprismaticlarge"),
    22450: ("Void Crystal", "enchanting", "inv_enchant_voidcrystal"),
    22445: ("Arcane Dust", "enchanting", "inv_enchant_dustarcane"),
    22446: ("Greater Planar Essence", "enchanting", "inv_enchant_essencearcanelarge"),
    22447: ("Lesser Planar Essence", "enchanting", "inv_enchant_essencearcanesmall"),
    22448: ("Small Prismatic Shard", "enchanting", "inv_enchant_shardprismaticsmall"),

    # Herbs — TBC
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

    # Herbs — Classic (still used in TBC recipes)
    13463: ("Dreamfoil", "herb", "inv_misc_herb_dreamfoil"),
    13464: ("Golden Sansam", "herb", "inv_misc_herb_goldensansam"),
    13465: ("Mountain Silversage", "herb", "inv_misc_herb_mountainsilversage"),

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
    24272: ("Spellcloth", "cloth", "inv_fabric_felrag"),
    21887: ("Knothide Leather", "leather", "inv_misc_leatherscrap_10"),
    23793: ("Heavy Knothide Leather", "leather", "inv_misc_leatherscrap_11"),
    29548: ("Nether Dragonscales", "leather", "inv_misc_monsterscales_10"),
    25708: ("Thick Clefthoof Leather", "leather", "inv_misc_leatherscrap_09"),
    25707: ("Fel Hide", "leather", "inv_misc_pelt_wolf_ruin_04"),
    29539: ("Cobra Scales", "leather", "inv_misc_monsterscales_17"),
    25699: ("Crystal Infused Leather", "leather", "inv_misc_leatherscrap_08"),

    # Crafted leatherworking goods
    29534: ("Clefthide Leg Armor", "leatherworking", "inv_misc_armorkit_22"),
    29533: ("Cobrahide Leg Armor", "leatherworking", "inv_misc_armorkit_19"),
    29535: ("Nethercobra Leg Armor", "leatherworking", "inv_misc_armorkit_21"),
    29536: ("Nethercleft Leg Armor", "leatherworking", "inv_misc_armorkit_18"),
    25684: ("Fel Leather Gloves", "leatherworking", "inv_gauntlets_25"),
    25685: ("Fel Leather Leggings", "leatherworking", "inv_pants_leather_09"),
    25686: ("Fel Leather Boots", "leatherworking", "inv_boots_05"),
    29521: ("Felstalker Bracers", "leatherworking", "inv_bracer_13"),
    29520: ("Felstalker Breastplate", "leatherworking", "inv_chest_leather_08"),
    29519: ("Felstalker Belt", "leatherworking", "inv_belt_27"),

    # Crafted tailoring goods
    24266: ("Spellstrike Hood", "tailoring", "inv_helmet_86"),
    24267: ("Spellstrike Pants", "tailoring", "inv_pants_cloth_10"),
    24264: ("Whitemend Hood", "tailoring", "inv_helmet_84"),
    24262: ("Whitemend Pants", "tailoring", "inv_pants_cloth_11"),
    24274: ("Runic Spellthread", "tailoring", "inv_misc_gem_sapphire_02"),
    24276: ("Golden Spellthread", "tailoring", "inv_misc_gem_topaz_02"),
    24273: ("Mystic Spellthread", "tailoring", "inv_misc_gem_sapphire_01"),
    24277: ("Silver Spellthread", "tailoring", "inv_misc_gem_topaz_01"),

    # Scrolls
    10305: ("Scroll of Protection IV", "scroll", "inv_scroll_07"),
    10306: ("Scroll of Spirit IV", "scroll", "inv_scroll_01"),
    10307: ("Scroll of Stamina IV", "scroll", "inv_scroll_07"),
    10308: ("Scroll of Intellect IV", "scroll", "inv_scroll_01"),
    10309: ("Scroll of Agility IV", "scroll", "inv_scroll_02"),
    10310: ("Scroll of Strength IV", "scroll", "inv_scroll_02"),
    27498: ("Scroll of Agility V", "scroll", "inv_scroll_02"),
    27499: ("Scroll of Intellect V", "scroll", "inv_scroll_01"),
    27500: ("Scroll of Protection V", "scroll", "inv_scroll_07"),
    27501: ("Scroll of Spirit V", "scroll", "inv_scroll_01"),
    27502: ("Scroll of Stamina V", "scroll", "inv_scroll_07"),
    27503: ("Scroll of Strength V", "scroll", "inv_scroll_02"),

    # Misc Crafting — IDs verified via Wowhead TBC
    23571: ("Primal Might", "other", "inv_elemental_primal_nether"),
    23572: ("Primal Nether", "other", "spell_nature_lightningoverload"),
    30183: ("Nether Vortex", "other", "inv_elemental_primal_nether"),

    # Vendor-bought crafting reagents (priced via VENDOR_PRICES, not AH)
    18256: ("Imbued Vial", "other", "inv_drink_20"),
    14341: ("Rune Thread", "other", "inv_misc_thread_01"),
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
    ("leatherworking", "Leatherworking"),
    ("tailoring", "Tailoring"),
    ("scroll", "Scrolls"),
    ("other", "Other"),
]
