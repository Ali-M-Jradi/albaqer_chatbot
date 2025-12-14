-- =====================================================
-- COMPLETE DATABASE SETUP (WITHOUT VECTOR SUPPORT)
-- This version works immediately on PostgreSQL 18.1
-- You can add pgvector later when needed
-- =====================================================

-- =====================================================
-- PART 1: SCHEMA MODIFICATIONS
-- =====================================================

-- 1. ENHANCE STONES TABLE
ALTER TABLE stones
ADD COLUMN IF NOT EXISTS arabic_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS islamic_significance TEXT,
ADD COLUMN IF NOT EXISTS cultural_significance TEXT,
ADD COLUMN IF NOT EXISTS prophetic_hadith TEXT,
ADD COLUMN IF NOT EXISTS healing_properties TEXT,
ADD COLUMN IF NOT EXISTS historical_facts TEXT,
ADD COLUMN IF NOT EXISTS recommended_for VARCHAR(50),
ADD COLUMN IF NOT EXISTS sunnah_stone BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS tourist_appeal BOOLEAN DEFAULT FALSE;

-- 2. ENHANCE PRODUCTS TABLE
ALTER TABLE products
ADD COLUMN IF NOT EXISTS has_engraving BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS engraving_options TEXT[],
ADD COLUMN IF NOT EXISTS is_sunnah_design BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_traditional_lebanese BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS story_behind TEXT,
ADD COLUMN IF NOT EXISTS halal_certified BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS price_usd NUMERIC(10,2),
ADD COLUMN IF NOT EXISTS price_lbp NUMERIC(15,2),
ADD COLUMN IF NOT EXISTS price_eur NUMERIC(10,2),
ADD COLUMN IF NOT EXISTS import_country VARCHAR(100),
ADD COLUMN IF NOT EXISTS customs_paid BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS gift_packaging_available BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS tourist_favorite BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS zakat_applicable BOOLEAN DEFAULT TRUE;

-- 3. CURRENCY EXCHANGE RATES TABLE
CREATE TABLE IF NOT EXISTS currency_rates (
    rate_id SERIAL PRIMARY KEY,
    currency_code VARCHAR(3) NOT NULL,
    rate_to_usd NUMERIC(15,6) NOT NULL,
    official_rate BOOLEAN DEFAULT FALSE,
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_currency_rates_date ON currency_rates(created_at DESC);

-- 4. DELIVERY ZONES TABLE
CREATE TABLE IF NOT EXISTS delivery_zones (
    zone_id SERIAL PRIMARY KEY,
    zone_name VARCHAR(100) NOT NULL,
    governorate VARCHAR(50),
    delivery_fee_usd NUMERIC(10,2),
    delivery_days INTEGER,
    requires_verification BOOLEAN DEFAULT FALSE,
    currently_delivering BOOLEAN DEFAULT TRUE,
    security_level VARCHAR(20),
    notes TEXT
);

-- 5. ENHANCE ORDERS TABLE
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS currency_used VARCHAR(3) DEFAULT 'USD',
ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(15,6),
ADD COLUMN IF NOT EXISTS delivery_zone_id INTEGER REFERENCES delivery_zones(zone_id),
ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50),
ADD COLUMN IF NOT EXISTS delivery_address TEXT,
ADD COLUMN IF NOT EXISTS delivery_phone VARCHAR(20),
ADD COLUMN IF NOT EXISTS special_instructions TEXT;

-- 6. PAYMENT METHODS TABLE
CREATE TABLE IF NOT EXISTS payment_methods (
    method_id SERIAL PRIMARY KEY,
    method_name VARCHAR(50) NOT NULL,
    method_type VARCHAR(30),
    is_active BOOLEAN DEFAULT TRUE,
    fee_percentage NUMERIC(5,2) DEFAULT 0,
    min_amount_usd NUMERIC(10,2),
    max_amount_usd NUMERIC(10,2),
    instructions TEXT
);

-- 7. ENHANCE KNOWLEDGE_BASE (WITHOUT VECTORS)
ALTER TABLE knowledge_base
ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en',
ADD COLUMN IF NOT EXISTS content_type VARCHAR(30) DEFAULT 'general',
ADD COLUMN IF NOT EXISTS target_audience VARCHAR(50) DEFAULT 'all',
ADD COLUMN IF NOT EXISTS tags TEXT[];

