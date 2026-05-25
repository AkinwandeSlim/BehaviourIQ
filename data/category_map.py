# data/category_map.py
# BehaviorIQ — Production Ecommerce Category Taxonomy v2
# -------------------------------------------------------
# BACKWARD-COMPATIBLE evolution of the original system.
# All existing IDs preserved. All original functions still work.
# New structures: CATEGORY_METADATA, DEPARTMENT_TREE, CATEGORY_SLUGS,
#                 CANONICAL_MAP, enriched DETAIL_TO_PRODUCT.

import pandas as pd
import os
from typing import Dict, List, Optional, Tuple

# ══════════════════════════════════════════════════════════════════════
#  1.  CANONICAL CATEGORY NAMES
#      Single source of truth for display names.
#      Duplicates resolved: each ID maps to ONE clean name.
#      Aliases are documented inline so future cleanup is easy.
# ══════════════════════════════════════════════════════════════════════

CATEGORY_NAMES: Dict[int, str] = {

    # ── ELECTRONICS ──────────────────────────────────────────────────
    1051: "Electronics & Gadgets",
    683:  "Mobile Phones",
    1483: "Computers & Accessories",
    686:  "Laptops & Notebooks",
    1248: "Smart Home Devices",
    196:  "Audio & Headphones",
    1173: "Cameras & Photography",
    1375: "Wearables & Smartwatches",
    1542: "Gaming & Consoles",
    936:  "Home Entertainment",
    57:   "TV & Home Theatre",
    1625: "Printers & Scanners",
    586:  "Computer Accessories",
    427:  "Networking & Connectivity",
    575:  "Computer Components",
    1037: "Networking Equipment",
    828:  "Headphones & Earbuds",
    1098: "Audio Equipment",
    1473: "Video Games",
    438:  "Gaming Accessories",
    411:  "Gaming Peripherals",          # kept distinct — UI can merge with 438
    1018: "Gaming Headsets",
    282:  "Home Security",
    1070: "Smart Lighting",
    1089: "Smart Home Accessories",
    1286: "Security Cameras",
    14:   "Laptop Accessories",
    1035: "Laptop Peripherals",
    684:  "Laptop Bags",
    1040: "Computer Peripherals",
    1043: "Printer Supplies",
    1364: "Phone Cases & Protectors",
    984:  "Smartphone Cases",            # alias → 1364 in CANONICAL_MAP
    944:  "Smartphone Accessories",
    819:  "Mobile Accessories",
    1355: "Tablet Accessories",
    558:  "Tablet Accessories",          # alias → 1355 in CANONICAL_MAP
    958:  "Camera Accessories",
    1302: "Smartwatch Accessories",
    366:  "Wearable Fitness Devices",
    1642: "Fitness Trackers",
    818:  "Audio Cables & Adapters",
    969:  "Audio Accessories",
    195:  "Audio Accessories",           # alias → 969 in CANONICAL_MAP
    1418: "Car Electronics",
    471:  "Car Electronics & Accessories",
    1111: "Musical Accessories",

    # ── FASHION & APPAREL ─────────────────────────────────────────────
    858:  "Clothing & Apparel",
    1:    "Men's Clothing",
    5:    "Men's Clothing",              # was "Men's Fashion" → canonical
    1233: "Men's Clothing",             # alias → 1 in CANONICAL_MAP
    1192: "Women's Clothing",           # was "Women's Fashion" → canonical
    1277: "Women's Clothing",           # alias → 1192 in CANONICAL_MAP
    406:  "Kids Clothing",
    390:  "Baby Clothing",
    228:  "Fashion Accessories",
    437:  "Winter Accessories",
    1573: "Active Wear",
    1273: "Sportswear",
    337:  "Men's Activewear",
    857:  "Women's Activewear",
    1646: "Winter Coats & Jackets",
    414:  "Winter Wear",
    1645: "Rain Jackets & Outerwear",
    1114: "Outdoor Clothing",
    29:   "Men's Underwear & Basics",

    # ── SHOES & FOOTWEAR ──────────────────────────────────────────────
    342:  "Footwear",
    730:  "Shoes & Footwear",           # alias → 342 in CANONICAL_MAP
    637:  "Women's Shoes",
    154:  "Men's Shoes",
    1113: "Outdoor Footwear",
    633:  "Sport Shoes",
    343:  "Casual Shoes",
    352:  "Casual Footwear",            # alias → 343 in CANONICAL_MAP
    1670: "Winter Boots",

    # ── BAGS & LUGGAGE ────────────────────────────────────────────────
    589:  "Bags & Luggage",
    1020: "Bags & Backpacks",
    1172: "Handbags & Purses",
    124:  "Women's Handbags",
    723:  "Luggage & Travel Gear",
    256:  "Travel Accessories",

    # ── JEWELRY & WATCHES ─────────────────────────────────────────────
    646:  "Jewelry & Watches",
    225:  "Jewelry & Watches",          # alias → 646 in CANONICAL_MAP
    1191: "Jewelry & Accessories",
    23:   "Fashion Jewelry",
    224:  "Jewelry Organizers",

    # ── BEAUTY & PERSONAL CARE ────────────────────────────────────────
    1135: "Beauty & Personal Care",
    65:   "Personal Care",
    66:   "Personal Care Appliances",
    610:  "Hair Care",
    792:  "Skin Care",
    1220: "Oral Care",
    808:  "Makeup & Cosmetics",
    531:  "Makeup & Cosmetics",         # alias → 808 in CANONICAL_MAP
    532:  "Makeup Tools",
    806:  "Beauty Tools",
    1529: "Fragrances & Perfumes",
    1255: "Men's Grooming",
    324:  "Men's Grooming",             # alias → 1255 in CANONICAL_MAP
    1650: "Women's Grooming",
    1578: "Hair Styling Tools",
    302:  "Hair Styling Tools",         # alias → 1578 in CANONICAL_MAP
    1261: "Nail Care",
    628:  "Bath & Body",
    1503: "Bath & Shower Products",
    1349: "Bathroom Accessories",
    530:  "Skincare Tools",
    1694: "Electric Toothbrushes",

    # ── HEALTH & WELLNESS ─────────────────────────────────────────────
    1421: "Health & Wellness",
    1163: "Vitamins & Supplements",
    1221: "Dietary Supplements",
    1219: "Fitness Nutrition",
    1385: "Medical Supplies",
    1393: "First Aid & Safety",
    799:  "Vision Care",

    # ── SPORTS & FITNESS ──────────────────────────────────────────────
    491:  "Sports & Fitness",
    451:  "Fitness Equipment",
    1322: "Sports Accessories",
    1679: "Fitness Accessories",
    535:  "Team Sports",
    434:  "Yoga & Pilates",
    844:  "Cycling & Outdoor Sports",
    691:  "Cycling Gear",
    269:  "Cycling Accessories",
    1589: "Outdoor Gear",
    1265: "Camping Equipment",
    694:  "Camping Gear",               # alias → 1265 in CANONICAL_MAP
    421:  "Hiking & Trekking",
    1119: "Hiking Gear",
    914:  "Outdoor Recreation",
    499:  "Forest & Nature",

    # ── HOME & GARDEN ─────────────────────────────────────────────────
    1680: "Furniture & Home Decor",
    1258: "Home Decor",
    839:  "Home Decor",                 # alias → 1258 in CANONICAL_MAP
    1317: "Wall Art & Decor",
    1186: "Rugs & Carpets",
    209:  "Bedding & Linens",
    1477: "Home Textiles",
    1250: "Storage & Organization",
    876:  "Home Storage Solutions",     # alias → 1250 in CANONICAL_MAP
    1176: "Bookshelves & Shelving",
    1634: "Lighting & Lamps",
    1373: "Home Lighting",              # alias → 1634 in CANONICAL_MAP
    1616: "Outdoor Lighting",
    769:  "Garden & Outdoors",
    739:  "Garden Furniture",
    1403: "Gardening Tools",
    671:  "Outdoor Tools & Equipment",
    746:  "Seasonal Decor",
    1196: "Party Supplies",
    1197: "Party Decorations",          # alias → 1196 in CANONICAL_MAP
    396:  "Gifts & Occasions",
    35:   "Table Linens",
    523:  "Home Cleaning Tools",
    1384: "Cleaning & Household",

    # ── KITCHEN & DINING ──────────────────────────────────────────────
    618:  "Kitchen & Dining",
    928:  "Kitchen Appliances",
    619:  "Small Appliances",
    50:   "Kitchen Utensils",
    239:  "Kitchen Gadgets",
    1415: "Cookware & Bakeware",
    1500: "Dinnerware & Serveware",
    1344: "Kitchen Textiles",
    1026: "Kitchen Storage",
    1343: "Kitchen Storage & Organization",  # alias → 1026
    1528: "Coffee Makers",
    1581: "Coffee Machine Accessories",
    317:  "Blenders & Mixers",
    1404: "Food Processors",
    330:  "Microwaves",
    34:   "Wine & Bar",

    # ── HOME APPLIANCES ───────────────────────────────────────────────
    959:  "Home Appliances",
    333:  "Major Appliances",
    707:  "Air Conditioners",
    1151: "Heating & Cooling",
    1584: "Vacuum Cleaners",
    1493: "Vacuum Accessories",
    1188: "Laundry Appliances",
    1593: "Irons & Steamers",
    1244: "Refrigerators",
    72:   "Dishwashers",
    793:  "Freezers",
    1498: "Refrigerator Parts",

    # ── TOYS, KIDS & BABY ─────────────────────────────────────────────
    1279: "Toys & Games",
    398:  "Kids Toys",
    175:  "Baby Toys",
    782:  "Board Games",
    417:  "Board Games",                # alias → 782 in CANONICAL_MAP
    227:  "Puzzles & Brain Games",
    1117: "Educational Toys",
    126:  "Baby & Kids",
    1388: "Baby Care Products",

    # ── BOOKS & OFFICE ────────────────────────────────────────────────
    84:   "Books & Stationery",
    48:   "Office Supplies",
    1305: "Office Furniture",
    599:  "Home Office Furniture",
    1059: "Office Chairs",
    1455: "Office Organization",

    # ── AUTOMOTIVE ────────────────────────────────────────────────────
    624:  "Automotive Accessories",
    470:  "Car Accessories",
    429:  "Car Care Products",

    # ── PET SUPPLIES ──────────────────────────────────────────────────
    1205: "Pet Supplies",
    1085: "Pet Food & Supplies",
    1240: "Pet Food",
    1280: "Pet Accessories & Supplies",
    1441: "Pet Toys & Accessories",
    973:  "Pet Grooming",

    # ── FOOD & GROCERIES ──────────────────────────────────────────────
    926:  "Food & Groceries",
    316:  "Food & Beverages",

    # ── ARTS & CRAFTS ─────────────────────────────────────────────────
    1567: "Arts & Crafts",

    # ── TOOLS & HARDWARE ──────────────────────────────────────────────
    242:  "Tools & Hardware",
    1073: "Power Tools",
    869:  "Home Improvement Tools",
    1303: "Building Materials",
}


