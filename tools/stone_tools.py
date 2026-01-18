# =====================================================
# Stone Information Tools - UPDATED FOR E-COMMERCE DB
# =====================================================

import json
from langchain.tools import tool
from psycopg2.extras import RealDictCursor
from database.connection import get_db_connection


# Gemstone knowledge database (since stones table doesn't exist)
STONE_KNOWLEDGE = {
    "Diamond": {
        "name": "Diamond",
        "color": "Clear/Various",
        "hardness": "10 (Mohs scale)",
        "meaning": "Eternal love, strength, clarity",
        "healing_properties": "Amplifies energy, enhances clarity, promotes courage",
        "care": "Clean with mild soap and water, avoid harsh chemicals",
        "facts": "Hardest natural material, formed deep in Earth's mantle",
    },
    "Ruby": {
        "name": "Ruby",
        "color": "Red/Pink",
        "hardness": "9 (Mohs scale)",
        "meaning": "Passion, protection, prosperity",
        "healing_properties": "Vitality, confidence, protection from negative energy",
        "care": "Clean with warm soapy water, avoid extreme temperature changes",
        "facts": "Variety of corundum, color comes from chromium",
    },
    "Sapphire": {
        "name": "Sapphire",
        "color": "Blue/Various",
        "hardness": "9 (Mohs scale)",
        "meaning": "Wisdom, loyalty, nobility",
        "healing_properties": "Mental clarity, spiritual insight, calming properties",
        "care": "Clean with warm water and mild detergent, very durable",
        "facts": "Same mineral as ruby (corundum), blue from titanium and iron",
    },
    "Emerald": {
        "name": "Emerald",
        "color": "Green",
        "hardness": "7.5-8 (Mohs scale)",
        "meaning": "Growth, renewal, love",
        "healing_properties": "Emotional balance, enhances memory, promotes harmony",
        "care": "Clean gently, avoid ultrasonic cleaners, sensitive to heat",
        "facts": "Variety of beryl, colored by chromium and vanadium",
    },
    "Amethyst": {
        "name": "Amethyst",
        "color": "Purple",
        "hardness": "7 (Mohs scale)",
        "meaning": "Peace, spiritual growth, protection",
        "healing_properties": "Calming, aids meditation, relieves stress",
        "care": "Clean with warm water, avoid prolonged sun exposure (may fade)",
        "facts": "Variety of quartz, color from iron and irradiation",
    },
    "Pearl": {
        "name": "Pearl",
        "color": "White/Cream/Various",
        "hardness": "2.5-4.5 (Mohs scale)",
        "meaning": "Purity, wisdom, integrity",
        "healing_properties": "Calming, balancing, promotes sincerity",
        "care": "Very delicate, wipe with soft cloth, avoid chemicals and perfumes",
        "facts": "Organic gem formed in mollusks, composed of nacre",
    },
    "Topaz": {
        "name": "Topaz",
        "color": "Blue/Yellow/Pink/Clear",
        "hardness": "8 (Mohs scale)",
        "meaning": "Joy, generosity, abundance",
        "healing_properties": "Promotes confidence, relieves tension, aids manifestation",
        "care": "Clean with warm soapy water, avoid sudden temperature changes",
        "facts": "November birthstone, name possibly from Sanskrit 'tapas' (fire)",
    },
}


@tool
def get_stone_info(stone_name: str) -> str:
    """
    Get detailed information about a gemstone including properties and care instructions.
    Args:
        stone_name: Name of the stone (e.g., 'Diamond', 'Ruby', 'Sapphire')
    Returns: JSON string with stone details including care instructions
    """
    # First check if we have this stone in our knowledge base
    stone_name_normalized = stone_name.strip().title()

    if stone_name_normalized in STONE_KNOWLEDGE:
        stone_info = STONE_KNOWLEDGE[stone_name_normalized].copy()

        # Get products with this stone from database
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT 
                COUNT(*) as product_count,
                AVG(base_price) as avg_price,
                MIN(base_price) as min_price,
                MAX(base_price) as max_price,
                STRING_AGG(DISTINCT stone_color, ', ') as available_colors
            FROM products
            WHERE stone_type ILIKE %s
        """,
            (f"%{stone_name}%",),
        )

        availability = cur.fetchone()
        cur.close()
        conn.close()

        if availability and availability["product_count"] > 0:
            stone_info["available_in_store"] = True
            stone_info["product_count"] = availability["product_count"]
            stone_info["price_range"] = (
                f"${availability['min_price']:.2f} - ${availability['max_price']:.2f}"
            )
            stone_info["avg_price"] = f"${availability['avg_price']:.2f}"
            if availability["available_colors"]:
                stone_info["colors_in_stock"] = availability["available_colors"]
        else:
            stone_info["available_in_store"] = False
            stone_info["message"] = (
                "This stone is not currently available in our inventory"
            )

        return json.dumps(stone_info, default=str)

    else:
        # Stone not in knowledge base - check if we have it in products
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT DISTINCT 
                stone_type, 
                stone_color,
                stone_cut,
                COUNT(*) as count
            FROM products
            WHERE stone_type ILIKE %s
            GROUP BY stone_type, stone_color, stone_cut
            LIMIT 5
        """,
            (f"%{stone_name}%",),
        )

        results = cur.fetchall()
        cur.close()
        conn.close()

        if results:
            return json.dumps(
                {
                    "stone_name": stone_name,
                    "found_in_products": True,
                    "variations": [dict(r) for r in results],
                    "message": "Stone found in our inventory but detailed information not available yet",
                }
            )
        else:
            return json.dumps(
                {
                    "stone_name": stone_name,
                    "found": False,
                    "message": f"Stone '{stone_name}' not found in our knowledge base or inventory",
                }
            )
