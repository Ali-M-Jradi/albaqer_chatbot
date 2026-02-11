# =====================================================
# Specialized Agents (1-10)
# Simplified - using direct tool calls
# =====================================================

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.settings import get_deepseek, get_gemini
from tools import (
    search_products,
    check_stock,
    get_stone_info,
    compare_products,
    add_to_cart,
    view_cart,
    remove_from_cart,
    get_order_history,
    get_order_details,
    track_order_status,
    get_product_reviews,
    get_top_rated_products,
    get_review_summary,
)


class SimpleAgent:
    """Simple agent that calls tools and formats response"""

    def __init__(self, model, tools, system_prompt):
        self.model = model
        self.tools = {tool.name: tool for tool in tools}
        self.system_prompt = system_prompt

    def invoke(self, inputs):
        user_input = inputs.get("input", "")

        # Try to call relevant tools
        tool_results = []
        for tool_name, tool in self.tools.items():
            try:
                # Simple keyword matching to decide if tool is relevant
                if any(
                    keyword in user_input.lower()
                    for keyword in [
                        "search",
                        "find",
                        "show",
                        "diamond",
                        "ring",
                        "necklace",
                        "sapphire",
                        "ruby",
                        "emerald",
                        "stone",
                        "product",
                    ]
                ):
                    if tool_name == "search_products":
                        # Extract filters from query
                        tool_result = tool.func()
                        if tool_result:
                            tool_results.append(f"Product search results: {tool_result}")
            except Exception as e:
                continue

        # If tools returned results, format them through the LLM
        if tool_results:
            format_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        f"""{self.system_prompt}

You have received data from the database. Your task is to format this data into a helpful, 
natural language response for the customer. DO NOT return raw JSON. Instead:

1. Present products in a clear, readable format
2. Include key details: name, price, stone type, rating
3. Use simple dashes (-) for lists, no special formatting
4. Add helpful context or recommendations
5. Keep the tone friendly and professional

IMPORTANT: Do NOT use any markdown formatting. No asterisks (*), no bold (**), no code blocks (```), 
no backticks (`), no headers (#). Use plain text only with simple dashes for lists.

If there are no products found, suggest alternatives or ask clarifying questions.""",
                    ),
                    ("human", "User asked: {user_input}\n\nDatabase returned: {tool_data}\n\nFormat this into a helpful plain text response:"),
                ]
            )
            chain = format_prompt | self.model | StrOutputParser()
            response = chain.invoke({"user_input": user_input, "tool_data": "\n".join(tool_results)})
            return {"output": response}

        # Otherwise use LLM directly
        prompt = ChatPromptTemplate.from_messages(
            [("system", self.system_prompt + "\n\nIMPORTANT: Respond in plain text only. Do NOT use markdown formatting like asterisks (*), bold (**), code blocks (```), backticks (`), or headers (#). Use simple dashes (-) for lists."), ("human", "{input}")]
        )
        chain = prompt | self.model | StrOutputParser()
        response = chain.invoke({"input": user_input})
        return {"output": response}


def create_agent(model, tools, system_prompt, middleware=None):
    """Helper to create simple agent"""
    return SimpleAgent(model, tools, system_prompt)


