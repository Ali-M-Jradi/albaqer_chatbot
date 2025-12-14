# =====================================================
# Stone Information Tools
# =====================================================

import json
from langchain.tools import tool
from psycopg2.extras import RealDictCursor
from database.connection import get_db_connection


@tool
def get_stone_info(stone_name: str) -> str:
    """
    Get detailed information about a gemstone including Islamic significance.
    Args:
        stone_name: Name of the stone (e.g., 'Aqeeq', 'Turquoise')
    Returns: JSON string with stone details
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT stone_id, name, color, arabic_name, 
               islamic_significance, cultural_significance,
               healing_properties, historical_facts,
               hardness, meaning, sunnah_stone, recommended_for
        FROM stones 
        WHERE name ILIKE %s
        LIMIT 1
    """,
        (f"%{stone_name}%",),
    )

    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        return json.dumps(dict(result), default=str)
    return json.dumps({"error": "Stone not found"})
