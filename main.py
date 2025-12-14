# =====================================================
# AlBaqer Stones - Multi-Agent System Entry Point
# =====================================================

from typing import Dict, Any
from agents import ALL_AGENTS


def run_multi_agent_system(user_query: str) -> Dict[str, Any]:
    """
    Main function implementing multi-agent workflow with supervisor pattern
    Includes automatic fallback if Gemini fails
    """
    try:
        # Step 1: Supervisor routes the query
        supervisor = ALL_AGENTS["SUPERVISOR_AGENT"]()

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
            customer_service = ALL_AGENTS["CUSTOMER_SERVICE_AGENT"]()
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
        # If anything fails, return error with fallback attempt
        error_msg = str(e)

        # Check if it's a Gemini error
        if (
            "RESOURCE_EXHAUSTED" in error_msg
            or "NOT_FOUND" in error_msg
            or "quota" in error_msg.lower()
        ):
            print(f"⚠️ Gemini API Error: {error_msg[:200]}")
            print("🔄 Switching to Customer Service...")

            try:
                # Retry with customer service
                customer_service = ALL_AGENTS["CUSTOMER_SERVICE_AGENT"]()
                result = customer_service.invoke(
                    {"messages": [{"role": "user", "content": user_query}]}
                )

                return {
                    "query": user_query,
                    "routed_to": "CUSTOMER_SERVICE_AGENT (fallback)",
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
