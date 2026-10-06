import os

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. "
        "Please add it to your .env file."
    )

#setup langraph postgres chseckpoint tables

with PostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:

    checkpointer.setup()

    print("LangGraph PostgreSQL tables created successfully!")