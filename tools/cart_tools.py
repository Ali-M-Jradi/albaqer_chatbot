# =====================================================
# Cart Management Tools - NEW
# =====================================================

import json
from langchain.tools import tool
from psycopg2.extras import RealDictCursor
from database.connection import get_db_connection


@tool
def add_to_cart(user_id: int, product_id: int, quantity: int = 1) -> str:
    """
    Add a product to user's shopping cart.
    Args:
        user_id: User ID
        product_id: Product ID to add
        quantity: Quantity to add (default: 1)
    Returns: Success message with cart summary
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Check if product exists and is available
        cur.execute(
            """
            SELECT id, name, base_price, quantity_in_stock, is_available
            FROM products WHERE id = %s
        """,
            (product_id,),
        )

        product = cur.fetchone()

        if not product:
            return json.dumps({"error": "Product not found", "success": False})

        if not product["is_available"] or product["quantity_in_stock"] < quantity:
            return json.dumps(
                {
                    "error": "Product not available in requested quantity",
                    "success": False,
                    "available_quantity": product["quantity_in_stock"],
                }
            )

        # Get or create cart for user
        cur.execute(
            """
            SELECT id FROM carts WHERE user_id = %s LIMIT 1
        """,
            (user_id,),
        )

        cart = cur.fetchone()

        if not cart:
            # Create new cart
            cur.execute(
                """
                INSERT INTO carts (user_id, created_at, updated_at)
                VALUES (%s, NOW(), NOW())
                RETURNING id
            """,
                (user_id,),
            )
            cart_id = cur.fetchone()["id"]
        else:
            cart_id = cart["id"]

        # Check if item already in cart
        cur.execute(
            """
            SELECT id, quantity FROM cart_items
            WHERE cart_id = %s AND product_id = %s
        """,
            (cart_id, product_id),
        )

        existing_item = cur.fetchone()

        if existing_item:
            # Update quantity
            new_quantity = existing_item["quantity"] + quantity
            cur.execute(
                """
                UPDATE cart_items
                SET quantity = %s
                WHERE id = %s
            """,
                (new_quantity, existing_item["id"]),
            )
            message = f"Updated quantity to {new_quantity}"
        else:
            # Add new item
            cur.execute(
                """
                INSERT INTO cart_items (cart_id, product_id, quantity, price_at_add)
                VALUES (%s, %s, %s, %s)
            """,
                (cart_id, product_id, quantity, product["base_price"]),
            )
            message = f"Added {quantity} item(s) to cart"

        # Update cart timestamp
        cur.execute(
            """
            UPDATE carts SET updated_at = NOW() WHERE id = %s
        """,
            (cart_id,),
        )

        # Get cart summary
        cur.execute(
            """
            SELECT COUNT(*) as item_count,
                   SUM(ci.quantity * p.base_price) as total
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.cart_id = %s
        """,
            (cart_id,),
        )

        summary = cur.fetchone()

        conn.commit()
        cur.close()
        conn.close()

        return json.dumps(
            {
                "success": True,
                "message": message,
                "product_name": product["name"],
                "cart_items": summary["item_count"],
                "cart_total": float(summary["total"]),
            }
        )

    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return json.dumps({"error": str(e), "success": False})


@tool
def view_cart(user_id: int) -> str:
    """
    View all items in user's shopping cart with details.
    Args:
        user_id: User ID
    Returns: List of cart items with product details and total price
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Get cart
        cur.execute(
            """
            SELECT id FROM carts WHERE user_id = %s LIMIT 1
        """,
            (user_id,),
        )

        cart = cur.fetchone()

        if not cart:
            return json.dumps(
                {
                    "empty": True,
                    "message": "Your cart is empty",
                    "items": [],
                    "total": 0,
                }
            )

        # Get cart items
        cur.execute(
            """
            SELECT 
                ci.id as cart_item_id,
                ci.quantity,
                ci.price_at_add,
                p.id as product_id,
                p.name,
                p.type,
                p.base_price as current_price,
                p.stone_type,
                p.metal_type,
                p.quantity_in_stock,
                p.is_available,
                p.image_url,
                (ci.quantity * ci.price_at_add) as subtotal
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.cart_id = %s
            ORDER BY ci.id DESC
        """,
            (cart["id"],),
        )

        items = cur.fetchall()
        cur.close()
        conn.close()

        if not items:
            return json.dumps(
                {
                    "empty": True,
                    "message": "Your cart is empty",
                    "items": [],
                    "total": 0,
                }
            )

        cart_data = [dict(item) for item in items]
        total = sum(item["subtotal"] for item in items)

        return json.dumps(
            {
                "empty": False,
                "items": cart_data,
                "item_count": len(cart_data),
                "total_items": sum(item["quantity"] for item in items),
                "total": float(total),
            },
            default=str,
        )

    except Exception as e:
        cur.close()
        conn.close()
        return json.dumps({"error": str(e)})


@tool
def remove_from_cart(user_id: int, product_id: int) -> str:
    """
    Remove a product from user's cart.
    Args:
        user_id: User ID
        product_id: Product ID to remove
    Returns: Success message
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Get cart
        cur.execute(
            """
            SELECT id FROM carts WHERE user_id = %s LIMIT 1
        """,
            (user_id,),
        )

        cart = cur.fetchone()

        if not cart:
            return json.dumps({"error": "Cart not found", "success": False})

        # Remove item
        cur.execute(
            """
            DELETE FROM cart_items
            WHERE cart_id = %s AND product_id = %s
            RETURNING id
        """,
            (cart["id"], product_id),
        )

        deleted = cur.fetchone()

        if not deleted:
            conn.rollback()
            return json.dumps({"error": "Item not in cart", "success": False})

        # Update cart timestamp
        cur.execute(
            """
            UPDATE carts SET updated_at = NOW() WHERE id = %s
        """,
            (cart["id"],),
        )

        conn.commit()
        cur.close()
        conn.close()

        return json.dumps({"success": True, "message": "Item removed from cart"})

    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return json.dumps({"error": str(e), "success": False})
