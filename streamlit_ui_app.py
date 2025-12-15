# =====================================================
# AlBaqer Islamic Gemstone Store - Streamlit UI
# Interactive Interface with Multi-Agent System
# =====================================================

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Import multi-agent system
try:
    from main import run_multi_agent_system

    AGENTS_AVAILABLE = True
except ImportError as e:
    AGENTS_AVAILABLE = False
    print(f"Warning: Could not import multi-agent system - {str(e)}")

load_dotenv()

# =====================================================
# PAGE CONFIGURATION
# =====================================================
st.set_page_config(
    page_title="AlBaqer Islamic Gemstone Store",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =====================================================
# DATABASE CONNECTION (FIXED)
# =====================================================
def get_db_connection():
    """Create a new database connection for each query"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "albaqer_stones_store"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


# =====================================================
# DATA FETCHING FUNCTIONS (Using Python Data Structures)
# =====================================================
def fetch_all_products(filters=None):
    """Fetch products with optional filters - returns list of dicts"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT p.product_id, p.name, p.description, p.price_usd, p.price_lbp,
                   p.gender, p.occasion, p.stock, p.is_sunnah_design, p.story_behind,
                   c.name as category, m.name as material,
                   array_agg(DISTINCT s.name) as stones
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN materials m ON p.material_id = m.material_id
            LEFT JOIN product_stones ps ON p.product_id = ps.product_id
            LEFT JOIN stones s ON ps.stone_id = s.stone_id
            WHERE 1=1
        """

        params = []
        if filters:
            if filters.get("category"):
                query += " AND c.name = %s"
                params.append(filters["category"])
            if filters.get("min_price"):
                query += " AND p.price_usd >= %s"
                params.append(filters["min_price"])
            if filters.get("max_price"):
                query += " AND p.price_usd <= %s"
                params.append(filters["max_price"])
            if filters.get("gender"):
                query += " AND (p.gender = %s OR p.gender = 'both')"
                params.append(filters["gender"])
            if filters.get("sunnah_only"):
                query += " AND p.is_sunnah_design = true"

        query += " GROUP BY p.product_id, c.name, m.name ORDER BY p.price_usd"

        cur.execute(query, params)
        results = [dict(row) for row in cur.fetchall()]  # List comprehension
        return results
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return []
    finally:
        if "cur" in locals() and cur:
            cur.close()
        if "conn" in locals() and conn:
            conn.close()


def fetch_categories():
    """Fetch all categories - returns list"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT category_id, name FROM categories ORDER BY name")
        results = [row["name"] for row in cur.fetchall()]  # List comprehension
        return results
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return []
    finally:
        if "cur" in locals() and cur:
            cur.close()
        if "conn" in locals() and conn:
            conn.close()


def fetch_stones():
    """Fetch all stones with details - returns dictionary"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT stone_id, name, color, arabic_name, islamic_significance,
                   cultural_significance, healing_properties, sunnah_stone
            FROM stones ORDER BY name
        """
        )
        results = {
            row["name"]: dict(row) for row in cur.fetchall()
        }  # Dict comprehension
        return results
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return {}
    finally:
        if "cur" in locals() and cur:
            cur.close()
        if "conn" in locals() and conn:
            conn.close()


