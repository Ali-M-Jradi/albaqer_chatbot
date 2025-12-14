# =====================================================
# Logistics & Payment Tools
# =====================================================

import json
from langchain.tools import tool
from psycopg2.extras import RealDictCursor
from database.connection import get_db_connection


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
