import os
import uuid

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from app.ingestion.ingest import ingest_document
from app.retrieval.vector_search import semantic_search
from app.retrieval.pinecone_store import upsert_chunks
from app.graph_runtime import graph

from app.chat_threads import (
    initialize_chat_threads,
    create_thread,
    get_threads,
    update_thread_title,
    touch_thread,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")


required_env_vars = {
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "DATABASE_URL": DATABASE_URL,
    "PINECONE_API_KEY": PINECONE_API_KEY,
    "PINECONE_INDEX_NAME": PINECONE_INDEX_NAME,
}

for name, value in required_env_vars.items():
    if not value:
        raise ValueError(
            f"{name} is not set. Please check your .env file."
        )


# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENT_RELEVANCE_THRESHOLD = 0.40
UPLOAD_DIRECTORY = "uploaded_documents"
MAX_THREAD_TITLE_LENGTH = 45


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI RAG Chatbot",
    page_icon="🤖",
    layout="wide",
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

initialize_chat_threads()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_new_thread():
    """Create and return a new conversation thread."""

    thread_id = f"streamlit-{uuid.uuid4().hex}"

    create_thread(
        thread_id=thread_id,
        title="New Conversation",
    )

    return thread_id


def load_thread(thread_id: str):
    """Load LangGraph messages for a conversation."""

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    try:
        state_snapshot = graph.get_state(config)

        if not state_snapshot:
            return []

        return state_snapshot.values.get("messages", [])

    except Exception as e:
        st.error(f"Unable to load conversation: {e}")
        return []


def extract_text(content) -> str:
    """
    Convert Gemini/LangChain message content into plain text.

    Gemini may return:
    - a normal string
    - a list of strings
    - a list of dictionaries containing text
    """

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []

        for block in content:

            if isinstance(block, str):
                text_parts.append(block)

            elif isinstance(block, dict):
                text = block.get("text")

                if text:
                    text_parts.append(str(text))

        return "".join(text_parts)

    if content is None:
        return ""

    return str(content)


def convert_messages(messages):
    """Convert LangGraph messages into Streamlit chat format."""

    converted = []

    for message in messages:

        if message.type == "human":
            converted.append(
                {
                    "role": "user",
                    "content": extract_text(message.content),
                }
            )

        elif message.type == "ai":
            converted.append(
                {
                    "role": "assistant",
                    "content": extract_text(message.content),
                    "source": None,
                }
            )

    return converted


def generate_thread_title(user_input: str) -> str:
    """Create a short title from the first user message."""

    title = user_input.strip()

    if len(title) > MAX_THREAD_TITLE_LENGTH:
        title = (
            title[:MAX_THREAD_TITLE_LENGTH].rstrip()
            + "..."
        )

    return title


def build_document_context(results):
    """Build context from retrieved document chunks."""

    if not results:
        return "", "general"

    best_score = max(
        result["score"]
        for result in results
    )

    if best_score < DOCUMENT_RELEVANCE_THRESHOLD:
        return "", "general"

    context = "\n\n".join(
        result["content"]
        for result in results
    )

    return context, "document"


# ============================================================
# SESSION STATE
# ============================================================

if "thread_id" not in st.session_state:
    st.session_state.thread_id = create_new_thread()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []


# ============================================================
# HEADER
# ============================================================

st.title("🤖 AI RAG Chatbot")

st.caption(
    "Gemini 3.8 Flash + LangGraph + "
    "PostgreSQL Memory + Pinecone"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # DOCUMENT UPLOAD
    # --------------------------------------------------------

    st.header("📄 Upload Document")

    uploaded_file = st.file_uploader(
        "Upload PDF, DOCX or TXT",
        type=["pdf", "docx", "txt"],
        help="Upload a document to ask questions about it.",
    )

    if (
        uploaded_file is not None
        and uploaded_file.name
        not in st.session_state.uploaded_files
    ):

        os.makedirs(
            UPLOAD_DIRECTORY,
            exist_ok=True,
        )

        file_path = os.path.join(
            UPLOAD_DIRECTORY,
            uploaded_file.name,
        )

        try:

            # Save uploaded file
            with open(file_path, "wb") as file:
                file.write(uploaded_file.getbuffer())

            # Ingest into PostgreSQL
            with st.spinner("Processing document..."):
                document_id = ingest_document(file_path)

            # Get chunks belonging to this document
            from index_documents import get_chunks

            all_chunks = get_chunks()

            document_chunks = [
                chunk
                for chunk in all_chunks
                if chunk["document_id"] == document_id
            ]

            # Create embeddings and store in Pinecone
            if document_chunks:

                with st.spinner(
                    "Creating document embeddings..."
                ):
                    indexed_count = upsert_chunks(
                        document_chunks
                    )

                st.success(
                    f"'{uploaded_file.name}' "
                    f"uploaded successfully."
                )

                st.caption(
                    f"{indexed_count} chunk(s) indexed."
                )

            else:
                st.warning(
                    "No text could be extracted "
                    "from this document."
                )

            st.session_state.uploaded_files.append(
                uploaded_file.name
            )

        except Exception as e:
            st.error(
                f"Document processing failed: {e}"
            )

    st.divider()

    # --------------------------------------------------------
    # SYSTEM STATUS
    # --------------------------------------------------------

    st.header("⚙️ System Status")

    st.success("🟢 Gemini 2.5 Flash")
    st.success("🟢 LangGraph")
    st.success("🟢 PostgreSQL Memory")
    st.success("🟢 Pinecone")
    st.success("🟢 Semantic Search")

    st.divider()

    # --------------------------------------------------------
    # CONVERSATIONS
    # --------------------------------------------------------

    st.header("💬 Conversations")

    st.caption("Current Thread ID")

    st.code(
        st.session_state.thread_id,
        language=None,
    )

    threads = get_threads()

    previous_threads = [
        thread
        for thread in threads
        if thread["thread_id"]
        != st.session_state.thread_id
    ]

    if previous_threads:

        st.subheader("Previous Chats")

        for thread in previous_threads:

            thread_id = thread["thread_id"]
            title = thread["title"]

            if st.button(
                title,
                key=f"thread_{thread_id}",
                use_container_width=True,
            ):

                st.session_state.thread_id = thread_id

                langgraph_messages = load_thread(
                    thread_id
                )

                st.session_state.messages = (
                    convert_messages(
                        langgraph_messages
                    )
                )

                st.rerun()

    else:
        st.caption(
            "No previous conversations yet."
        )

    st.divider()

    # --------------------------------------------------------
    # NEW CONVERSATION
    # --------------------------------------------------------

    if st.button(
        "🆕 New Conversation",
        use_container_width=True,
    ):

        st.session_state.thread_id = (
            create_new_thread()
        )

        st.session_state.messages = []

        st.rerun()


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message["role"] == "assistant":

            source = message.get("source")

            if source == "document":
                st.caption(
                    "📄 From uploaded document"
                )

            elif source == "general":
                st.caption(
                    "🌐 General knowledge"
                )

        st.markdown(
            message["content"]
        )


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Ask me anything..."
)


if user_input:

    # --------------------------------------------------------
    # SAVE USER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    # --------------------------------------------------------
    # UPDATE THREAD TITLE
    # --------------------------------------------------------

    current_threads = get_threads()

    current_thread = next(
        (
            thread
            for thread in current_threads
            if thread["thread_id"]
            == st.session_state.thread_id
        ),
        None,
    )

    if (
        current_thread
        and current_thread["title"]
        == "New Conversation"
    ):

        update_thread_title(
            thread_id=st.session_state.thread_id,
            title=generate_thread_title(
                user_input
            ),
        )

    # --------------------------------------------------------
    # DISPLAY USER MESSAGE
    # --------------------------------------------------------

    with st.chat_message("user"):
        st.markdown(user_input)

    # --------------------------------------------------------
    # RETRIEVE DOCUMENT CONTEXT
    # --------------------------------------------------------

    try:

        results = semantic_search(
            user_input,
            top_k=5,
        )

    except Exception as e:

        results = []

        st.warning(
            f"Document search unavailable: {e}"
        )

    context, source = build_document_context(
        results
    )

    # --------------------------------------------------------
    # LANGGRAPH CONFIG
    # --------------------------------------------------------

    config = {
        "configurable": {
            "thread_id":
                st.session_state.thread_id
        }
    }

    input_state = {
        "messages": [
            HumanMessage(
                content=user_input
            )
        ],
        "context": context,
    }

    # --------------------------------------------------------
    # ASSISTANT RESPONSE
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        if source == "document":
            st.caption(
                "📄 From uploaded document"
            )
        else:
            st.caption(
                "🌐 General knowledge"
            )

        response_placeholder = st.empty()

        full_response = ""

        try:

            for message_chunk, metadata in graph.stream(
                input_state,
                config=config,
                stream_mode="messages",
            ):

                if (
                    metadata.get("langgraph_node")
                    != "chatbot"
                ):
                    continue

                # Gemini content may be str or list.
                chunk_text = extract_text(
                    message_chunk.content
                )

                if not chunk_text:
                    continue

                full_response += chunk_text

                response_placeholder.markdown(
                    full_response
                )

            if not full_response:

                full_response = (
                    "I couldn't generate a response."
                )

                response_placeholder.markdown(
                    full_response
                )

        except Exception as e:

            full_response = (
                f"An error occurred: {e}"
            )

            response_placeholder.error(
                full_response
            )

    # --------------------------------------------------------
    # SAVE ASSISTANT RESPONSE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response,
            "source": source,
        }
    )

    # Update conversation ordering
    touch_thread(
        st.session_state.thread_id
    )