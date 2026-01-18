# =====================================================
# Product Search & Comparison Tools - UPDATED FOR E-COMMERCE DB
# =====================================================

import json
from langchain.tools import tool
from psycopg2.extras import RealDictCursor
from database.connection import get_db_connection


@tool
def search_products(
    query: str = None,
    product_type: str = None,
    min_price: float = None,
    max_price: float = None,
    stone_type: str = None,
    metal_type: str = None,
    metal_color: str = None,
    min_rating: float = None,
) -> str:
    """
    Search products by various filters.
    Args:
        query: General search term (searches name and description)
        product_type: Type of product (e.g., 'ring', 'necklace', 'bracelet', 'earrings')
        min_price: Minimum price in USD
        max_price: Maximum price in USD
        stone_type: Gemstone type (e.g., 'Diamond', 'Ruby', 'Sapphire', 'Emerald')
        metal_type: Metal type (e.g., 'Gold', 'Silver', 'Platinum')
        metal_color: Metal color (e.g., 'Yellow', 'White', 'Rose')
        min_rating: Minimum customer rating (0-5)
    Returns: JSON string of matching products
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    sql = """
        SELECT 
            p.id,
            p.name,
            p.type,
            p.description,
            p.base_price,
            p.rating,
            p.total_reviews,
            p.quantity_in_stock,
            p.is_available,
            p.stone_type,
            p.stone_color,
            p.stone_carat,
            p.stone_cut,
            p.stone_clarity,
            p.metal_type,
            p.metal_color,
            p.metal_purity,
            p.metal_weight_grams,
            p.image_url
        FROM products p
        WHERE p.is_available = true
    """

    params = []

    if query:
        sql += " AND (p.name ILIKE %s OR p.description ILIKE %s)"
        params.extend([f"%{query}%", f"%{query}%"])

    if product_type:
        sql += " AND p.type ILIKE %s"
        params.append(f"%{product_type}%")

    if min_price:
        sql += " AND p.base_price >= %s"
        params.append(min_price)

    if max_price:
        sql += " AND p.base_price <= %s"
        params.append(max_price)

    if stone_type:
        sql += " AND p.stone_type ILIKE %s"
        params.append(f"%{stone_type}%")

    if metal_type:
        sql += " AND p.metal_type ILIKE %s"
        params.append(f"%{metal_type}%")

    if metal_color:
        sql += " AND p.metal_color ILIKE %s"
        params.append(f"%{metal_color}%")

    if min_rating:
        sql += " AND p.rating >= %s"
        params.append(min_rating)

    sql += " ORDER BY p.rating DESC, p.base_price ASC LIMIT 10"

    cur.execute(sql, params)
    results = cur.fetchall()
    cur.close()
    conn.close()

    if not results:
        return json.dumps(
            {"message": "No products found matching your criteria", "products": []}
        )

    return json.dumps([dict(row) for row in results], default=str)


@tool
def compare_products(product_ids: str) -> str:
    """
    Compare multiple products side by side.
    Args:
        product_ids: Comma-separated product IDs (e.g., "1,2,3")
    Returns: Comparison data with detailed product information
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    ids = [int(id.strip()) for id in product_ids.split(",")]

    cur.execute(
        """
        SELECT 
            p.id,
            p.name,
            p.type,
            p.description,
            p.base_price,
            p.rating,
            p.total_reviews,
            p.quantity_in_stock,
            p.stone_type,
            p.stone_color,
            p.stone_carat,
            p.stone_cut,
            p.stone_clarity,
            p.metal_type,
            p.metal_color,
            p.metal_purity,
            p.metal_weight_grams,
            p.image_url
        FROM products p
        WHERE p.id = ANY(%s)
        ORDER BY p.base_price ASC
    """,
        (ids,),
    )

    results = cur.fetchall()
    cur.close()
    conn.close()

    if not results:
        return json.dumps({"error": "No products found with provided IDs"})

    return json.dumps([dict(row) for row in results], default=str)
