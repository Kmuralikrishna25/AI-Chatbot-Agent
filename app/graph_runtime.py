import os

import streamlit as st
import psycopg

from dotenv import load_dotenv
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver

from .graph import build_graph


load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. "
        "Please check your .env file."
    )


@st.cache_resource
def get_graph():

    # Create a persistent PostgreSQL connection.
    connection = psycopg.connect(
        DATABASE_URL,
        autocommit=True,
        prepare_threshold=0,
        row_factory=dict_row,
    )

    # Create the LangGraph PostgreSQL checkpointer
    checkpointer = PostgresSaver(
        connection
    )

    # Create checkpoint tables if necessary
    checkpointer.setup()

    # Build LangGraph with PostgreSQL memory
    graph = build_graph(
        checkpointer
    )

    return graph


graph = get_graph()