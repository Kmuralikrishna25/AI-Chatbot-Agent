
import os

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from .state import ChatState
from .nodes import chatbot_node


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(override=True)


# ============================================================
# DATABASE URL
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. "
        "Please add it to your .env file."
    )


# ============================================================
# BUILD LANGGRAPH
# ============================================================

def build_graph(checkpointer):

    graph = StateGraph(ChatState)

    # Add chatbot node
    graph.add_node(
        "chatbot",
        chatbot_node
    )

    # Define workflow
    graph.add_edge(START,"chatbot")
    graph.add_edge("chatbot",END)

    # Compile with PostgreSQL checkpointer
    return graph.compile(
        checkpointer=checkpointer
    )
