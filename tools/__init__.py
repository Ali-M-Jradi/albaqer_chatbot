# Tools module for AlBaqer Stones agents - UPDATED
from .product_tools import search_products, compare_products
from .stone_tools import get_stone_info
from .inventory_tools import check_stock
from .cart_tools import add_to_cart, view_cart, remove_from_cart
from .order_tools import get_order_history, get_order_details, track_order_status
from .review_tools import (
    get_product_reviews,
    get_top_rated_products,
    get_review_summary,
)

__all__ = [
    # Product tools
    "search_products",
    "compare_products",
    # Stone tools
    "get_stone_info",
    # Inventory tools
    "check_stock",
    # Cart tools (NEW)
    "add_to_cart",
    "view_cart",
    "remove_from_cart",
    # Order tools (NEW)
    "get_order_history",
    "get_order_details",
    "track_order_status",
    # Review tools (NEW)
    "get_product_reviews",
    "get_top_rated_products",
    "get_review_summary",
]