# ══════════════════════════════════════════════════════════════════════
#  2.  CANONICAL MAP  (alias_id → canonical_id)
#      When two IDs carry the same meaning, point the alias to the
#      canonical ID so deduplication logic is explicit and auditable.
# ══════════════════════════════════════════════════════════════════════

CANONICAL_MAP: Dict[int, int] = {
    # Fashion
    1233: 1,       # Men's Clothing (dup) → 1
    5:    1,       # Men's Fashion → Men's Clothing
    1277: 1192,    # Women's Clothing (dup) → 1192

    # Footwear
    730:  342,     # Shoes & Footwear → Footwear
    352:  343,     # Casual Footwear → Casual Shoes

    # Jewelry
    225:  646,     # Jewelry & Watches (dup) → 646

    # Beauty
    531:  808,     # Makeup & Beauty → Makeup & Cosmetics
    324:  1255,    # Men's Grooming (dup) → 1255
    302:  1578,    # Hair Styling Devices → Hair Styling Tools

    # Electronics
    984:  1364,    # Smartphone Cases → Phone Cases & Protectors
    558:  1355,    # Tablet Accessories (dup) → 1355
    195:  969,     # Audio Accessories (dup) → 969

    # Home
    839:  1258,    # Home Décor → Home Decor
    876:  1250,    # Home Storage Solutions → Storage & Organization
    1373: 1634,    # Home Lighting → Lighting & Lamps
    1197: 1196,    # Party Decorations → Party Supplies

    # Kitchen
    1343: 1026,    # Kitchen Storage & Organization → Kitchen Storage

    # Sports
    694:  1265,    # Camping Gear → Camping Equipment

    # Gaming
    417:  782,     # Board Games (dup) → 782
}


def canonical_id(category_id: int) -> int:
    """Resolve an alias category ID to its canonical ID."""
    return CANONICAL_MAP.get(category_id, category_id)


# ══════════════════════════════════════════════════════════════════════
#  3.  DEPARTMENT TREE  (3-level hierarchy for UI)
#
#      department → category → [subcategories]
#
#      This drives: sidebar nav, breadcrumbs, mega-menus, filters.
#      Category IDs in the lists reference CATEGORY_NAMES above.
# ══════════════════════════════════════════════════════════════════════

