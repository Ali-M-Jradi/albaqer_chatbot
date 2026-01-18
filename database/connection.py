# =====================================================
# Database Connection
# =====================================================

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Create and return a database connection"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "albaqer_gemstone_ecommerce_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "po$7Gr@s$"),
    )
