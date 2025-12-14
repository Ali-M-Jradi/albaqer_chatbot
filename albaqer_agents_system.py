# =====================================================
# AlBaqer Islamic Gemstone Store - Multi-Agent System
# 10+ Agents with RAG, Database Integration, Multi-Agent Patterns
# =====================================================

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import List, Dict, Any, Optional
import json

# Import semantic RAG
from vector_rag_system import semantic_search, rag_query, get_rag_context

load_dotenv()


# =====================================================
# DATABASE CONNECTION
# =====================================================
def get_db_connection():
    """Create and return a database connection"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "albaqer_stones_store"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "your_password"),
    )


# =====================================================
# LLM MODELS
# =====================================================
def get_deepseek():
    """Returns DeepSeek model for complex reasoning"""
    return ChatOpenAI(
        model="deepseek-chat",
        max_tokens=1500,
        timeout=30,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"),
    )


def get_gemini():
    """Returns Gemini model with fallback to DeepSeek"""
    try:
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",  # Use latest stable version
            api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.7,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )
    except Exception as e:
        print(f"⚠️ Gemini unavailable: {str(e)[:100]}... Falling back to DeepSeek")
        return get_deepseek()


# =====================================================
# MIDDLEWARE: Dynamic Model Selection (Pattern 1)
# =====================================================
@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    """
    PATTERN: Dynamic routing based on query complexity
    Simple queries -> Gemini (fast, cheap)
    Complex queries -> DeepSeek (powerful, accurate)
    """
    message_count = len(request.state["messages"])
    last_message = str(request.state["messages"][-1]) if message_count > 0 else ""

    # Complex query indicators
    complex_keywords = [
        "compare",
        "recommend",
        "best",
        "difference",
        "analyze",
        "explain",
    ]
    is_complex = any(keyword in last_message.lower() for keyword in complex_keywords)

    if is_complex or message_count > 5:
        request.model = get_deepseek()
    else:
        request.model = get_gemini()

    return handler(request)


# =====================================================
# DATABASE TOOLS - For All Agents
# =====================================================
@tool
def search_products(
    query: str = None,
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    gender: str = None,
    stone_name: str = None,
) -> str:
    """
    Search products by various filters.
    Args:
        query: General search term
        category: Category name (e.g., 'Aqeeq Rings', 'Tasbih')
        min_price: Minimum price in USD
        max_price: Maximum price in USD
        gender: 'men', 'women', or 'both'
        stone_name: Specific gemstone name
    Returns: JSON string of matching products
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    sql = """
        SELECT DISTINCT p.product_id, p.name, p.description, p.price_usd, 
               p.gender, p.occasion, p.stock, p.is_sunnah_design,
               c.name as category, m.name as material,
               array_agg(s.name) as stones
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN materials m ON p.material_id = m.material_id
        LEFT JOIN product_stones ps ON p.product_id = ps.product_id
        LEFT JOIN stones s ON ps.stone_id = s.stone_id
        WHERE 1=1
    """

    params = []
    if query:
        sql += " AND (p.name ILIKE %s OR p.description ILIKE %s)"
        params.extend([f"%{query}%", f"%{query}%"])
    if category:
        sql += " AND c.name ILIKE %s"
        params.append(f"%{category}%")
    if min_price:
        sql += " AND p.price_usd >= %s"
        params.append(min_price)
    if max_price:
        sql += " AND p.price_usd <= %s"
        params.append(max_price)
    if gender:
        sql += " AND (p.gender = %s OR p.gender = 'both')"
        params.append(gender)
    if stone_name:
        sql += " AND s.name ILIKE %s"
        params.append(f"%{stone_name}%")

    sql += " GROUP BY p.product_id, c.name, m.name LIMIT 10"

    cur.execute(sql, params)
    results = cur.fetchall()
    cur.close()
    conn.close()

    return json.dumps([dict(row) for row in results], default=str)


@tool
def get_stone_info(stone_name: str) -> str:
    """
    Get detailed information about a gemstone including Islamic significance.
    Args:
        stone_name: Name of the stone (e.g., 'Aqeeq', 'Turquoise')
    Returns: JSON string with stone details
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT stone_id, name, color, arabic_name, 
               islamic_significance, cultural_significance,
               healing_properties, historical_facts,
               hardness, meaning, sunnah_stone, recommended_for
        FROM stones 
        WHERE name ILIKE %s
        LIMIT 1
    """,
        (f"%{stone_name}%",),
    )

    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        return json.dumps(dict(result), default=str)
    return json.dumps({"error": "Stone not found"})