DEPARTMENT_TREE: Dict[str, Dict] = {
    "Electronics": {
        "icon": "🔌",
        "slug": "electronics",
        "ui_priority": 1,
        "categories": {
            "Mobile Phones": {
                "id": 683, "slug": "mobile-phones",
                "subcategories": [
                    {"id": 944, "name": "Smartphone Accessories"},
                    {"id": 1364, "name": "Phone Cases & Protectors"},
                    {"id": 819, "name": "Mobile Accessories"},
                ]
            },
            "Computers & Laptops": {
                "id": 1483, "slug": "computers-laptops",
                "subcategories": [
                    {"id": 686,  "name": "Laptops & Notebooks"},
                    {"id": 575,  "name": "Computer Components"},
                    {"id": 586,  "name": "Computer Accessories"},
                    {"id": 14,   "name": "Laptop Accessories"},
                    {"id": 684,  "name": "Laptop Bags"},
                    {"id": 1625, "name": "Printers & Scanners"},
                    {"id": 427,  "name": "Networking & Connectivity"},
                ]
            },
            "Audio & Headphones": {
                "id": 196, "slug": "audio-headphones",
                "subcategories": [
                    {"id": 828, "name": "Headphones & Earbuds"},
                    {"id": 1098, "name": "Audio Equipment"},
                    {"id": 818,  "name": "Audio Cables & Adapters"},
                ]
            },
            "TV & Home Entertainment": {
                "id": 936, "slug": "tv-home-entertainment",
                "subcategories": [
                    {"id": 57,   "name": "TV & Home Theatre"},
                ]
            },
            "Gaming": {
                "id": 1542, "slug": "gaming",
                "subcategories": [
                    {"id": 1473, "name": "Video Games"},
                    {"id": 438,  "name": "Gaming Accessories"},
                    {"id": 1018, "name": "Gaming Headsets"},
                ]
            },
            "Cameras & Photography": {
                "id": 1173, "slug": "cameras-photography",
                "subcategories": [
                    {"id": 958, "name": "Camera Accessories"},
                ]
            },
            "Wearables": {
                "id": 1375, "slug": "wearables",
                "subcategories": [
                    {"id": 1302, "name": "Smartwatch Accessories"},
                    {"id": 366,  "name": "Wearable Fitness Devices"},
                    {"id": 1642, "name": "Fitness Trackers"},
                ]
            },
            "Smart Home": {
                "id": 1248, "slug": "smart-home",
                "subcategories": [
                    {"id": 1070, "name": "Smart Lighting"},
                    {"id": 1089, "name": "Smart Home Accessories"},
                    {"id": 1286, "name": "Security Cameras"},
                    {"id": 282,  "name": "Home Security"},
                ]
            },
        },
    },

    "Fashion": {
        "icon": "👗",
        "slug": "fashion",
        "ui_priority": 2,
        "categories": {
            "Men's Fashion": {
                "id": 1, "slug": "mens-fashion",
                "subcategories": [
                    {"id": 337,  "name": "Men's Activewear"},
                    {"id": 1646, "name": "Winter Coats & Jackets"},
                    {"id": 29,   "name": "Men's Underwear & Basics"},
                    {"id": 228,  "name": "Fashion Accessories"},
                ]
            },
            "Women's Fashion": {
                "id": 1192, "slug": "womens-fashion",
                "subcategories": [
                    {"id": 857,  "name": "Women's Activewear"},
                    {"id": 1645, "name": "Rain Jackets & Outerwear"},
                    {"id": 228,  "name": "Fashion Accessories"},
                ]
            },
            "Kids & Baby Clothing": {
                "id": 406, "slug": "kids-baby-clothing",
                "subcategories": [
                    {"id": 390, "name": "Baby Clothing"},
                ]
            },
            "Shoes & Footwear": {
                "id": 342, "slug": "shoes-footwear",
                "subcategories": [
                    {"id": 154,  "name": "Men's Shoes"},
                    {"id": 637,  "name": "Women's Shoes"},
                    {"id": 633,  "name": "Sport Shoes"},
                    {"id": 343,  "name": "Casual Shoes"},
                    {"id": 1113, "name": "Outdoor Footwear"},
                    {"id": 1670, "name": "Winter Boots"},
                ]
            },
            "Bags & Luggage": {
                "id": 589, "slug": "bags-luggage",
                "subcategories": [
                    {"id": 1172, "name": "Handbags & Purses"},
                    {"id": 1020, "name": "Bags & Backpacks"},
                    {"id": 723,  "name": "Luggage & Travel Gear"},
                ]
            },
            "Jewelry & Watches": {
                "id": 646, "slug": "jewelry-watches",
                "subcategories": [
                    {"id": 23,   "name": "Fashion Jewelry"},
                    {"id": 1191, "name": "Jewelry & Accessories"},
                ]
            },
        },
    },

    "Beauty & Personal Care": {
        "icon": "✨",
        "slug": "beauty-personal-care",
        "ui_priority": 3,
        "categories": {
            "Skincare": {
                "id": 792, "slug": "skincare",
                "subcategories": [
                    {"id": 530,  "name": "Skincare Tools"},
                    {"id": 628,  "name": "Bath & Body"},
                    {"id": 1503, "name": "Bath & Shower Products"},
                ]
            },
            "Hair Care": {
                "id": 610, "slug": "hair-care",
                "subcategories": [
                    {"id": 1578, "name": "Hair Styling Tools"},
                ]
            },
            "Makeup": {
                "id": 808, "slug": "makeup",
                "subcategories": [
                    {"id": 532, "name": "Makeup Tools"},
                    {"id": 806, "name": "Beauty Tools"},
                    {"id": 1261, "name": "Nail Care"},
                ]
            },
            "Men's Grooming": {
                "id": 1255, "slug": "mens-grooming",
                "subcategories": [
                    {"id": 1694, "name": "Electric Toothbrushes"},
                ]
            },
            "Fragrances": {
                "id": 1529, "slug": "fragrances",
                "subcategories": []
            },
            "Oral Care": {
                "id": 1220, "slug": "oral-care",
                "subcategories": [
                    {"id": 1694, "name": "Electric Toothbrushes"},
                ]
            },
        },
    },

    "Health & Wellness": {
        "icon": "💊",
        "slug": "health-wellness",
        "ui_priority": 4,
        "categories": {
            "Vitamins & Supplements": {
                "id": 1163, "slug": "vitamins-supplements",
                "subcategories": [
                    {"id": 1221, "name": "Dietary Supplements"},
                    {"id": 1219, "name": "Fitness Nutrition"},
                ]
            },
            "Medical Supplies": {
                "id": 1385, "slug": "medical-supplies",
                "subcategories": [
                    {"id": 1393, "name": "First Aid & Safety"},
                    {"id": 799,  "name": "Vision Care"},
                ]
            },
        },
    },

    "Sports & Fitness": {
        "icon": "🏋️",
        "slug": "sports-fitness",
        "ui_priority": 5,
        "categories": {
            "Fitness Equipment": {
                "id": 451, "slug": "fitness-equipment",
                "subcategories": [
                    {"id": 1679, "name": "Fitness Accessories"},
                    {"id": 434,  "name": "Yoga & Pilates"},
                ]
            },
            "Outdoor Sports": {
                "id": 914, "slug": "outdoor-sports",
                "subcategories": [
                    {"id": 844,  "name": "Cycling & Outdoor Sports"},
                    {"id": 691,  "name": "Cycling Gear"},
                    {"id": 421,  "name": "Hiking & Trekking"},
                    {"id": 1119, "name": "Hiking Gear"},
                    {"id": 1589, "name": "Outdoor Gear"},
                    {"id": 1265, "name": "Camping Equipment"},
                ]
            },
            "Team Sports": {
                "id": 535, "slug": "team-sports",
                "subcategories": [
                    {"id": 1322, "name": "Sports Accessories"},
                ]
            },
            "Active Wear": {
                "id": 1573, "slug": "active-wear",
                "subcategories": [
                    {"id": 1273, "name": "Sportswear"},
                ]
            },
        },
    },

    "Home & Garden": {
        "icon": "🏠",
        "slug": "home-garden",
        "ui_priority": 6,
        "categories": {
            "Furniture & Decor": {
                "id": 1680, "slug": "furniture-decor",
                "subcategories": [
                    {"id": 1258, "name": "Home Decor"},
                    {"id": 1317, "name": "Wall Art & Decor"},
                    {"id": 1186, "name": "Rugs & Carpets"},
                    {"id": 1176, "name": "Bookshelves & Shelving"},
                    {"id": 1059, "name": "Office Chairs"},
                ]
            },
            "Bedding & Bath": {
                "id": 209, "slug": "bedding-bath",
                "subcategories": [
                    {"id": 1477, "name": "Home Textiles"},
                    {"id": 1349, "name": "Bathroom Accessories"},
                ]
            },
            "Storage & Organisation": {
                "id": 1250, "slug": "storage-organisation",
                "subcategories": []
            },
            "Lighting": {
                "id": 1634, "slug": "lighting",
                "subcategories": [
                    {"id": 1070, "name": "Smart Lighting"},
                    {"id": 1616, "name": "Outdoor Lighting"},
                ]
            },
            "Garden & Outdoors": {
                "id": 769, "slug": "garden-outdoors",
                "subcategories": [
                    {"id": 739,  "name": "Garden Furniture"},
                    {"id": 1403, "name": "Gardening Tools"},
                    {"id": 671,  "name": "Outdoor Tools & Equipment"},
                ]
            },
            "Cleaning & Household": {
                "id": 1384, "slug": "cleaning-household",
                "subcategories": [
                    {"id": 523, "name": "Home Cleaning Tools"},
                ]
            },
            "Seasonal & Gifts": {
                "id": 396, "slug": "seasonal-gifts",
                "subcategories": [
                    {"id": 746,  "name": "Seasonal Decor"},
                    {"id": 1196, "name": "Party Supplies"},
                ]
            },
        },
    },

    "Kitchen & Dining": {
        "icon": "🍳",
        "slug": "kitchen-dining",
        "ui_priority": 7,
        "categories": {
            "Kitchen Appliances": {
                "id": 928, "slug": "kitchen-appliances",
                "subcategories": [
                    {"id": 1528, "name": "Coffee Makers"},
                    {"id": 317,  "name": "Blenders & Mixers"},
                    {"id": 1404, "name": "Food Processors"},
                    {"id": 330,  "name": "Microwaves"},
                    {"id": 619,  "name": "Small Appliances"},
                ]
            },
            "Cookware & Bakeware": {
                "id": 1415, "slug": "cookware-bakeware",
                "subcategories": [
                    {"id": 50,   "name": "Kitchen Utensils"},
                    {"id": 239,  "name": "Kitchen Gadgets"},
                    {"id": 1500, "name": "Dinnerware & Serveware"},
                ]
            },
            "Kitchen Storage": {
                "id": 1026, "slug": "kitchen-storage",
                "subcategories": [
                    {"id": 1344, "name": "Kitchen Textiles"},
                    {"id": 35,   "name": "Table Linens"},
                ]
            },
            "Wine & Bar": {
                "id": 34, "slug": "wine-bar",
                "subcategories": []
            },
        },
    },

    "Home Appliances": {
        "icon": "🧺",
        "slug": "home-appliances",
        "ui_priority": 8,
        "categories": {
            "Major Appliances": {
                "id": 333, "slug": "major-appliances",
                "subcategories": [
                    {"id": 707,  "name": "Air Conditioners"},
                    {"id": 1151, "name": "Heating & Cooling"},
                    {"id": 1244, "name": "Refrigerators"},
                    {"id": 72,   "name": "Dishwashers"},
                    {"id": 793,  "name": "Freezers"},
                    {"id": 1188, "name": "Laundry Appliances"},
                ]
            },
            "Vacuum Cleaners": {
                "id": 1584, "slug": "vacuum-cleaners",
                "subcategories": [
                    {"id": 1493, "name": "Vacuum Accessories"},
                ]
            },
            "Irons & Garment Care": {
                "id": 1593, "slug": "irons-garment-care",
                "subcategories": []
            },
        },
    },

    "Toys, Kids & Baby": {
        "icon": "🧸",
        "slug": "toys-kids-baby",
        "ui_priority": 9,
        "categories": {
            "Toys & Games": {
                "id": 1279, "slug": "toys-games",
                "subcategories": [
                    {"id": 782,  "name": "Board Games"},
                    {"id": 227,  "name": "Puzzles & Brain Games"},
                    {"id": 1117, "name": "Educational Toys"},
                    {"id": 398,  "name": "Kids Toys"},
                ]
            },
            "Baby": {
                "id": 126, "slug": "baby",
                "subcategories": [
                    {"id": 390,  "name": "Baby Clothing"},
                    {"id": 175,  "name": "Baby Toys"},
                    {"id": 1388, "name": "Baby Care Products"},
                ]
            },
        },
    },

    "Books & Office": {
        "icon": "📚",
        "slug": "books-office",
        "ui_priority": 10,
        "categories": {
            "Books & Stationery": {
                "id": 84, "slug": "books-stationery",
                "subcategories": []
            },
            "Office Supplies": {
                "id": 48, "slug": "office-supplies",
                "subcategories": [
                    {"id": 1455, "name": "Office Organisation"},
                ]
            },
            "Office Furniture": {
                "id": 1305, "slug": "office-furniture",
                "subcategories": [
                    {"id": 599,  "name": "Home Office Furniture"},
                    {"id": 1059, "name": "Office Chairs"},
                ]
            },
        },
    },

    "Automotive": {
        "icon": "🚗",
        "slug": "automotive",
        "ui_priority": 11,
        "categories": {
            "Car Accessories": {
                "id": 624, "slug": "car-accessories",
                "subcategories": [
                    {"id": 470,  "name": "Car Accessories"},
                    {"id": 429,  "name": "Car Care Products"},
                    {"id": 1418, "name": "Car Electronics"},
                ]
            },
        },
    },

    "Pet Supplies": {
        "icon": "🐾",
        "slug": "pet-supplies",
        "ui_priority": 12,
        "categories": {
            "Pet Food": {
                "id": 1240, "slug": "pet-food",
                "subcategories": [
                    {"id": 1085, "name": "Pet Food & Supplies"},
                ]
            },
            "Pet Accessories": {
                "id": 1280, "slug": "pet-accessories",
                "subcategories": [
                    {"id": 1441, "name": "Pet Toys & Accessories"},
                    {"id": 973,  "name": "Pet Grooming"},
                ]
            },
        },
    },

    "Food & Groceries": {
        "icon": "🛒",
        "slug": "food-groceries",
        "ui_priority": 13,
        "categories": {
            "Food & Beverages": {
                "id": 926, "slug": "food-beverages",
                "subcategories": [
                    {"id": 316, "name": "Food & Beverages"},
                ]
            },
        },
    },

    "Tools & Hardware": {
        "icon": "🔧",
        "slug": "tools-hardware",
        "ui_priority": 14,
        "categories": {
            "Power Tools": {
                "id": 1073, "slug": "power-tools",
                "subcategories": [
                    {"id": 869,  "name": "Home Improvement Tools"},
                    {"id": 1303, "name": "Building Materials"},
                ]
            },
            "Hand Tools": {
                "id": 242, "slug": "hand-tools",
                "subcategories": []
            },
        },
    },

    "Arts & Crafts": {
        "icon": "🎨",
        "slug": "arts-crafts",
        "ui_priority": 15,
        "categories": {
            "Arts & Crafts": {
                "id": 1567, "slug": "arts-crafts",
                "subcategories": [
                    {"id": 1111, "name": "Musical Accessories"},
                ]
            },
        },
    },
}


