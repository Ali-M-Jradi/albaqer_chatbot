# Agents module for AlBaqer Stones
from .specialized_agents import (
    create_search_agent,
    create_knowledge_agent,
    create_recommendation_agent,
    create_comparison_agent,
    create_pricing_agent,
    create_delivery_agent,
    create_payment_agent,
    create_customer_service_agent,
    create_cultural_agent,
    create_inventory_agent,
)
from .supervisor import create_supervisor_agent

__all__ = [
    "create_search_agent",
    "create_knowledge_agent",
    "create_recommendation_agent",
    "create_comparison_agent",
    "create_pricing_agent",
    "create_delivery_agent",
    "create_payment_agent",
    "create_customer_service_agent",
    "create_cultural_agent",
    "create_inventory_agent",
    "create_supervisor_agent",
]

# Complete agent dictionary
ALL_AGENTS = {
    "SEARCH_AGENT": create_search_agent,
    "KNOWLEDGE_AGENT": create_knowledge_agent,
    "RECOMMENDATION_AGENT": create_recommendation_agent,
    "COMPARISON_AGENT": create_comparison_agent,
    "PRICING_AGENT": create_pricing_agent,
    "DELIVERY_AGENT": create_delivery_agent,
    "PAYMENT_AGENT": create_payment_agent,
    "CUSTOMER_SERVICE_AGENT": create_customer_service_agent,
    "CULTURAL_AGENT": create_cultural_agent,
    "INVENTORY_AGENT": create_inventory_agent,
    "SUPERVISOR_AGENT": create_supervisor_agent,
}