@tool
def get_knowledge_base(topic: str) -> str:
    """
    RAG Tool: Semantic search on knowledge base using vector embeddings.
    Args:
        topic: Topic to search (e.g., 'diamond', 'zakat', 'aqeeq care')
    Returns: Relevant knowledge base articles with semantic similarity
    """
    try:
        # Use semantic vector search
        results = semantic_search(topic, top_k=3)

        if not results:
            return json.dumps({"error": "No relevant information found"})

        # Format results for agent
        formatted = []
        for result in results:
            formatted.append(
                {
                    "title": result["title"],
                    "content": result["content"],
                    "category": result["category"],
                    "relevance_score": result["similarity_score"],
                }
            )

        return json.dumps(formatted, default=str)

    except Exception as e:
        # Fallback to database keyword search if vector search fails
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT title, content, category, target_audience
            FROM knowledge_base
            WHERE to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', %s)
               OR category ILIKE %s
               OR title ILIKE %s
            LIMIT 3
        """,
            (topic, f"%{topic}%", f"%{topic}%"),
        )

        results = cur.fetchall()
        cur.close()
        conn.close()

        return json.dumps([dict(row) for row in results], default=str)


@tool
def calculate_delivery_fee(governorate: str) -> str:
    """
    Calculate delivery fee based on Lebanese governorate.
    Args:
        governorate: Governorate name (e.g., 'Beirut', 'Mount Lebanon')
    Returns: JSON with delivery info
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT zone_name, governorate, delivery_fee_usd, 
               delivery_days, security_level, currently_delivering
        FROM delivery_zones
        WHERE governorate ILIKE %s OR zone_name ILIKE %s
        LIMIT 1
    """,
        (f"%{governorate}%", f"%{governorate}%"),
    )

    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        return json.dumps(dict(result), default=str)
    return json.dumps({"error": "Zone not found", "default_fee": 5.00})


@tool
def convert_currency(amount_usd: float, target_currency: str = "LBP") -> str:
    """
    Convert USD to Lebanese Pound or Euro using latest rates.
    Args:
        amount_usd: Amount in USD
        target_currency: 'LBP' or 'EUR'
    Returns: Converted amount with rate info
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT currency_code, rate_to_usd, official_rate, source
        FROM currency_rates
        WHERE currency_code = %s
        ORDER BY created_at DESC
        LIMIT 1
    """,
        (target_currency,),
    )

    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        converted = amount_usd * result["rate_to_usd"]
        return json.dumps(
            {
                "amount_usd": amount_usd,
                "target_currency": target_currency,
                "converted_amount": round(converted, 2),
                "exchange_rate": result["rate_to_usd"],
                "rate_type": (
                    "official" if result["official_rate"] else "parallel market"
                ),
            }
        )
    return json.dumps({"error": "Currency not found"})


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


@tool
def get_payment_methods() -> str:
    """
    Get available payment methods in Lebanon.
    Returns: List of payment methods with details
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT method_name, method_type, fee_percentage, instructions
        FROM payment_methods
        WHERE is_active = true
    """
    )

    results = cur.fetchall()
    cur.close()
    conn.close()

    return json.dumps([dict(row) for row in results], default=str)


@tool
def compare_products(product_ids: str) -> str:
    """
    Compare multiple products side by side.
    Args:
        product_ids: Comma-separated product IDs (e.g., "1,2,3")
    Returns: Comparison data
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    ids = [int(id.strip()) for id in product_ids.split(",")]

    cur.execute(
        """
        SELECT p.product_id, p.name, p.price_usd, p.description,
               c.name as category, m.name as material,
               p.stock, p.is_sunnah_design, p.story_behind
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN materials m ON p.material_id = m.material_id
        WHERE p.product_id = ANY(%s)
    """,
        (ids,),
    )

    results = cur.fetchall()
    cur.close()
    conn.close()

    return json.dumps([dict(row) for row in results], default=str)


