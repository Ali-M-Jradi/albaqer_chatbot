# =====================================================
# Dynamic Model Selection Middleware
# =====================================================

from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from config.settings import get_deepseek, get_gemini


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
