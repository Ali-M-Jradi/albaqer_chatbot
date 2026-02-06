-- =====================================================
-- AlBaqer Stones - Simple Vector Storage (NO pgvector)
-- Works on any PostgreSQL without extensions
-- =====================================================

-- =====================================================
-- Vector Storage Table (using JSON for embeddings)
-- =====================================================
CREATE TABLE IF NOT EXISTS knowledge_base_vectors (
    id SERIAL PRIMARY KEY,
    knowledge_base_id INTEGER REFERENCES knowledge_base(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding_json TEXT NOT NULL,  -- Store as JSON array string
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for knowledge_base_id lookups
CREATE INDEX IF NOT EXISTS idx_knowledge_vectors_kb_id 
ON knowledge_base_vectors(knowledge_base_id);

-- Create index for metadata filtering
CREATE INDEX IF NOT EXISTS idx_knowledge_vectors_metadata 
ON knowledge_base_vectors USING gin(metadata);


-- =====================================================
-- Chat History Tables (for mobile app)
-- =====================================================
CREATE TABLE IF NOT EXISTS chat_conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,  -- Made nullable for guest users
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
-- Verify Setup
-- =====================================================
SELECT 'Tables created successfully' as status
WHERE EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name IN ('knowledge_base_vectors', 'chat_conversations', 'chat_messages')
);

-- Show table structure
\d knowledge_base_vectors
\d chat_conversations
\d chat_messages