# =====================================================
# AGENT 1: SEARCH AGENT
# =====================================================
def create_search_agent():
    """Agent specialized in finding products"""
    return create_agent(
        model=get_deepseek(),  # Use DeepSeek instead
        middleware=[],
        tools=[search_products, check_stock],
        system_prompt="""You are a product search specialist for AlBaqer Islamic Gemstone Store.
        
Your role:
- Help customers find products based on their requirements
- Use search_products tool with appropriate filters
- Mention Islamic significance when relevant (Sunnah designs, sacred stones)
- Always check stock availability
- Present results clearly with prices in USD

Be helpful, concise, and culturally sensitive.""",
    )


# =====================================================
# AGENT 2: ISLAMIC KNOWLEDGE AGENT
# =====================================================
def create_knowledge_agent():
    """Agent specialized in gemstone education and Islamic significance"""
    return create_agent(
        model=get_deepseek(),  # Use DeepSeek instead
        middleware=[],
        tools=[get_stone_info, get_knowledge_base],
        system_prompt="""You are an Islamic gemstone education expert at AlBaqer Stones.

Your role:
- Educate customers about gemstones and their significance
- Use get_stone_info for specific stone details
- Use get_knowledge_base for broader educational content
- Explain Islamic significance respectfully (hadiths, Sunnah, spiritual meanings)
- Also provide universal gemological facts for all customers
- Cite sources when mentioning Islamic traditions

Be knowledgeable, respectful, and educational.""",
    )


# =====================================================
# AGENT 3: RECOMMENDATION AGENT
# =====================================================
def create_recommendation_agent():
    """Agent specialized in personalized recommendations"""
    return create_agent(
        model=get_deepseek(),  # Uses more powerful model
        middleware=[],
        tools=[search_products, get_stone_info],
        system_prompt="""You are a personalized recommendation specialist at AlBaqer Stones.

Your role:
- Understand customer preferences (budget, occasion, gender, beliefs)
- Recommend products that match their needs
- Consider Islamic significance for Muslim customers
- Suggest universal appeal items for others
- Explain why you recommend each item

Ask clarifying questions if needed. Be personalized and thoughtful.""",
    )


# =====================================================
# AGENT 4: COMPARISON AGENT
# =====================================================
def create_comparison_agent():
    """Agent specialized in comparing products"""
    return create_agent(
        model=get_gemini(),
        middleware=[],
        tools=[compare_products, get_stone_info],
        system_prompt="""You are a product comparison specialist at AlBaqer Stones.

Your role:
- Compare products objectively
- Highlight differences in price, materials, stones, significance
- Help customers make informed decisions
- Present comparisons in clear, structured format

Use tables or bullet points. Be objective and helpful.""",
    )


# =====================================================
# AGENT 5: PRICING & CURRENCY AGENT
# =====================================================
def create_pricing_agent():
    """Agent specialized in pricing and currency conversion"""
    return create_agent(
        model=get_gemini(),
        middleware=[],
        tools=[convert_currency, search_products],
        system_prompt="""You are a pricing and currency specialist for Lebanese market.

Your role:
- Convert prices between USD, LBP, and EUR
- Explain parallel market vs official rates
- Help customers understand pricing in their preferred currency
- Warn about LBP volatility

Be clear about which rate you're using (official vs parallel).""",
    )


# =====================================================
# AGENT 6: DELIVERY & LOGISTICS AGENT
# =====================================================
def create_delivery_agent():
    """Agent specialized in delivery and logistics"""
    return create_agent(
        model=get_gemini(),
        middleware=[],
        tools=[calculate_delivery_fee],
        system_prompt="""You are a delivery and logistics specialist for Lebanon.

Your role:
- Calculate delivery fees based on location
- Provide estimated delivery times
- Inform about delivery zones and restrictions
- Handle Lebanese governorates (Beirut, Mount Lebanon, North, South, Bekaa)

Be clear about delivery times and any location-specific challenges.""",
    )


# =====================================================
# AGENT 7: PAYMENT AGENT
# =====================================================
def create_payment_agent():
    """Agent specialized in payment methods"""
    return create_agent(
        model=get_gemini(),
        middleware=[],
        tools=[get_payment_methods],
        system_prompt="""You are a payment specialist for AlBaqer Stones.

Your role:
- Explain available payment methods (Cash, OMT, Whish, Bank Transfer, Crypto)
- Guide customers through payment process
- Explain fees and requirements
- Handle Lebanese payment methods specifically

Be clear about fees and processing times.""",
    )


