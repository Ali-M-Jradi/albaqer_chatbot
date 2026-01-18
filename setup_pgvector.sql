-- =====================================================
-- AlBaqer Stones - pgvector Setup Script
-- PostgreSQL Vector Extension for RAG System
-- =====================================================

-- =====================================================
-- Step 1: Install pgvector Extension
-- =====================================================
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_available_extensions WHERE name = 'vector';


-- =====================================================
-- Step 2: Create Vector Storage Table
-- =====================================================
CREATE TABLE IF NOT EXISTS knowledge_base_vectors (
    id SERIAL PRIMARY KEY,
    knowledge_base_id INTEGER REFERENCES knowledge_base(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(384),  -- MiniLM model produces 384-dimensional vectors
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for fast similarity search (cosine distance)
CREATE INDEX IF NOT EXISTS idx_knowledge_vectors_embedding 
ON knowledge_base_vectors USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for knowledge_base_id lookups
CREATE INDEX IF NOT EXISTS idx_knowledge_vectors_kb_id 
ON knowledge_base_vectors(knowledge_base_id);

-- Create index for metadata filtering
CREATE INDEX IF NOT EXISTS idx_knowledge_vectors_metadata 
ON knowledge_base_vectors USING gin(metadata);


-- =====================================================
-- Step 3: Create Chat History Tables (for mobile app)
-- =====================================================
CREATE TABLE IF NOT EXISTS chat_conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES chat_conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    routed_to VARCHAR(100),  -- Which agent handled this
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for chat history
CREATE INDEX IF NOT EXISTS idx_chat_conv_user ON chat_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_conv_session ON chat_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_msg_conv ON chat_messages(conversation_id);


-- =====================================================
-- Step 4: Utility Functions
-- =====================================================

-- Function to search vectors by similarity
CREATE OR REPLACE FUNCTION search_knowledge_vectors(
    query_embedding vector(384),
    match_count INT DEFAULT 3,
    filter_metadata JSONB DEFAULT NULL
)
RETURNS TABLE (
    id INT,
    knowledge_base_id INT,
    content TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        kbv.id,
        kbv.knowledge_base_id,
        kbv.content,
        1 - (kbv.embedding <=> query_embedding) as similarity,
        kbv.metadata
    FROM knowledge_base_vectors kbv
    WHERE 
        CASE 
            WHEN filter_metadata IS NOT NULL THEN kbv.metadata @> filter_metadata
            ELSE TRUE
        END
    ORDER BY kbv.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;


-- =====================================================
-- Verify Setup
-- =====================================================
SELECT 'pgvector extension installed' as status
WHERE EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector');

SELECT 'Tables created successfully' as status
WHERE EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name IN ('knowledge_base_vectors', 'chat_conversations', 'chat_messages')
);

-- Show table counts
SELECT 
    'knowledge_base_vectors' as table_name,
    COUNT(*) as record_count
FROM knowledge_base_vectors
UNION ALL
SELECT 
    'chat_conversations',
    COUNT(*)
FROM chat_conversations
UNION ALL
SELECT 
    'chat_messages',
    COUNT(*)
FROM chat_messages;
