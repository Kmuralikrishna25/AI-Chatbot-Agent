import os

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver
from .graph import build_graph


# Load environment variables
load_dotenv(override=True)


# ============================================================
# Gemini API Key
# ============================================================

if not os.getenv("GEMINI_API_KEY"):
    raise ValueError(
        "GEMINI_API_KEY is not set. "
        "Please add it to your .env file."
    )


# ============================================================
# PostgreSQL
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. "
        "Please add it to your .env file."
    )


def main():

    # Connect to PostgreSQL
    with PostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:

        # Build LangGraph with PostgreSQL memory
        graph = build_graph(checkpointer)

        print("AI Chatbot started!")
        print("Model: Gemini 1.5 Flash")
        print("Google Gemini API enabled.")
        print("PostgreSQL memory enabled.")
        print("Type 'exit' or 'quit' to stop.\n")

        # Conversation ID
        thread_id = "conversation-1"

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        # ----------------------------------------------------
        # Chat loop
        # ----------------------------------------------------

        while True:

            user_input = input("You: ").strip()

            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            if not user_input:
                continue

            try:

                result = graph.invoke(
                    {
                        "messages": [
                            ("user", user_input)
                        ]
                    },
                    config=config
                )

                response = result["messages"][-1]

                print(f"AI: {response.content}\n")

            except Exception as e:

                print(f"Error: {e}\n")


if __name__ == "__main__":
    main()