# =====================================================
# AGENT 8: CUSTOMER SERVICE AGENT
# =====================================================
def create_customer_service_agent():
    """General customer service agent"""
    return create_agent(
        model=get_gemini(),
        middleware=[dynamic_model_selection],
        tools=[search_products, get_payment_methods, calculate_delivery_fee],
        system_prompt="""You are a friendly customer service representative at AlBaqer Islamic Gemstone Store.

Your role:
- Answer general inquiries
- Help with order process
- Handle complaints gracefully
- Provide store information
- Route complex questions to specialized agents

Be friendly, professional, and helpful.""",
    )


# =====================================================
# AGENT 9: CULTURAL ADVISOR AGENT
# =====================================================
def create_cultural_agent():
    """Agent for cultural guidance and Islamic traditions"""
    return create_agent(
        model=get_gemini(),
        middleware=[],
        tools=[get_stone_info, get_knowledge_base],
        system_prompt="""You are a cultural advisor specializing in Islamic jewelry traditions.

Your role:
- Advise on culturally appropriate choices
- Explain men's vs women's jewelry in Islam (gold prohibition for men)
- Guide on occasions (Eid, Ramadan, Hajj gifts)
- Respect diverse customer backgrounds
- Explain Zakat on gold/silver when relevant

Be respectful, knowledgeable, and inclusive.""",
    )


# =====================================================
# AGENT 10: INVENTORY MANAGER AGENT
# =====================================================
def create_inventory_agent():
    """Agent for checking stock and availability"""
    return create_agent(
        model=get_gemini(),
        middleware=[],
        tools=[check_stock, search_products],
        system_prompt="""You are an inventory specialist at AlBaqer Stones.

Your role:
- Check product availability
- Inform about stock levels
- Suggest alternatives if out of stock
- Provide restock information when possible

Be clear about stock status and alternatives.""",
    )


# =====================================================
# AGENT 11: SUPERVISOR AGENT (PATTERN 2)
# Implements Hierarchical Multi-Agent Pattern
# =====================================================
def create_supervisor_agent():
    """
    PATTERN: Supervisor/Coordinator Pattern
    Routes customer queries to appropriate specialized agents
    """
    return create_agent(
        model=get_deepseek(),  # More powerful for routing decisions
        middleware=[],
        tools=[],  # Supervisor doesn't use tools, delegates to agents
        system_prompt="""You are the Supervisor at AlBaqer Islamic Gemstone Store.

Your role is to ROUTE customer queries to the right specialist agent:

1. SEARCH_AGENT: Finding/browsing products
2. KNOWLEDGE_AGENT: Learning about stones, Islamic significance, education
3. RECOMMENDATION_AGENT: "What should I buy?", personalized suggestions
4. COMPARISON_AGENT: "Compare these products", "which is better?"
5. PRICING_AGENT: Currency conversion, price questions
6. DELIVERY_AGENT: Shipping, delivery fees, locations
7. PAYMENT_AGENT: Payment methods, how to pay
8. CUSTOMER_SERVICE_AGENT: General questions, complaints
9. CULTURAL_AGENT: Islamic traditions, cultural guidance, occasions
10. INVENTORY_AGENT: Stock availability, "is this in stock?"

Analyze the customer's intent and respond with ONLY the agent name that should handle this, nothing else.
Examples:
- "Show me aqeeq rings" -> SEARCH_AGENT
- "What is the Islamic meaning of turquoise?" -> KNOWLEDGE_AGENT  
- "I need a gift for Eid" -> RECOMMENDATION_AGENT
- "How much is 75 USD in LBP?" -> PRICING_AGENT
""",
    )


# =====================================================
# COMPLETE AGENT DICTIONARY
# =====================================================
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


