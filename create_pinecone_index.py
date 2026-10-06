import os

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec


load_dotenv()


API_KEY = os.getenv("PINECONE_API_KEY")

INDEX_NAME = "ai-chatbot-rag-384"


if not API_KEY:
    raise ValueError(
        "PINECONE_API_KEY is not set. "
        "Please check your .env file."
    )


pc = Pinecone(api_key=API_KEY)


existing_indexes = [
    index["name"]
    for index in pc.list_indexes()
]


if INDEX_NAME in existing_indexes:

    print(f"Index '{INDEX_NAME}' already exists.")

else:

    print(f"Creating index: {INDEX_NAME}")

    pc.create_index(
        name=INDEX_NAME,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

    print("Index creation requested.")


print("\nAvailable Pinecone indexes:")

for index in pc.list_indexes():
    print(f"- {index['name']}")