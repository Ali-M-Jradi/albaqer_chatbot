# =====================================================
# Order Management Tools - NEW
# =====================================================

import json
from langchain.tools import tool
from psycopg2.extras import RealDictCursor
from database.connection import get_db_connection


@tool
def get_order_history(user_id: int, limit: int = 10) -> str:
    """
    Get user's order history.
    Args:
        user_id: User ID
        limit: Maximum number of orders to return (default: 10)
    Returns: List of past orders with details
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            SELECT 
                o.id as order_id,
                o.total_amount,
                o.status,
                o.shipping_address,
                o.created_at as order_date,
                o.updated_at as last_updated,
                COUNT(oi.id) as item_count
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.user_id = %s
            GROUP BY o.id
            ORDER BY o.created_at DESC
            LIMIT %s
        """,
            (user_id, limit),
        )

        orders = cur.fetchall()
        cur.close()
        conn.close()

        if not orders:
            return json.dumps({"message": "No orders found", "orders": []})

        return json.dumps(
            {"order_count": len(orders), "orders": [dict(order) for order in orders]},
            default=str,
        )

    except Exception as e:
        cur.close()
        conn.close()
        return json.dumps({"error": str(e)})


@tool
def get_order_details(order_id: int, user_id: int) -> str:
    """
    Get detailed information about a specific order.
    Args:
        order_id: Order ID
        user_id: User ID (for security check)
    Returns: Detailed order information including items
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Get order header
        cur.execute(
            """
            SELECT 
                o.id,
                o.total_amount,
                o.status,
                o.shipping_address,
                o.created_at,
                o.updated_at
            FROM orders o
            WHERE o.id = %s AND o.user_id = %s
        """,
            (order_id, user_id),
        )

        order = cur.fetchone()

        if not order:
            return json.dumps({"error": "Order not found or access denied"})

        # Get order items
        cur.execute(
            """
            SELECT 
                oi.id,
                oi.quantity,
                oi.price_at_time,
                p.name,
                p.type,
                p.stone_type,
                p.metal_type,
                p.image_url,
                (oi.quantity * oi.price_at_time) as subtotal
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """,
            (order_id,),
        )

        items = cur.fetchall()
        cur.close()
        conn.close()

        order_dict = dict(order)
        order_dict["items"] = [dict(item) for item in items]
        order_dict["item_count"] = len(items)

        return json.dumps(order_dict, default=str)

    except Exception as e:
        cur.close()
        conn.close()
        return json.dumps({"error": str(e)})


@tool
def track_order_status(order_id: int, user_id: int) -> str:
    """
    Track the current status of an order.
    Args:
        order_id: Order ID
        user_id: User ID (for security check)
    Returns: Current order status and estimated delivery
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            SELECT 
                o.id,
                o.status,
                o.created_at,
                o.updated_at,
                o.shipping_address,
                COUNT(oi.id) as item_count,
                o.total_amount
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.id = %s AND o.user_id = %s
            GROUP BY o.id
        """,
            (order_id, user_id),
        )

        order = cur.fetchone()
        cur.close()
        conn.close()

        if not order:
            return json.dumps({"error": "Order not found or access denied"})

        # Status messages
        status_messages = {
            "pending": "Your order is being processed",
            "processing": "Your order is being prepared",
            "shipped": "Your order has been shipped!",
            "delivered": "Your order has been delivered",
            "cancelled": "This order has been cancelled",
        }

        result = dict(order)
        result["status_message"] = status_messages.get(
            order["status"].lower(), "Status update pending"
        )

        return json.dumps(result, default=str)

    except Exception as e:
        cur.close()
        conn.close()
        return json.dumps({"error": str(e)})
