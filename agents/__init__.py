# Agents module for AlBaqer Stones
from .specialized_agents import (
    create_search_agent,
    create_stone_education_agent,
    create_recommendation_agent,
    create_comparison_agent,
    create_cart_agent,
    create_order_agent,
    create_review_agent,
    create_customer_service_agent,
    create_quality_agent,
    create_inventory_agent,
)
from .supervisor import create_supervisor_agent

__all__ = [
    "create_search_agent",
    "create_stone_education_agent",
    "create_recommendation_agent",
    "create_comparison_agent",
    "create_cart_agent",
    "create_order_agent",
    "create_review_agent",
    "create_customer_service_agent",
    "create_quality_agent",
    "create_inventory_agent",
    "create_supervisor_agent",
]

# Complete agent dictionary
ALL_AGENTS = {
    "SEARCH_AGENT": create_search_agent,
    "STONE_EDUCATION_AGENT": create_stone_education_agent,
    "RECOMMENDATION_AGENT": create_recommendation_agent,
    "COMPARISON_AGENT": create_comparison_agent,
    "CART_AGENT": create_cart_agent,
    "ORDER_AGENT": create_order_agent,
    "REVIEW_AGENT": create_review_agent,
    "CUSTOMER_SERVICE_AGENT": create_customer_service_agent,
    "QUALITY_AGENT": create_quality_agent,
    "INVENTORY_AGENT": create_inventory_agent,
    "SUPERVISOR_AGENT": create_supervisor_agent,
}
