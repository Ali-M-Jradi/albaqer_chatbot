# =====================================================
# Review & Rating Tools - NEW
# =====================================================

import json
from langchain.tools import tool
from psycopg2.extras import RealDictCursor
from database.connection import get_db_connection


@tool
def get_product_reviews(product_id: int, limit: int = 5) -> str:
    """
    Get customer reviews for a specific product.
    Args:
        product_id: Product ID
        limit: Maximum number of reviews to return (default: 5)
    Returns: List of customer reviews with ratings
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # First get product info and overall rating
        cur.execute(
            """
            SELECT 
                p.id,
                p.name,
                p.rating,
                p.total_reviews
            FROM products p
            WHERE p.id = %s
        """,
            (product_id,),
        )

        product = cur.fetchone()

        if not product:
            return json.dumps({"error": "Product not found"})

        # Get reviews
        cur.execute(
            """
            SELECT 
                r.id,
                r.rating,
                r.comment,
                r.created_at,
                u.username
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.product_id = %s
            ORDER BY r.created_at DESC
            LIMIT %s
        """,
            (product_id, limit),
        )

        reviews = cur.fetchall()
        cur.close()
        conn.close()

        result = {
            "product_id": product["id"],
            "product_name": product["name"],
            "overall_rating": float(product["rating"]) if product["rating"] else 0,
            "total_reviews": product["total_reviews"],
            "reviews": [dict(review) for review in reviews],
        }

        return json.dumps(result, default=str)

    except Exception as e:
        cur.close()
        conn.close()
        return json.dumps({"error": str(e)})


@tool
def get_top_rated_products(product_type: str = None, limit: int = 10) -> str:
    """
    Get highest rated products.
    Args:
        product_type: Filter by product type (e.g., 'ring', 'necklace') - optional
        limit: Maximum number of products to return (default: 10)
    Returns: List of top-rated products
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        sql = """
            SELECT 
                p.id,
                p.name,
                p.type,
                p.base_price,
                p.rating,
                p.total_reviews,
                p.stone_type,
                p.metal_type,
                p.image_url,
                p.quantity_in_stock
            FROM products p
            WHERE p.is_available = true
            AND p.rating IS NOT NULL
            AND p.total_reviews > 0
        """

        params = []

        if product_type:
            sql += " AND p.type ILIKE %s"
            params.append(f"%{product_type}%")

        sql += " ORDER BY p.rating DESC, p.total_reviews DESC LIMIT %s"
        params.append(limit)

        cur.execute(sql, params)
        products = cur.fetchall()
        cur.close()
        conn.close()

        return json.dumps(
            {
                "count": len(products),
                "products": [dict(product) for product in products],
            },
            default=str,
        )

    except Exception as e:
        cur.close()
        conn.close()
        return json.dumps({"error": str(e)})


@tool
def get_review_summary(product_id: int) -> str:
    """
    Get summarized review statistics for a product.
    Args:
        product_id: Product ID
    Returns: Review statistics including rating distribution
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Get rating distribution
        cur.execute(
            """
            SELECT 
                rating,
                COUNT(*) as count
            FROM reviews
            WHERE product_id = %s
            GROUP BY rating
            ORDER BY rating DESC
        """,
            (product_id,),
        )

        distribution = cur.fetchall()

        # Get overall stats
        cur.execute(
            """
            SELECT 
                p.name,
                p.rating as avg_rating,
                p.total_reviews,
                COUNT(CASE WHEN r.rating >= 4 THEN 1 END) as positive_reviews,
                COUNT(CASE WHEN r.rating <= 2 THEN 1 END) as negative_reviews
            FROM products p
            LEFT JOIN reviews r ON p.id = r.product_id
            WHERE p.id = %s
            GROUP BY p.id, p.name, p.rating, p.total_reviews
        """,
            (product_id,),
        )

        summary = cur.fetchone()
        cur.close()
        conn.close()

        if not summary:
            return json.dumps({"error": "Product not found"})

        result = dict(summary)
        result["rating_distribution"] = [dict(d) for d in distribution]
        result["positive_percentage"] = (
            (summary["positive_reviews"] / summary["total_reviews"] * 100)
            if summary["total_reviews"] > 0
            else 0
        )

        return json.dumps(result, default=str)

    except Exception as e:
        cur.close()
        conn.close()
        return json.dumps({"error": str(e)})