# ══════════════════════════════════════════════════════════════════════
#  4.  CATEGORY SLUGS  (id → slug)
#      Auto-generated from CATEGORY_NAMES for URL-safe routing.
# ══════════════════════════════════════════════════════════════════════

def _slugify(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

CATEGORY_SLUGS: Dict[int, str] = {
    cid: _slugify(name) for cid, name in CATEGORY_NAMES.items()
}


# ══════════════════════════════════════════════════════════════════════
#  5.  CATEGORY METADATA  (id → metadata dict)
#      Covers the top ~60 most navigated categories.
#      Lightweight — add more entries as needed.
# ══════════════════════════════════════════════════════════════════════

CATEGORY_METADATA: Dict[int, Dict] = {
    1051: {"icon": "🔌", "department": "Electronics",          "featured": True,  "ui_priority": 1},
    683:  {"icon": "📱", "department": "Electronics",          "featured": True,  "ui_priority": 2},
    686:  {"icon": "💻", "department": "Electronics",          "featured": True,  "ui_priority": 3},
    1483: {"icon": "🖥️", "department": "Electronics",          "featured": True,  "ui_priority": 4},
    196:  {"icon": "🎧", "department": "Electronics",          "featured": True,  "ui_priority": 5},
    1542: {"icon": "🎮", "department": "Electronics",          "featured": True,  "ui_priority": 6},
    1248: {"icon": "🏠", "department": "Electronics",          "featured": False, "ui_priority": 7},
    1375: {"icon": "⌚", "department": "Electronics",          "featured": True,  "ui_priority": 8},
    1173: {"icon": "📷", "department": "Electronics",          "featured": False, "ui_priority": 9},

    1:    {"icon": "👔", "department": "Fashion",              "featured": True,  "ui_priority": 1},
    1192: {"icon": "👗", "department": "Fashion",              "featured": True,  "ui_priority": 2},
    342:  {"icon": "👟", "department": "Fashion",              "featured": True,  "ui_priority": 3},
    589:  {"icon": "👜", "department": "Fashion",              "featured": True,  "ui_priority": 4},
    646:  {"icon": "💍", "department": "Fashion",              "featured": True,  "ui_priority": 5},
    406:  {"icon": "👶", "department": "Fashion",              "featured": False, "ui_priority": 6},

    1135: {"icon": "💄", "department": "Beauty & Personal Care", "featured": True,  "ui_priority": 1},
    792:  {"icon": "🧴", "department": "Beauty & Personal Care", "featured": True,  "ui_priority": 2},
    808:  {"icon": "💋", "department": "Beauty & Personal Care", "featured": True,  "ui_priority": 3},
    610:  {"icon": "💇", "department": "Beauty & Personal Care", "featured": False, "ui_priority": 4},
    1529: {"icon": "🌸", "department": "Beauty & Personal Care", "featured": False, "ui_priority": 5},

    491:  {"icon": "🏋️", "department": "Sports & Fitness",    "featured": True,  "ui_priority": 1},
    451:  {"icon": "🏃", "department": "Sports & Fitness",    "featured": True,  "ui_priority": 2},
    914:  {"icon": "⛺", "department": "Sports & Fitness",    "featured": False, "ui_priority": 3},
    1573: {"icon": "🩱", "department": "Sports & Fitness",    "featured": False, "ui_priority": 4},

    1421: {"icon": "💊", "department": "Health & Wellness",   "featured": True,  "ui_priority": 1},
    1163: {"icon": "🧪", "department": "Health & Wellness",   "featured": True,  "ui_priority": 2},

    1680: {"icon": "🛋️", "department": "Home & Garden",       "featured": True,  "ui_priority": 1},
    769:  {"icon": "🌿", "department": "Home & Garden",       "featured": False, "ui_priority": 2},
    1258: {"icon": "🖼️", "department": "Home & Garden",       "featured": False, "ui_priority": 3},
    1250: {"icon": "📦", "department": "Home & Garden",       "featured": False, "ui_priority": 4},

    618:  {"icon": "🍳", "department": "Kitchen & Dining",    "featured": True,  "ui_priority": 1},
    928:  {"icon": "☕", "department": "Kitchen & Dining",    "featured": True,  "ui_priority": 2},
    1415: {"icon": "🥘", "department": "Kitchen & Dining",    "featured": False, "ui_priority": 3},

    959:  {"icon": "🧺", "department": "Home Appliances",     "featured": True,  "ui_priority": 1},
    333:  {"icon": "🧊", "department": "Home Appliances",     "featured": False, "ui_priority": 2},
    1584: {"icon": "🌀", "department": "Home Appliances",     "featured": False, "ui_priority": 3},

    1279: {"icon": "🧸", "department": "Toys, Kids & Baby",   "featured": True,  "ui_priority": 1},
    126:  {"icon": "👶", "department": "Toys, Kids & Baby",   "featured": False, "ui_priority": 2},

    84:   {"icon": "📚", "department": "Books & Office",      "featured": True,  "ui_priority": 1},
    48:   {"icon": "📎", "department": "Books & Office",      "featured": False, "ui_priority": 2},

    624:  {"icon": "🚗", "department": "Automotive",          "featured": False, "ui_priority": 1},
    1205: {"icon": "🐾", "department": "Pet Supplies",        "featured": True,  "ui_priority": 1},
    926:  {"icon": "🛒", "department": "Food & Groceries",    "featured": True,  "ui_priority": 1},
    242:  {"icon": "🔧", "department": "Tools & Hardware",    "featured": False, "ui_priority": 1},
    1567: {"icon": "🎨", "department": "Arts & Crafts",       "featured": False, "ui_priority": 1},
}


# ══════════════════════════════════════════════════════════════════════
#  6.  CATEGORY DEPARTMENTS  (flat lookup: id → department name)
#      Derived from CATEGORY_METADATA + DEPARTMENT_TREE fallback.
# ══════════════════════════════════════════════════════════════════════

CATEGORY_DEPARTMENTS: Dict[int, str] = {
    cid: meta["department"] for cid, meta in CATEGORY_METADATA.items()
}


# ══════════════════════════════════════════════════════════════════════
#  7.  CATEGORY TREE (CSV-based parent map) — unchanged from v1
# ══════════════════════════════════════════════════════════════════════

def load_category_tree() -> Dict:
    try:
        tree_path = os.path.join(os.path.dirname(__file__), 'data', 'category_tree.csv')
        if not os.path.exists(tree_path):
            tree_path = os.path.join(os.path.dirname(__file__), 'category_tree.csv')
        df_tree = pd.read_csv(tree_path)
        df_tree['categoryid'] = pd.to_numeric(df_tree['categoryid'], errors='coerce').astype('Int64')
        df_tree['parentid']   = pd.to_numeric(df_tree['parentid'],   errors='coerce').astype('Int64')
        return df_tree.set_index('categoryid')['parentid'].to_dict()
    except Exception as e:
        print(f"Warning: Could not load category_tree.csv: {e}")
        return {}

PARENT_MAP = load_category_tree()


# ══════════════════════════════════════════════════════════════════════
#  8.  CORE FUNCTIONS  (backward-compatible — all v1 signatures kept)
# ══════════════════════════════════════════════════════════════════════

def get_category_name(category_id) -> str:
    """Return a clean display name for any category ID."""
    try:
        cid = int(category_id)
        # Resolve alias → canonical name
        resolved = canonical_id(cid)
        if resolved in CATEGORY_NAMES:
            return CATEGORY_NAMES[resolved]
        if cid in CATEGORY_NAMES:
            return CATEGORY_NAMES[cid]
        # Hierarchical CSV fallback
        if cid in PARENT_MAP:
            parent_id = PARENT_MAP[cid]
            if parent_id and int(parent_id) in CATEGORY_NAMES:
                return f"{CATEGORY_NAMES[int(parent_id)]} › Subcategory {cid}"
        return f"Category {cid}"
    except Exception:
        return f"Category {category_id}"


def get_category_names_list(category_ids: list) -> list:
    """Batch version of get_category_name."""
    return [get_category_name(cid) for cid in category_ids]


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Add category_name column. Optionally enriches with slug and department."""
    df = df.copy()
    df["category_name"]       = df["categoryid"].apply(get_category_name)
    df["category_slug"]       = df["categoryid"].apply(
        lambda cid: CATEGORY_SLUGS.get(canonical_id(int(cid)), _slugify(get_category_name(cid)))
    )
    df["category_department"] = df["categoryid"].apply(
        lambda cid: CATEGORY_DEPARTMENTS.get(canonical_id(int(cid)), "Other")
    )
    return df


def print_mapping_coverage(df: pd.DataFrame) -> float:
    total  = len(df)
    mapped = df["categoryid"].isin(CATEGORY_NAMES.keys()).sum()
    coverage = mapped / total * 100
    print(f"✅ Manual mapping coverage: {coverage:.1f}%")
    print(f"   Remaining IDs use hierarchical fallback names")
    return coverage


# ══════════════════════════════════════════════════════════════════════
#  9.  DETAIL → PRODUCT COARSE GROUPING  (expanded v2)
#      Maps display names → recommendation group labels.
#      Still drives to_product_category() exactly as before.
# ══════════════════════════════════════════════════════════════════════

DETAIL_TO_PRODUCT: Dict[str, str] = {
    # tech
    "Electronics & Gadgets": "tech",   "Computers & Accessories": "tech",
    "Mobile Phones": "tech",           "Laptops & Notebooks": "tech",
    "Audio & Headphones": "tech",      "Gaming & Consoles": "tech",
    "Headphones & Earbuds": "tech",    "Smart Home Devices": "tech",
    "Wearables & Smartwatches": "tech","TV & Home Theatre": "tech",
    "Home Entertainment": "tech",      "Cameras & Photography": "tech",
    "Printers & Scanners": "tech",     "Computer Accessories": "tech",
    "Networking & Connectivity": "tech","Computer Components": "tech",
    "Gaming Accessories": "tech",      "Gaming Peripherals": "tech",
    "Gaming Headsets": "tech",         "Video Games": "tech",
    "Smartphone Accessories": "tech",  "Mobile Accessories": "tech",
    "Phone Cases & Protectors": "tech","Tablet Accessories": "tech",
    "Smart Lighting": "tech",          "Security Cameras": "tech",
    "Home Security": "tech",           "Laptop Accessories": "tech",
    "Car Electronics": "tech",         "Wearable Fitness Devices": "tech",
    "Fitness Trackers": "tech",        "Audio Equipment": "tech",
    "Smartwatch Accessories": "tech",

    # fashion
    "Clothing & Apparel": "fashion",   "Footwear": "fashion",
    "Women's Clothing": "fashion",     "Men's Clothing": "fashion",
    "Women's Fashion": "fashion",      "Men's Fashion": "fashion",
    "Kids Clothing": "fashion",        "Baby Clothing": "fashion",
    "Fashion Accessories": "fashion",  "Winter Accessories": "fashion",
    "Active Wear": "fashion",          "Sportswear": "fashion",
    "Men's Activewear": "fashion",     "Women's Activewear": "fashion",
    "Winter Coats & Jackets": "fashion","Rain Jackets & Outerwear": "fashion",
    "Outdoor Clothing": "fashion",     "Men's Underwear & Basics": "fashion",
    "Women's Shoes": "fashion",        "Men's Shoes": "fashion",
    "Sport Shoes": "fashion",          "Casual Shoes": "fashion",
    "Outdoor Footwear": "fashion",     "Winter Boots": "fashion",
    "Bags & Luggage": "fashion",       "Handbags & Purses": "fashion",
    "Bags & Backpacks": "fashion",     "Luggage & Travel Gear": "fashion",
    "Jewelry & Watches": "fashion",    "Fashion Jewelry": "fashion",
    "Jewelry & Accessories": "fashion","Women's Handbags": "fashion",
    "Shoes & Footwear": "fashion",     "Makeup & Cosmetics": "fashion",
    "Fragrances & Perfumes": "fashion","Beauty & Personal Care": "fashion",

    # food
    "Kitchen & Dining": "food",        "Food & Groceries": "food",
    "Kitchen Appliances": "food",      "Cookware & Bakeware": "food",
    "Kitchen Utensils": "food",        "Kitchen Gadgets": "food",
    "Blenders & Mixers": "food",       "Food Processors": "food",
    "Coffee Makers": "food",           "Small Appliances": "food",
    "Dinnerware & Serveware": "food",  "Wine & Bar": "food",
    "Food & Beverages": "food",        "Kitchen Storage": "food",
    "Microwaves": "food",              "Air Conditioners": "food",

    # fitness
    "Sports & Fitness": "fitness",     "Fitness Equipment": "fitness",
    "Health & Wellness": "fitness",    "Vitamins & Supplements": "fitness",
    "Dietary Supplements": "fitness",  "Fitness Nutrition": "fitness",
    "Medical Supplies": "fitness",     "First Aid & Safety": "fitness",
    "Vision Care": "fitness",          "Yoga & Pilates": "fitness",
    "Sports Accessories": "fitness",   "Fitness Accessories": "fitness",
    "Active Wear": "fitness",          "Wearable Fitness Devices": "fitness",
    "Fitness Trackers": "fitness",

    # travel
    "Garden & Outdoors": "travel",     "Outdoor Gear": "travel",
    "Camping Equipment": "travel",     "Hiking & Trekking": "travel",
    "Outdoor Recreation": "travel",    "Cycling & Outdoor Sports": "travel",
    "Cycling Gear": "travel",          "Travel Accessories": "travel",
    "Luggage & Travel Gear": "travel", "Forest & Nature": "travel",
    "Hiking Gear": "travel",

    # finance
    "Office Supplies": "finance",      "Books & Stationery": "finance",
    "Office Furniture": "finance",     "Home Office Furniture": "finance",
    "Office Chairs": "finance",        "Office Organisation": "finance",
}


def to_product_category(detail_name: str, categoryid: Optional[int] = None) -> str:
    """Map a display name to a coarse product group. Backward compatible."""
    if detail_name in DETAIL_TO_PRODUCT:
        return DETAIL_TO_PRODUCT[detail_name]

    # Try resolving alias
    if categoryid:
        resolved_name = get_category_name(categoryid)
        if resolved_name in DETAIL_TO_PRODUCT:
            return DETAIL_TO_PRODUCT[resolved_name]

    # Hierarchical CSV fallback
    if categoryid and categoryid in PARENT_MAP:
        parent_name = get_category_name(PARENT_MAP[categoryid])
        if parent_name in DETAIL_TO_PRODUCT:
            return DETAIL_TO_PRODUCT[parent_name]

    # Keyword heuristic fallback
    name_lower = detail_name.lower()
    if any(k in name_lower for k in ["phone", "laptop", "computer", "gaming", "audio", "camera", "smart"]):
        return "tech"
    if any(k in name_lower for k in ["cloth", "shoe", "bag", "jewel", "fashion", "wear", "boot"]):
        return "fashion"
    if any(k in name_lower for k in ["kitchen", "food", "cook", "coffee", "blender"]):
        return "food"
    if any(k in name_lower for k in ["fitness", "sport", "yoga", "gym", "health", "vitamin"]):
        return "fitness"
    if any(k in name_lower for k in ["travel", "outdoor", "camp", "hike", "garden"]):
        return "travel"
    if any(k in name_lower for k in ["office", "book", "stationery", "finance"]):
        return "finance"

    # Deterministic hash fallback (preserves original behaviour)
    if categoryid:
        labels = ["tech", "fashion", "food", "fitness", "travel", "finance"]
        return labels[int(categoryid) % 6]
    return "tech"


# ══════════════════════════════════════════════════════════════════════
#  10.  NEW HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def get_breadcrumb(category_id: int) -> List[str]:
    """
    Return a breadcrumb list: [Department, Category, display_name].
    Useful for page headers and SEO structured data.
    """
    cid = canonical_id(category_id)
    name = get_category_name(cid)
    dept = CATEGORY_DEPARTMENTS.get(cid, "")

    for dept_name, dept_data in DEPARTMENT_TREE.items():
        for cat_name, cat_data in dept_data.get("categories", {}).items():
            if cat_data["id"] == cid:
                return [dept_name, cat_name, name]
            for sub in cat_data.get("subcategories", []):
                if sub["id"] == cid:
                    return [dept_name, cat_name, name]

    return [dept, name] if dept else [name]


def get_department(category_id: int) -> str:
    """Return the top-level department for a category ID."""
    cid = canonical_id(category_id)
    return CATEGORY_DEPARTMENTS.get(cid, "Other")


def get_sidebar_nav() -> List[Dict]:
    """
    Return a structured list for rendering a sidebar navigation menu.
    Each entry has: department, icon, slug, ui_priority, categories.
    """
    nav = []
    for dept_name, dept_data in sorted(
        DEPARTMENT_TREE.items(), key=lambda x: x[1].get("ui_priority", 99)
    ):
        nav.append({
            "department": dept_name,
            "icon":       dept_data.get("icon", ""),
            "slug":       dept_data.get("slug", _slugify(dept_name)),
            "ui_priority":dept_data.get("ui_priority", 99),
            "categories": [
                {
                    "name": cat_name,
                    "id":   cat_data["id"],
                    "slug": cat_data.get("slug", _slugify(cat_name)),
                    "subcategories": cat_data.get("subcategories", []),
                }
                for cat_name, cat_data in dept_data.get("categories", {}).items()
            ],
        })
    return nav


def get_featured_categories() -> List[Dict]:
    """Return featured categories for homepage banners / hero carousels."""
    return [
        {"id": cid, "name": CATEGORY_NAMES[cid], **meta}
        for cid, meta in sorted(
            CATEGORY_METADATA.items(), key=lambda x: x[1].get("ui_priority", 99)
        )
        if meta.get("featured")
    ]


def get_filter_options(department: str) -> List[Dict]:
    """
    Return filter options for a given department page.
    Drives left-panel filters (category checkboxes).
    """
    dept = DEPARTMENT_TREE.get(department, {})
    filters = []
    for cat_name, cat_data in dept.get("categories", {}).items():
        filters.append({
            "label": cat_name,
            "id":    cat_data["id"],
            "count": len(cat_data.get("subcategories", [])) + 1,
        })
    return filters












# # data/category_map.py
# # Clean, judge-friendly category mapping for BehaviorIQ
# # Coverage optimized for demo + Kafka real-time

# import pandas as pd
# import os
# from typing import Dict, List, Optional

# # ====================== MANUAL MAPPINGS ======================
# CATEGORY_NAMES = {
#     # === ORIGINAL HIGH-QUALITY MAPPINGS ===
#     1051: "Electronics & Gadgets",
#     959:  "Home Appliances",
#     858:  "Clothing & Apparel",
#     491:  "Sports & Fitness",
#     1135: "Beauty & Personal Care",
#     618:  "Kitchen & Dining",
#     1483: "Computers & Accessories",
#     1279: "Toys & Games",
#     84:   "Books & Stationery",
#     342:  "Footwear",
#     646:  "Jewelry & Watches",
#     683:  "Mobile Phones",
#     769:  "Garden & Outdoors",
#     126:  "Baby & Kids",
#     1680: "Furniture & Decor",
#     196:  "Audio & Headphones",
#     1173: "Cameras & Photography",
#     1421: "Health & Wellness",
#     589:  "Bags & Luggage",
#     624:  "Automotive Accessories",
#     48:   "Office Supplies",
#     1375: "Wearables & Smartwatches",
#     926:  "Food & Groceries",
#     1205: "Pet Supplies",
#     1567: "Arts & Crafts",
#     1384: "Cleaning & Household",
#     242:  "Tools & Hardware",
#     1163: "Vitamins & Supplements",
#     844:  "Cycling & Outdoor Sports",
#     1542: "Gaming & Consoles",
#     936:  "Home Entertainment",
#     928:  "Kitchen Appliances",
#     686:  "Laptops & Notebooks",
#     1248: "Smart Home Devices",
#     1625: "Printers & Scanners",
#     586:  "Computer Accessories",
#     427:  "Networking & Connectivity",
#     5:    "Men's Fashion",
#     1192: "Women's Fashion",
#     406:  "Kids Clothing",
#     1258: "Home Decor",
#     209:  "Bedding & Linens",
#     1250: "Storage & Organization",
#     914:  "Outdoor Recreation",
#     451:  "Fitness Equipment",
#     535:  "Team Sports",
#     65:   "Personal Care",
#     610:  "Hair Care",
#     792:  "Skin Care",
#     1220: "Oral Care",
#     1322: "Sports Accessories",
#     1573: "Active Wear",
#     1385: "Medical Supplies",
#     1393: "First Aid & Safety",
#     799:  "Vision Care",
#     1221: "Dietary Supplements",
#     1219: "Fitness Nutrition",
#     434:  "Yoga & Pilates",
#     1589: "Outdoor Gear",
#     1265: "Camping Equipment",
#     421:  "Hiking & Trekking",
#     57:   "TV & Home Theatre",
#     1098: "Audio Equipment",
#     1473: "Video Games",
#     438:  "Gaming Accessories",
#     782:  "Board Games",
#     227:  "Puzzles & Brain Games",
#     1117: "Educational Toys",
#     1529: "Fragrances & Perfumes",
#     1255: "Men's Grooming",
#     1650: "Women's Grooming",
#     1578: "Hair Styling Tools",
#     808:  "Makeup & Cosmetics",
#     1261: "Nail Care",
#     628:  "Bath & Body",
#     282:  "Home Security",
#     1070: "Smart Lighting",
#     50:   "Kitchen Utensils",
#     1415: "Cookware & Bakeware",
#     1500: "Dinnerware & Serveware",
#     619:  "Small Appliances",
#     333:  "Major Appliances",
#     707:  "Air Conditioners",
#     1151: "Heating & Cooling",
#     1584: "Vacuum Cleaners",
#     1188: "Laundry Appliances",
#     1593: "Irons & Steamers",
#     1528: "Coffee Makers",
#     317:  "Blenders & Mixers",
#     1404: "Food Processors",
#     330:  "Microwaves",
#     1244: "Refrigerators",
#     72:   "Dishwashers",
#     793:  "Freezers",
#     34:   "Wine & Bar",
#     1026: "Kitchen Storage",
#     35:   "Table Linens",
#     1196: "Party Supplies",
#     396:  "Gifts & Occasions",
#     746:  "Seasonal Decor",
#     1317: "Wall Art & Decor",
#     1186: "Rugs & Carpets",

#     # === ADDED HIGH-FREQUENCY CATEGORIES (Clean & Non-repetitive) ===
#     14:    "Laptop Accessories",
#     1040:  "Computer Peripherals",
#     1364:  "Phone Cases & Protectors",
#     828:   "Headphones & Earbuds",
#     1355:  "Tablet Accessories",
#     958:   "Camera Accessories",
#     1302:  "Smartwatch Accessories",
#     411:   "Gaming Peripherals",
#     1113:  "Outdoor Footwear",
#     1:     "Men's Clothing",
#     1043:  "Printer Supplies",
#     1172:  "Handbags & Purses",
#     1373:  "Home Lighting",
#     239:   "Kitchen Gadgets",
#     302:   "Hair Styling Devices",
#     366:   "Wearable Fitness Devices",
#     1286:  "Security Cameras",
#     1441:  "Pet Toys & Accessories",
#     1646:  "Winter Coats & Jackets",
#     1418:  "Car Electronics",
#     684:   "Laptop Bags",
#     739:   "Garden Furniture",
#     1059:  "Office Chairs",
#     1493:  "Vacuum Accessories",
#     1581:  "Coffee Machine Accessories",
#     1349:  "Bathroom Accessories",
#     691:   "Cycling Gear",
#     1119:  "Hiking Gear",
#     819:   "Mobile Accessories",
#     228:   "Fashion Accessories",
#     1277:  "Women's Clothing",
#     1233:  "Men's Clothing",
#     730:   "Shoes & Footwear",
#     1020:  "Bags & Backpacks",
#     1191: "Jewelry & Accessories",
#     806:   "Beauty Tools",
#     1477:  "Home Textiles",
#     1503:  "Bath & Shower Products",
#     575:   "Computer Components",
#     1037:  "Networking Equipment",
#     984:   "Smartphone Cases",
#     1114:  "Outdoor Clothing",
#     1344:  "Kitchen Textiles",
#     1634:  "Lighting & Lamps",
#     1085:  "Pet Food & Supplies",
#     1305:  "Office Furniture",
#     1273:  "Sportswear",
#     470:   "Car Accessories",
#     1388:  "Baby Care Products",
#     1403:  "Gardening Tools",
#     969:   "Audio Accessories",
#     414:   "Winter Wear",
#     352:   "Casual Footwear",
#     532:   "Makeup Tools",
#     256:   "Travel Accessories",
#     876:   "Home Storage Solutions",
#     1679:  "Fitness Accessories",
#     558:   "Tablet Accessories",


#     637:  "Women's Shoes",
#     390:  "Baby Clothing",
#     531:  "Makeup & Beauty",
#     633:  "Sport Shoes",
#     857:  "Women's Activewear",
#     324:  "Men's Grooming",
#     398:  "Kids Toys",
#     417:  "Board Games",
#     818:  "Audio Cables & Adapters",
#     1498: "Refrigerator Parts",
#     224:  "Jewelry Organizers",
#     1240: "Pet Food",
#     269:  "Cycling Accessories",
#     530:  "Skincare Tools",
#     337:  "Men's Activewear",


#     1089: "Smart Home Accessories",
#     1035: "Laptop Peripherals",
#     437:  "Winter Accessories",
#     523:  "Home Cleaning Tools",
#     225:  "Jewelry & Watches",
#     195:  "Audio Accessories",
#     1645: "Rain Jackets & Outerwear",
#     29:   "Men's Underwear & Basics",
#     175:  "Baby Toys",
#     124:  "Women's Handbags",
#     1694: "Electric Toothbrushes",
#     1073: "Power Tools",
#     1018: "Gaming Headsets",
#     343:  "Casual Shoes",
#     429:  "Car Care Products",
#     316:  "Food & Beverages",
#     1303: "Building Materials",
#     1111: "Musical Accessories",
#     1176: "Book Shelves",
#     839:  "Home Décor",
#     1616: "Outdoor Lighting",
#     1670: "Winter Boots",
#     1642: "Fitness Trackers",
#     1197: "Party Decorations",
#     869:  "Home Improvement Tools",
#     973:  "Pet Grooming",
#     1455: "Office Organization",
#     23:  "Fashion Jewelry",
#     154: "Men's Shoes",
#     1343: "Kitchen Storage & Organization",
#     471: "Car Electronics & Accessories",
#     694: "Camping Gear",
#     66:  "Personal Care Appliances",
#     1280: "Pet Accessories & Supplies",  
#     944:  "Smartphone Accessories", 
#     499: "Forest & Nature",
#     723: "Luggage & Travel Gear",
#     599: "Home Office Furniture",
#     671: "Outdoor Tools & Equipment",


# }

# # ====================== CATEGORY TREE ======================
# def load_category_tree() -> Dict:
#     try:
#         tree_path = os.path.join(os.path.dirname(__file__), 'data', 'category_tree.csv')
#         if not os.path.exists(tree_path):
#             tree_path = os.path.join(os.path.dirname(__file__), 'category_tree.csv')
        
#         df_tree = pd.read_csv(tree_path)
#         df_tree['categoryid'] = pd.to_numeric(df_tree['categoryid'], errors='coerce').astype('Int64')
#         df_tree['parentid'] = pd.to_numeric(df_tree['parentid'], errors='coerce').astype('Int64')
#         return df_tree.set_index('categoryid')['parentid'].to_dict()
#     except Exception as e:
#         print(f"Warning: Could not load category_tree.csv: {e}")
#         return {}

# PARENT_MAP = load_category_tree()


# def get_category_name(category_id) -> str:
#     """Clean professional names for judges"""
#     try:
#         cid = int(category_id)
        
#         if cid in CATEGORY_NAMES:
#             return CATEGORY_NAMES[cid]
        
#         # Hierarchical fallback
#         if cid in PARENT_MAP:
#             parent_id = PARENT_MAP[cid]
#             if parent_id and parent_id in CATEGORY_NAMES:
#                 return f"{CATEGORY_NAMES[parent_id]} › Subcategory {cid}"
        
#         return f"Category {cid}"
        
#     except:
#         return f"Category {category_id}"


# def get_category_names_list(category_ids: list) -> list:
#     return [get_category_name(cid) for cid in category_ids]


# def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
#     df = df.copy()
#     df["category_name"] = df["categoryid"].apply(get_category_name)
#     return df


# def print_mapping_coverage(df):
#     total = len(df)
#     mapped = df["categoryid"].isin(CATEGORY_NAMES.keys()).sum()
#     coverage = mapped / total * 100
#     print(f"✅ Manual mapping coverage: {coverage:.1f}%")
#     print(f"   Remaining use hierarchical names")
#     return coverage


# # ====================== COARSE GROUPING ======================
# DETAIL_TO_PRODUCT = {
#     "Electronics & Gadgets": "tech", "Computers & Accessories": "tech",
#     "Mobile Phones": "tech", "Laptops & Notebooks": "tech",
#     "Audio & Headphones": "tech", "Gaming & Consoles": "tech",
#     "Clothing & Apparel": "fashion", "Footwear": "fashion",
#     "Women's Fashion": "fashion", "Men's Fashion": "fashion",
#     "Kitchen & Dining": "food", "Food & Groceries": "food",
#     "Sports & Fitness": "fitness", "Fitness Equipment": "fitness",
#     "Health & Wellness": "fitness", "Garden & Outdoors": "travel",
#     "Outdoor Gear": "travel", "Office Supplies": "finance",
#     "Books & Stationery": "finance",
# }

# def to_product_category(detail_name: str, categoryid: Optional[int] = None) -> str:
#     if detail_name in DETAIL_TO_PRODUCT:
#         return DETAIL_TO_PRODUCT[detail_name]
    
#     if categoryid and categoryid in PARENT_MAP:
#         parent_name = get_category_name(PARENT_MAP[categoryid])
#         if parent_name in DETAIL_TO_PRODUCT:
#             return DETAIL_TO_PRODUCT[parent_name]
    
#     if categoryid:
#         labels = ["tech", "fashion", "food", "fitness", "travel", "finance"]
#         return labels[int(categoryid) % 6]
#     return "tech"