def fetch_delivery_zones():
    """Fetch delivery zones - returns list of dicts"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM delivery_zones ORDER BY governorate")
        results = [dict(row) for row in cur.fetchall()]
        return results
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return []
    finally:
        if "cur" in locals() and cur:
            cur.close()
        if "conn" in locals() and conn:
            conn.close()


# =====================================================
# SESSION STATE INITIALIZATION
# =====================================================
if "cart" not in st.session_state:
    st.session_state.cart = []  # List of product dicts
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # List of message dicts
if "selected_currency" not in st.session_state:
    st.session_state.selected_currency = "USD"


# =====================================================
# CURRENCY FUNCTIONS
# =====================================================
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_currency_rates():
    """Fetch latest currency rates from database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT currency_code, rate_to_usd
            FROM currency_rates
            WHERE currency_code = 'LBP'
            ORDER BY created_at DESC
            LIMIT 1
        """
        )
        rates_data = cur.fetchall()
        cur.close()
        conn.close()

        # Build rates dictionary (rate_to_usd means how many units per 1 USD)
        rates = {"USD": 1.0}
        for row in rates_data:
            if row["currency_code"] == "LBP":
                rates["LBP"] = float(row["rate_to_usd"])

        # Fallback if LBP rate is missing
        if "LBP" not in rates:
            rates["LBP"] = 89500  # 1 USD = 89,500 LBP

        return rates
    except Exception as e:
        # Fallback rates if database unavailable
        return {"USD": 1.0, "LBP": 89500}


def convert_price(usd_price, target_currency="LBP"):
    """Convert USD price to other currencies using live rates"""
    rates = fetch_currency_rates()
    return usd_price * rates.get(target_currency, 1.0)


def format_price(usd_price, currency="USD"):
    """Format price with currency symbol"""
    converted = convert_price(usd_price, currency)
    symbols = {"USD": "$", "LBP": "LL"}
    return f"{symbols[currency]}{converted:,.2f}"


# =====================================================
# SIDEBAR NAVIGATION
# =====================================================
st.sidebar.image(
    "https://via.placeholder.com/200x100?text=AlBaqer+Stones", use_container_width=True
)
st.sidebar.title("🕌 Navigation")

page = st.sidebar.radio(
    "Go to",
    [
        "🏠 Home",
        "🛍️ Shop",
        "🤖 AI Assistant",
        "🛒 Cart",
        "📍 Delivery Info",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 💱 Currency")
st.session_state.selected_currency = st.sidebar.selectbox(
    "Select Currency", ["USD", "LBP"], index=1
)

# Show current exchange rate from database
rates = fetch_currency_rates()
with st.sidebar.expander("📊 Current Exchange Rates"):
    st.write(f"🇺🇸 USD: 1.00")
    st.write(f"🇱🇧 LBP: {rates['LBP']:,.0f}")
    st.caption("Rates updated hourly from database")

# =====================================================
# PAGE: HOME
# =====================================================
if page == "🏠 Home":
    st.title("🕌 Welcome to AlBaqer Islamic Gemstone Store")
    st.markdown("### Your Trusted Source for Authentic Islamic Jewelry in Lebanon")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Products Available", "28", delta="In Stock")
    with col2:
        st.metric("Islamic Gemstones", "9", delta="Authentic")
    with col3:
        st.metric("Delivery Zones", "8", delta="Across Lebanon")

    st.markdown("---")

    # Why Choose Us
    st.subheader("🌟 Why Choose AlBaqer Stones?")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        - ✅ **Authentic Islamic Gemstones** - Yemeni Aqeeq, Persian Turquoise
        - ✅ **Sunnah Designs** - Following traditional Islamic jewelry styles
        - ✅ **Educational Approach** - Learn about Islamic significance
        - ✅ **Multi-Currency Support** - USD, LBP, EUR
        """
        )

    with col2:
        st.markdown(
            """
        - ✅ **Lebanon-Wide Delivery** - All governorates covered
        - ✅ **Flexible Payment** - Cash, OMT, Whish, Bank Transfer, Crypto
        - ✅ **AI Shopping Assistant** - Get personalized recommendations
        - ✅ **Welcome All Customers** - Respect for diverse backgrounds
        """
        )

