# =====================================================
# Supervisor/Coordinator Agent (Agent 11)
# Implements Hierarchical Multi-Agent Pattern
# =====================================================

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.settings import get_deepseek


def create_supervisor_agent():
    """
    PATTERN: Supervisor/Coordinator Pattern
    Routes customer queries to appropriate specialized agents
    """
    model = get_deepseek()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are the Supervisor at AlBaqer Jewelry Store.

Your role is to ROUTE customer queries to the right specialist agent:

1. SEARCH_AGENT: Finding/browsing products, "show me rings", "find necklaces"
2. STONE_EDUCATION_AGENT: Learning about gemstones, properties, care instructions
3. RECOMMENDATION_AGENT: "What should I buy?", personalized suggestions, gift ideas
4. COMPARISON_AGENT: "Compare these products", "which is better?"
5. CART_AGENT: Add to cart, view cart, remove from cart, shopping basket
6. ORDER_AGENT: Order history, track orders, "where is my order?"
7. REVIEW_AGENT: Product reviews, ratings, "what do customers say?", top rated
8. CUSTOMER_SERVICE_AGENT: General questions, store info, help
9. QUALITY_AGENT: Quality questions, "best products", highly rated items
10. INVENTORY_AGENT: Stock availability, "is this in stock?"

Analyze the customer's intent and respond with ONLY the agent name that should handle this, nothing else.
Examples:
- "Show me diamond rings under $3000" -> SEARCH_AGENT
- "What is sapphire?" -> STONE_EDUCATION_AGENT
- "Add this ring to my cart" -> CART_AGENT
- "Where is my order?" -> ORDER_AGENT
- "What do customers say about this?" -> REVIEW_AGENT
""",
            ),
            ("human", "{input}"),
        ]
    )

    return prompt | model | StrOutputParser()