# =====================================================
# MAIN EXECUTION FUNCTION WITH ERROR HANDLING
# =====================================================
def run_multi_agent_system(user_query: str) -> Dict[str, Any]:
    """
    Main function implementing multi-agent workflow with supervisor pattern
    Includes automatic fallback if Gemini fails
    """
    try:
        # Step 1: Supervisor routes the query
        supervisor = create_supervisor_agent()

        routing_result = supervisor.invoke(
            {
                "messages": [
                    {"role": "user", "content": f"Route this query: {user_query}"}
                ]
            }
        )

        # Extract agent name from supervisor response
        agent_name = routing_result["messages"][-1].content.strip()

        # Handle cases where supervisor returns full sentences
        for key in ALL_AGENTS.keys():
            if key in agent_name:
                agent_name = key
                break

        # Step 2: Execute with selected agent
        if agent_name in ALL_AGENTS:
            agent_func = ALL_AGENTS[agent_name]
            selected_agent = agent_func()

            result = selected_agent.invoke(
                {"messages": [{"role": "user", "content": user_query}]}
            )

            return {
                "query": user_query,
                "routed_to": agent_name,
                "response": result["messages"][-1].content,
                "full_conversation": result["messages"],
            }
        else:
            # Fallback to customer service
            customer_service = create_customer_service_agent()
            result = customer_service.invoke(
                {"messages": [{"role": "user", "content": user_query}]}
            )

            return {
                "query": user_query,
                "routed_to": "CUSTOMER_SERVICE_AGENT (fallback)",
                "response": result["messages"][-1].content,
                "full_conversation": result["messages"],
            }

    except Exception as e:
        # If anything fails, return error with DeepSeek fallback attempt
        error_msg = str(e)

        # Check if it's a Gemini error
        if (
            "RESOURCE_EXHAUSTED" in error_msg
            or "NOT_FOUND" in error_msg
            or "quota" in error_msg.lower()
        ):
            print(f"⚠️ Gemini API Error: {error_msg[:200]}")
            print("🔄 Switching all agents to DeepSeek...")

            # Force all agents to use DeepSeek
            try:
                # Retry with customer service using DeepSeek
                from langchain_openai import ChatOpenAI

                deepseek_agent = create_agent(
                    model=get_deepseek(),
                    middleware=[],
                    tools=[search_products],
                    system_prompt="You are a helpful assistant at AlBaqer Islamic Gemstone Store. Answer the customer's question helpfully.",
                )

                result = deepseek_agent.invoke(
                    {"messages": [{"role": "user", "content": user_query}]}
                )

                return {
                    "query": user_query,
                    "routed_to": "DEEPSEEK_FALLBACK",
                    "response": result["messages"][-1].content,
                    "full_conversation": result["messages"],
                }
            except Exception as fallback_error:
                return {
                    "query": user_query,
                    "routed_to": "ERROR",
                    "response": f"I apologize, but I'm experiencing technical difficulties. Error: {str(fallback_error)[:200]}. Please try again or contact support.",
                    "full_conversation": [],
                }

        # For other errors
        return {
            "query": user_query,
            "routed_to": "ERROR",
            "response": f"I apologize, but I encountered an error processing your request: {error_msg[:200]}. Please try rephrasing your question.",
            "full_conversation": [],
        }


# =====================================================
# EXAMPLE USAGE
# =====================================================
if __name__ == "__main__":
    print("=" * 60)
    print("AlBaqer Stones - Multi-Agent System")
    print("=" * 60)

    # Example queries demonstrating different agents
    test_queries = [
        "Show me Yemeni Aqeeq rings under $100",
        "What is the Islamic significance of turquoise?",
        "I need a gift for my mother's birthday, budget $150",
        "Compare product IDs 1, 2, and 3",
        "How much is 75 USD in Lebanese Pounds?",
        "What's the delivery fee to Tripoli?",
        "What payment methods do you accept?",
        "Is product ID 5 in stock?",
        "Can Muslim men wear gold jewelry?",
        "Tell me about Dur Al Najaf stone",
    ]

    print("\n🤖 Running Multi-Agent System Tests...\n")

    for query in test_queries[:3]:  # Test first 3 queries
        print(f"\n{'='*60}")
        print(f"USER: {query}")
        print(f"{'='*60}")

        try:
            result = run_multi_agent_system(query)
            print(f"\n✅ Routed to: {result['routed_to']}")
            print(f"\n🤖 Response:\n{result['response']}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

    print("\n" + "=" * 60)
    print("✅ Multi-Agent System Ready!")
    print("=" * 60)