# =====================================================
# PAGE: SHOP
# =====================================================
elif page == "🛍️ Shop":
    st.title("🛍️ Shop Our Collection")

    # Filters Section
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Filters")

    categories = fetch_categories()
    selected_category = st.sidebar.selectbox("Category", ["All"] + categories)

    gender_filter = st.sidebar.radio("Gender", ["All", "men", "women", "both"])

    price_range = st.sidebar.slider(
        "Price Range (USD)", min_value=0, max_value=500, value=(0, 500), step=10
    )

    sunnah_only = st.sidebar.checkbox("Sunnah Designs Only")

    # Build filters dictionary
    filters = {
        "category": selected_category if selected_category != "All" else None,
        "gender": gender_filter if gender_filter != "All" else None,
        "min_price": price_range[0],
        "max_price": price_range[1],
        "sunnah_only": sunnah_only,
    }

    # Fetch filtered products
    products = fetch_all_products(filters)

    st.markdown(f"### Found {len(products)} products")

    # Display products in grid
    cols_per_row = 3
    for i in range(0, len(products), cols_per_row):
        cols = st.columns(cols_per_row)

        for col, product in zip(cols, products[i : i + cols_per_row]):
            with col:
                with st.container(border=True):
                    # Product card
                    st.markdown(f"### {product['name']}")

                    # Badges
                    badges = []
                    if product["is_sunnah_design"]:
                        badges.append("🕌 Sunnah")
                    if product["gender"]:
                        badges.append(f"👤 {product['gender'].title()}")
                    if badges:
                        st.markdown(" ".join(badges))

                    st.markdown(f"**Category:** {product['category']}")
                    if product["material"]:
                        st.markdown(f"**Material:** {product['material']}")
                    if product["stones"] and product["stones"][0]:
                        st.markdown(
                            f"**Stones:** {', '.join(filter(None, product['stones']))}"
                        )

                    # Price
                    price_formatted = format_price(
                        float(product["price_usd"]), st.session_state.selected_currency
                    )
                    st.markdown(f"### {price_formatted}")

                    # Stock status
                    if product["stock"] > 5:
                        st.success(f"✅ In Stock ({product['stock']} available)")
                    elif product["stock"] > 0:
                        st.warning(f"⚠️ Low Stock ({product['stock']} left)")
                    else:
                        st.error("❌ Out of Stock")

                    # Buttons
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(
                            "View Details", key=f"view_{product['product_id']}"
                        ):
                            st.session_state.selected_product = product
                            st.session_state.show_modal = True

                    with col_btn2:
                        if product["stock"] > 0:
                            if st.button(
                                "Add to Cart", key=f"cart_{product['product_id']}"
                            ):
                                st.session_state.cart.append(product)
                                st.success("Added to cart!")

    # Product Details Modal (using expander)
    if hasattr(st.session_state, "show_modal") and st.session_state.show_modal:
        product = st.session_state.selected_product

        with st.expander("📋 Product Details", expanded=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"## {product['name']}")
                st.markdown(product["description"])

                if product["story_behind"]:
                    st.markdown("### 📖 Story Behind This Piece")
                    st.info(product["story_behind"])

            with col2:
                st.markdown(
                    f"### {format_price(float(product['price_usd']), st.session_state.selected_currency)}"
                )
                st.markdown(f"**Stock:** {product['stock']}")
                st.markdown(f"**Category:** {product['category']}")
                st.markdown(f"**Material:** {product['material']}")

                if st.button("Close", key="close_modal"):
                    st.session_state.show_modal = False
                    st.rerun()

