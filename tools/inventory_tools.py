# =====================================================
# Inventory Tools - UPDATED FOR E-COMMERCE DB
# =====================================================

import json
from langchain.tools import tool
from psycopg2.extras import RealDictCursor
from database.connection import get_db_connection


@tool
def check_stock(product_id: int) -> str:
    """
    Check product stock availability and get detailed product information.
    Args:
        product_id: Product ID
    Returns: Stock information with availability status and product details
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT 
            id,
            name,
            type,
            quantity_in_stock,
            is_available,
            base_price,
            rating,
            total_reviews,
            stone_type,
            metal_type,
            image_url
        FROM products
        WHERE id = %s
    """,
        (product_id,),
    )

    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        stock_qty = result["quantity_in_stock"]
        is_available = result["is_available"]

        # Determine stock status
        if not is_available or stock_qty == 0:
            status = "Out of Stock"
        elif stock_qty <= 2:
            status = "Low Stock - Only {} left!".format(stock_qty)
        elif stock_qty <= 5:
            status = "Limited Stock Available"
        else:
            status = "In Stock"

        return json.dumps(
            {
                "product_id": result["id"],
                "name": result["name"],
                "type": result["type"],
                "quantity_in_stock": stock_qty,
                "is_available": is_available,
                "stock_status": status,
                "price": float(result["base_price"]),
                "rating": float(result["rating"]) if result["rating"] else None,
                "total_reviews": result["total_reviews"],
                "stone_type": result["stone_type"],
                "metal_type": result["metal_type"],
                "can_order": is_available and stock_qty > 0,
            }
        )
    return json.dumps({"error": "Product not found", "product_id": product_id})
