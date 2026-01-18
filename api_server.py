# =====================================================
# AlBaqer Stones - FastAPI Server for Mobile Integration
# =====================================================

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
from datetime import datetime
import json

# Import chatbot system
from main import run_multi_agent_system

load_dotenv()

# =====================================================
# FastAPI APP
# =====================================================
app = FastAPI(
    title="AlBaqer Stones Chatbot API",
    description="RAG-powered chatbot for Islamic gemstone e-commerce",
    version="1.0.0",
)

# CORS Configuration for mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your mobile app domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# DATABASE CONNECTION
# =====================================================
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "albaqer_gemstone_ecommerce_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "po$7Gr@s$"),
    )


# =====================================================
# REQUEST/RESPONSE MODELS
# =====================================================
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class ChatResponse(BaseModel):
    session_id: str
    message: str
    routed_to: str
    sources: Optional[List[Dict]] = []
    metadata: Optional[Dict] = {}


class ChatHistoryResponse(BaseModel):
    conversation_id: int
    session_id: str
    messages: List[Dict]
    created_at: str
    last_message_at: str


# =====================================================
# ENDPOINTS
# =====================================================


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "AlBaqer Stones Chatbot API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "chat": "POST /api/chat",
            "history": "GET /api/chat/history/{user_id}",
            "delete_conversation": "DELETE /api/chat/history/{session_id}",
        },
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check with database status"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - processes user messages through multi-agent system

    Example request:
    {
        "message": "Show me diamond rings under $100",
        "user_id": 1,
        "session_id": "optional-session-id"
    }
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Process query through multi-agent system
        result = run_multi_agent_system(request.message)

        # Save conversation to database if user_id provided
        if request.user_id:
            save_chat_message(
                user_id=request.user_id,
                session_id=session_id,
                user_message=request.message,
                assistant_message=result["response"],
                routed_to=result["routed_to"],
                metadata=request.metadata,
            )

        return ChatResponse(
            session_id=session_id,
            message=result["response"],
            routed_to=result["routed_to"],
            sources=result.get("sources", []),
            metadata=result.get("metadata", {}),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@app.get("/api/chat/history/{user_id}", response_model=List[ChatHistoryResponse])
async def get_chat_history(user_id: int, limit: int = 10):
    """
    Retrieve chat history for a user

    Query parameters:
    - limit: Number of conversations to return (default: 10)
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get conversations
        cur.execute(
            """
            SELECT 
                c.id, c.session_id, c.created_at, c.last_message_at,
                json_agg(
                    json_build_object(
                        'role', m.role,
                        'content', m.content,
                        'routed_to', m.routed_to,
                        'created_at', m.created_at
                    ) ORDER BY m.created_at ASC
                ) as messages
            FROM chat_conversations c
            LEFT JOIN chat_messages m ON c.id = m.conversation_id
            WHERE c.user_id = %s
            GROUP BY c.id
            ORDER BY c.last_message_at DESC
            LIMIT %s
        """,
            (user_id, limit),
        )

        conversations = cur.fetchall()
        cur.close()
        conn.close()

        return [
            ChatHistoryResponse(
                conversation_id=conv["id"],
                session_id=conv["session_id"],
                messages=conv["messages"] or [],
                created_at=conv["created_at"].isoformat(),
                last_message_at=conv["last_message_at"].isoformat(),
            )
            for conv in conversations
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving history: {str(e)}"
        )


@app.delete("/api/chat/history/{session_id}")
async def delete_conversation(session_id: str):
    """
    Delete a conversation by session ID
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            DELETE FROM chat_conversations 
            WHERE session_id = %s
        """,
            (session_id,),
        )

        deleted_count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()

        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {"status": "deleted", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting conversation: {str(e)}"
        )


@app.get("/api/chat/session/{session_id}")
async def get_conversation_by_session(session_id: str):
    """
    Get a specific conversation by session ID
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT 
                c.id, c.session_id, c.user_id, c.created_at, c.last_message_at,
                json_agg(
                    json_build_object(
                        'role', m.role,
                        'content', m.content,
                        'routed_to', m.routed_to,
                        'created_at', m.created_at
                    ) ORDER BY m.created_at ASC
                ) as messages
            FROM chat_conversations c
            LEFT JOIN chat_messages m ON c.id = m.conversation_id
            WHERE c.session_id = %s
            GROUP BY c.id
        """,
            (session_id,),
        )

        conversation = cur.fetchone()
        cur.close()
        conn.close()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "conversation_id": conversation["id"],
            "session_id": conversation["session_id"],
            "user_id": conversation["user_id"],
            "messages": conversation["messages"] or [],
            "created_at": conversation["created_at"].isoformat(),
            "last_message_at": conversation["last_message_at"].isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving conversation: {str(e)}"
        )


# =====================================================
# HELPER FUNCTIONS
# =====================================================
def save_chat_message(
    user_id: int,
    session_id: str,
    user_message: str,
    assistant_message: str,
    routed_to: str,
    metadata: Dict = None,
):
    """Save chat message to database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get or create conversation
        cur.execute(
            """
            INSERT INTO chat_conversations (user_id, session_id)
            VALUES (%s, %s)
            ON CONFLICT (session_id) DO UPDATE SET last_message_at = CURRENT_TIMESTAMP
            RETURNING id
        """,
            (user_id, session_id),
        )

        conversation_id = cur.fetchone()["id"]

        # Save user message
        cur.execute(
            """
            INSERT INTO chat_messages (conversation_id, role, content, metadata)
            VALUES (%s, 'user', %s, %s)
        """,
            (conversation_id, user_message, json.dumps(metadata or {})),
        )

        # Save assistant message
        cur.execute(
            """
            INSERT INTO chat_messages (conversation_id, role, content, routed_to, metadata)
            VALUES (%s, 'assistant', %s, %s, %s)
        """,
            (conversation_id, assistant_message, routed_to, json.dumps(metadata or {})),
        )

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error saving chat message: {e}")


# =====================================================
# RUN SERVER
# =====================================================
if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🚀 Starting AlBaqer Stones Chatbot API Server")
    print("=" * 60)
    print("📍 Server will be available at:")
    print("   - http://localhost:8000")
    print("   - http://127.0.0.1:8000")
    print("   - http://192.168.0.116:8000")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
