import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage

from .state import ChatState


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not set. "
        "Please add it to your .env file."
    )


# ============================================================
# GEMINI MODEL
# ============================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0,
)


# ============================================================
# CHATBOT NODE
# ============================================================

def chatbot_node(state: ChatState):

    # --------------------------------------------------------
    # Get conversation history
    # --------------------------------------------------------

    messages = state["messages"]


    # --------------------------------------------------------
    # Get current RAG context
    # --------------------------------------------------------

    context = state.get("context", "")


    # --------------------------------------------------------
    # Build system prompt
    # --------------------------------------------------------

    if context:

        system_prompt = f"""
You are a helpful AI assistant with access to
an uploaded document.

The retrieved document context below is relevant
to the user's current question.

Use this document context as the primary source
for your answer.

DOCUMENT CONTEXT:

{context}

INSTRUCTIONS:

1. Answer the user's question using the document
   context whenever the information is available.

2. Do not invent information that is not supported
   by the document.

3. If the document context does not contain enough
   information to answer the question, clearly say
   that the available document context is insufficient.

4. You may use general knowledge when necessary,
   but do not contradict the document.

5. If the user asks what the uploaded document
   is about, summarize the information available
   in the retrieved document context.

6. Give a clear, natural and concise answer.
"""

    else:

        system_prompt = """
You are a helpful AI assistant.

No relevant information was retrieved from the
uploaded documents for the current question.

Answer the user's question using your general
knowledge.

Do not claim that your answer came from an
uploaded document.

Give a clear, natural and concise answer.
"""


    # --------------------------------------------------------
    # Build temporary model messages
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # The SystemMessage is NOT returned to LangGraph.
    # Therefore it does not become part of the
    # persistent conversation history.
    #
    # The document context is only used for this request.
    # --------------------------------------------------------

    model_messages = [
        SystemMessage(
            content=system_prompt
        )
    ] + messages


    # --------------------------------------------------------
    # Call Gemini
    # --------------------------------------------------------

    response = llm.invoke(
        model_messages
    )


    # --------------------------------------------------------
    # Return only assistant response
    # --------------------------------------------------------

    return {
        "messages": [response]
    }