# =====================================================
# AGENT 1: SEARCH AGENT
# =====================================================
def create_search_agent():
    """Agent specialized in finding products"""
    return create_agent(
        model=get_deepseek(),
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
# AGENT 2: STONE EDUCATION AGENT
# =====================================================
def create_stone_education_agent():
    """Agent specialized in gemstone education"""
    return create_agent(
        model=get_deepseek(),
        middleware=[],
        tools=[get_stone_info],
        system_prompt="""You are a gemstone education expert at AlBaqer Islamic Gemstone Store.

**DOMAIN: Gemstones, Minerals, and Precious Stones ONLY**

Your role:
- Educate customers about gemstones, minerals, and their properties
- Use get_stone_info for specific stone details and RAG knowledge
- Provide gemological facts, formation, and care instructions
- Explain Islamic significance of gemstones
- Help customers understand stone quality, 4Cs, and characteristics
- Answer ONLY gemstone-related questions

**Domain Restriction:**
If asked about non-gemstone topics, respond:
"I specialize in gemstone education. Please ask about gemstone properties, identification, care, or our Islamic gemstone collection."

Be knowledgeable, accurate, and stay within gemstone expertise.""",
    )


# =====================================================
# AGENT 3: RECOMMENDATION AGENT
# =====================================================
def create_recommendation_agent():
    """Agent specialized in personalized recommendations"""
    return create_agent(
        model=get_deepseek(),
        middleware=[],
        tools=[search_products, get_stone_info, get_top_rated_products],
        system_prompt="""You are a personalized recommendation specialist at AlBaqer Jewelry.

Your role:
- Understand customer preferences (budget, occasion, style)
- Recommend products that match their needs
- Consider top-rated products for quality assurance
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
        tools=[compare_products, get_stone_info, get_review_summary],
        system_prompt="""You are a product comparison specialist at AlBaqer Jewelry.

Your role:
- Compare products objectively
- Highlight differences in price, materials, stones, ratings
- Include customer reviews and ratings in comparisons
- Help customers make informed decisions
- Present comparisons in clear, structured format

Use tables or bullet points. Be objective and helpful.""",
    )


# =====================================================
# AGENT 5: CART AGENT
# =====================================================
def create_cart_agent():
    """Agent specialized in shopping cart management"""
    return create_agent(
        model=get_gemini(),
        middleware=[],
        tools=[add_to_cart, view_cart, remove_from_cart],
        system_prompt="""You are a shopping cart specialist at AlBaqer Jewelry.

Your role:
- Help customers add products to their cart
- Show cart contents and totals
- Remove items from cart
- Guide customers through the shopping process

Be helpful and clear about cart operations.""",
    )


# =====================================================
# AGENT 6: ORDER AGENT
# =====================================================
def create_order_agent():
    """Agent specialized in order management and tracking"""
    return create_agent(
        model=get_gemini(),
        middleware=[],
        tools=[get_order_history, get_order_details, track_order_status],
        system_prompt="""You are an order management specialist at AlBaqer Jewelry.

Your role:
- Show customer order history
- Provide detailed order information
- Track order status and updates
- Answer questions about past purchases

Be clear about order details and status.""",
    )


# =====================================================
# AGENT 7: REVIEW AGENT
# =====================================================
def create_review_agent():
    """Agent specialized in product reviews and ratings"""
    return create_agent(
        model=get_gemini(),
        middleware=[],
        tools=[get_product_reviews, get_top_rated_products, get_review_summary],
        system_prompt="""You are a customer review specialist at AlBaqer Jewelry.

Your role:
- Show product reviews and ratings
- Help customers find top-rated products
- Provide review summaries and statistics
- Help customers make informed decisions based on ratings

Be objective and helpful with review information.""",
    )


# =====================================================
# AGENT 8: CUSTOMER SERVICE AGENT
# =====================================================
def create_customer_service_agent():
    """General customer service agent with gemstone domain restriction"""
    return create_agent(
        model=get_gemini(),
        middleware=[dynamic_model_selection],
        tools=[search_products, view_cart],
        system_prompt="""You are a friendly customer service representative at AlBaqer Islamic Gemstone Store.

**DOMAIN RESTRICTION - GEMSTONES ONLY:**
You ONLY answer questions related to:
✅ Gemstones, minerals, and precious stones
✅ Our gemstone products and jewelry
✅ Gemstone properties, care, and identification
✅ Orders, shopping, and cart for gemstones
✅ Islamic significance of gemstones
✅ Gemstone grading, quality, and authenticity

You DO NOT answer questions about:
❌ General topics unrelated to gemstones
❌ Other products (electronics, clothing, food, etc.)
❌ Personal advice, medical, legal, or financial topics
❌ Current events, politics, or entertainment
❌ Homework, essays, or general knowledge
❌ Technical support for non-gemstone topics

**If user asks non-gemstone questions:**
Politely respond: "I apologize, but I am specialized in gemstone identification and Islamic gemstone jewelry. I can only assist with gemstone-related questions. Please ask me about our gemstones, products, orders, or gemstone properties."

**Your Role (Gemstone Topics Only):**
- Answer gemstone and jewelry inquiries
- Help with shopping for gemstones
- Provide gemstone information and care
- Handle orders and cart
- Route complex gemstone questions to specialized agents
- Share Islamic significance of stones

Be friendly, professional, and stay within gemstone domain.""",
    )


# =====================================================
# AGENT 9: QUALITY ASSURANCE AGENT
# =====================================================
def create_quality_agent():
    """Agent for product quality and ratings"""
    return create_agent(
        model=get_gemini(),
        middleware=[],
        tools=[get_top_rated_products, get_review_summary, get_product_reviews],
        system_prompt="""You are a quality assurance specialist at AlBaqer Jewelry.

Your role:
- Help customers find high-quality products
- Show top-rated items by category
- Explain rating systems and review summaries
- Guide customers to trusted products

Be objective and helpful with quality information.""",
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