-- Create text search indexes instead of vector
CREATE INDEX IF NOT EXISTS idx_knowledge_content_type ON knowledge_base(content_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_audience ON knowledge_base(target_audience);
CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_base(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge_base USING gin(tags);

-- Full text search index (alternative to vector search)
CREATE INDEX IF NOT EXISTS idx_knowledge_fulltext 
ON knowledge_base USING gin(to_tsvector('english', title || ' ' || content));

-- 8. ENHANCE MATERIALS TABLE
ALTER TABLE materials
ADD COLUMN IF NOT EXISTS purity VARCHAR(20),
ADD COLUMN IF NOT EXISTS color VARCHAR(50);

-- =====================================================
-- PART 2: SAMPLE DATA INSERTION
-- =====================================================

-- Delete existing sample data to avoid conflicts (if re-running)
DELETE FROM currency_rates;
DELETE FROM delivery_zones;
DELETE FROM payment_methods;

-- 1. CURRENCY RATES
INSERT INTO currency_rates (currency_code, rate_to_usd, official_rate, source) VALUES
('LBP', 89500, FALSE, 'parallel_market'),
('LBP', 15000, TRUE, 'BDL'),
('EUR', 0.92, TRUE, 'ECB'),
('USD', 1.00, TRUE, 'base');

-- 2. DELIVERY ZONES
INSERT INTO delivery_zones (zone_name, governorate, delivery_fee_usd, delivery_days, security_level) VALUES
('Beirut Central', 'Beirut', 2.00, 1, 'safe'),
('Beirut Suburbs', 'Beirut', 3.00, 2, 'safe'),
('Jounieh/Byblos', 'Mount Lebanon', 3.50, 2, 'safe'),
('Tripoli', 'North', 5.00, 3, 'safe'),
('Saida', 'South', 4.50, 2, 'safe'),
('Tyre', 'South', 6.00, 3, 'moderate'),
('Zahle', 'Bekaa', 5.50, 3, 'safe'),
('Baalbek', 'Bekaa', 7.00, 4, 'moderate');

-- 3. PAYMENT METHODS
INSERT INTO payment_methods (method_name, method_type, is_active, fee_percentage, instructions) VALUES
('Cash on Delivery', 'cash', TRUE, 0, 'Pay in USD or LBP at current rate'),
('OMT', 'mobile_money', TRUE, 1.5, 'Transfer via OMT offices'),
('Whish Money', 'mobile_money', TRUE, 1.0, 'Transfer via Whish app'),
('Bank Transfer', 'bank', TRUE, 0, 'Local bank transfer'),
('USDT (TRC20)', 'crypto', TRUE, 0, 'Cryptocurrency payment');

-- 4. CATEGORIES (only insert if not exists)
INSERT INTO categories (name, description) 
SELECT 'Rings', 'Traditional and modern rings for men and women'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Rings')
UNION ALL
SELECT 'Necklaces', 'Elegant necklaces and pendants'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Necklaces')
UNION ALL
SELECT 'Bracelets', 'Beautiful bracelets and bangles'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Bracelets')
UNION ALL
SELECT 'Earrings', 'Stylish earrings for women'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Earrings')
UNION ALL
SELECT 'Tasbih', 'Islamic prayer beads (Misbaha/Subha)'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Tasbih')
UNION ALL
SELECT 'Aqeeq Rings', 'Traditional Islamic Aqeeq rings'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Aqeeq Rings')
UNION ALL
SELECT 'Islamic Pendants', 'Pendants with Islamic calligraphy'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Islamic Pendants')
UNION ALL
SELECT 'Hijab Pins', 'Decorative pins for hijab'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Hijab Pins');

-- 5. MATERIALS (only insert if not exists)
INSERT INTO materials (name, purity, color)
SELECT '925 Silver', '92.5%', 'silver'
WHERE NOT EXISTS (SELECT 1 FROM materials WHERE name = '925 Silver')
UNION ALL
SELECT '18K Gold', '75%', 'yellow'
WHERE NOT EXISTS (SELECT 1 FROM materials WHERE name = '18K Gold')
UNION ALL
SELECT '14K Gold', '58.5%', 'yellow'
WHERE NOT EXISTS (SELECT 1 FROM materials WHERE name = '14K Gold')
UNION ALL
SELECT 'Rose Gold', '75%', 'rose'
WHERE NOT EXISTS (SELECT 1 FROM materials WHERE name = 'Rose Gold')
UNION ALL
SELECT 'White Gold', '75%', 'white'
WHERE NOT EXISTS (SELECT 1 FROM materials WHERE name = 'White Gold')
UNION ALL
SELECT 'Stainless Steel', 'surgical grade', 'silver'
WHERE NOT EXISTS (SELECT 1 FROM materials WHERE name = 'Stainless Steel')
UNION ALL
SELECT 'Platinum', '95%', 'white'
WHERE NOT EXISTS (SELECT 1 FROM materials WHERE name = 'Platinum');

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Check what was created
SELECT 'Setup Complete!' AS status;
SELECT COUNT(*) AS total_categories FROM categories;
SELECT COUNT(*) AS total_materials FROM materials;
SELECT COUNT(*) AS total_products FROM products;
SELECT COUNT(*) AS total_stones FROM stones;
SELECT COUNT(*) AS delivery_zones FROM delivery_zones;
SELECT COUNT(*) AS payment_methods FROM payment_methods;

-- =====================================================
-- DONE! 
-- Database ready for multi-agent system
-- RAG will use keyword search instead of semantic search
-- You can add pgvector later when available for PG 18
-- =====================================================