# =====================================================
# PAGE: AI ASSISTANT
# =====================================================
elif page == "🤖 AI Assistant":
    st.title("🤖 AI Shopping Assistant")
    st.markdown(
        "Ask me anything about products, Islamic significance, or get personalized recommendations!"
    )

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("agent"):
                st.caption(f"🤖 Handled by: {message['agent']}")

    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if AGENTS_AVAILABLE:
                    try:
                        # Use actual multi-agent system
                        response = run_multi_agent_system(prompt)

                        st.markdown(response["response"])
                        st.caption(f"🤖 {response['routed_to']}")

                        # Save assistant response
                        st.session_state.chat_history.append(
                            {
                                "role": "assistant",
                                "content": response["response"],
                                "agent": response["routed_to"],
                            }
                        )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        st.markdown(
                            "I'm having trouble processing your request. Please try again."
                        )
                else:
                    # Fallback simulated response
                    st.markdown(
                        f"I found several products matching '{prompt}'. Here are my top recommendations..."
                    )
                    st.caption("🤖 SEARCH_AGENT (Demo Mode)")

                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": f"Demo response for: {prompt}",
                            "agent": "DEMO_MODE",
                        }
                    )

    # Quick actions
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ Quick Questions")
    quick_questions = [
        "Show me Aqeeq rings under $100",
        "What is the Islamic significance of turquoise?",
        "I need a gift for Eid",
        "Convert 75 USD to LBP",
        "What's the delivery fee to Beirut?",
    ]

    for question in quick_questions:
        if st.sidebar.button(question, key=f"quick_{question}"):
            st.session_state.chat_history.append({"role": "user", "content": question})
            st.rerun()

# =====================================================
# PAGE: CART
# =====================================================
elif page == "🛒 Cart":
    st.title("🛒 Shopping Cart")

    if not st.session_state.cart:
        st.info("Your cart is empty. Start shopping!")
    else:
        # Display cart items
        total = 0

        for idx, item in enumerate(st.session_state.cart):
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"### {item['name']}")
                    st.markdown(f"*{item['category']}*")

                with col2:
                    price = float(item["price_usd"])
                    st.markdown(
                        f"**{format_price(price, st.session_state.selected_currency)}**"
                    )
                    total += price

                with col3:
                    if st.button("Remove", key=f"remove_{idx}"):
                        st.session_state.cart.pop(idx)
                        st.rerun()

        st.markdown("---")

        # Cart summary
        col1, col2 = st.columns([2, 1])

        with col2:
            st.markdown(
                f"### Subtotal: {format_price(total, st.session_state.selected_currency)}"
            )

            delivery_zone = st.selectbox(
                "Delivery Zone", ["Beirut Central", "Beirut Suburbs", "Other"]
            )
            delivery_fee = 2.0 if delivery_zone == "Beirut Central" else 3.0

            st.markdown(
                f"**Delivery:** {format_price(delivery_fee, st.session_state.selected_currency)}"
            )
            st.markdown(
                f"### Total: {format_price(total + delivery_fee, st.session_state.selected_currency)}"
            )

            if st.button("Proceed to Checkout", type="primary"):
                st.success("🎉 Order placed successfully!")
                st.balloons()
                st.session_state.cart = []

# =====================================================
# PAGE: DELIVERY INFO
# =====================================================
elif page == "📍 Delivery Info":
    st.title("📍 Delivery Information")

    zones = fetch_delivery_zones()

    # Group by governorate using dictionary
    grouped_zones = {}
    for zone in zones:
        gov = zone["governorate"]
        if gov not in grouped_zones:
            grouped_zones[gov] = []
        grouped_zones[gov].append(zone)

    for governorate, zone_list in grouped_zones.items():
        with st.expander(f"📍 {governorate}", expanded=True):
            for zone in zone_list:
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown(f"**{zone['zone_name']}**")
                with col2:
                    st.markdown(f"💵 ${zone['delivery_fee_usd']:.2f}")
                with col3:
                    st.markdown(f"📦 {zone['delivery_days']} days")
                with col4:
                    status = "🟢" if zone["security_level"] == "safe" else "🟡"
                    st.markdown(f"{status} {zone['security_level'].title()}")

# =====================================================
# FOOTER
# =====================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 📞 Contact Us")
st.sidebar.markdown("📧 info@albaqerstones.com")
st.sidebar.markdown("📱 +961 XX XXX XXX")
st.sidebar.markdown("📍 Beirut, Lebanon")

st.sidebar.markdown("---")
st.sidebar.caption("💎 AlBaqer Stones © 2024")
st.sidebar.caption("Authentic Islamic Gemstone Jewelry")
