# =====================================================
# Product Search & Comparison Tools
# =====================================================

import json
from langchain.tools import tool
from psycopg2.extras import RealDictCursor
from database.connection import get_db_connection


@tool
def search_products(
    query: str = None,
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    gender: str = None,
    stone_name: str = None,
) -> str:
    """
    Search products by various filters.
    Args:
        query: General search term
        category: Category name (e.g., 'Aqeeq Rings', 'Tasbih')
        min_price: Minimum price in USD
        max_price: Maximum price in USD
        gender: 'men', 'women', or 'both'
        stone_name: Specific gemstone name
    Returns: JSON string of matching products
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    sql = """
        SELECT DISTINCT p.product_id, p.name, p.description, p.price_usd, 
               p.gender, p.occasion, p.stock, p.is_sunnah_design,
               c.name as category, m.name as material,
               array_agg(s.name) as stones
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN materials m ON p.material_id = m.material_id
        LEFT JOIN product_stones ps ON p.product_id = ps.product_id
        LEFT JOIN stones s ON ps.stone_id = s.stone_id
        WHERE 1=1
    """

    params = []
    if query:
        sql += " AND (p.name ILIKE %s OR p.description ILIKE %s)"
        params.extend([f"%{query}%", f"%{query}%"])
    if category:
        sql += " AND c.name ILIKE %s"
        params.append(f"%{category}%")
    if min_price:
        sql += " AND p.price_usd >= %s"
        params.append(min_price)
    if max_price:
        sql += " AND p.price_usd <= %s"
        params.append(max_price)
    if gender:
        sql += " AND (p.gender = %s OR p.gender = 'both')"
        params.append(gender)
    if stone_name:
        sql += " AND s.name ILIKE %s"
        params.append(f"%{stone_name}%")

    sql += " GROUP BY p.product_id, c.name, m.name LIMIT 10"

    cur.execute(sql, params)
    results = cur.fetchall()
    cur.close()
    conn.close()

    return json.dumps([dict(row) for row in results], default=str)


@tool
def compare_products(product_ids: str) -> str:
    """
    Compare multiple products side by side.
    Args:
        product_ids: Comma-separated product IDs (e.g., "1,2,3")
    Returns: Comparison data
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    ids = [int(id.strip()) for id in product_ids.split(",")]

    cur.execute(
        """
        SELECT p.product_id, p.name, p.price_usd, p.description,
               c.name as category, m.name as material,
               p.stock, p.is_sunnah_design, p.story_behind
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN materials m ON p.material_id = m.material_id
        WHERE p.product_id = ANY(%s)
    """,
        (ids,),
    )

    results = cur.fetchall()
    cur.close()
    conn.close()

    return json.dumps([dict(row) for row in results], default=str)
