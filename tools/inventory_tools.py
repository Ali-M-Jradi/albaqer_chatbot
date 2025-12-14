# =====================================================
# Inventory Tools
# =====================================================

import json
from langchain.tools import tool
from psycopg2.extras import RealDictCursor
from database.connection import get_db_connection


@tool
def check_stock(product_id: int) -> str:
    """
    Check product stock availability.
    Args:
        product_id: Product ID
    Returns: Stock information
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT product_id, name, stock, price_usd
        FROM products
        WHERE product_id = %s
    """,
        (product_id,),
    )

    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        status = (
            "In Stock"
            if result["stock"] > 5
            else "Low Stock" if result["stock"] > 0 else "Out of Stock"
        )
        return json.dumps(
            {
                "product_id": result["product_id"],
                "name": result["name"],
                "stock": result["stock"],
                "status": status,
                "price_usd": float(result["price_usd"]),
            }
        )
    return json.dumps({"error": "Product not found"})
