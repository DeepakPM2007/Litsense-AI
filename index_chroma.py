import pandas as pd
from sqlalchemy import create_engine
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import math

# 1. Load metadata directly from PostgreSQL
DATABASE_URL = "postgresql://postgres:1234@localhost:5432/litsense_db"
engine = create_engine(DATABASE_URL)

print("Fetching records from PostgreSQL...")
df = pd.read_sql("SELECT book_id, title, authors, categories, description FROM books_metadata", engine)

# 2. Initialize ChromaDB
print("Initializing ChromaDB and loading the local embedding model...")
client = chromadb.PersistentClient(path="./chroma_db")

# Point to your local model directory and utilize the dedicated GPU for fast computation
embedding_func = SentenceTransformerEmbeddingFunction(
    model_name=r"D:\LLM Models\all-MiniLM-L6-v2",
    device="cuda"
)

# We delete the old collection to avoid mixing old data with the new dataset
try:
    client.delete_collection(name="books_catalog")
    print("Deleted old 'books_catalog' collection.")
except:
    pass

collection = client.get_or_create_collection(
    name="books_catalog",
    embedding_function=embedding_func
)

# 3. Prepare the payload arrays for ChromaDB
# --- THE AI ENGINEERING UPGRADE: RICH DOCUMENT EMBEDDING ---
# We concatenate Title + Category + Description so the vector captures deep context
print("Creating Rich Document Embeddings...")
documents = df.apply(
    lambda row: f"Title: {row['title']}. Genre/Category: {row['categories']}. Synopsis: {row['description']}", 
    axis=1
).tolist()

ids = df["book_id"].tolist()
metadatas = df.apply(lambda row: {
    "title": row["title"],
    "authors": row["authors"],
    "categories": row["categories"]
}, axis=1).tolist()

# 4. Insert into ChromaDB in batches to manage memory efficiently
batch_size = 1000
total_batches = math.ceil(len(df) / batch_size)

print(f"Embedding and indexing {len(df)} records into ChromaDB. This may take 5-15 minutes on GPU...")
for i in range(total_batches):
    start_idx = i * batch_size
    end_idx = min((i + 1) * batch_size, len(df))

    collection.add(
        documents=documents[start_idx:end_idx],
        metadatas=metadatas[start_idx:end_idx],
        ids=ids[start_idx:end_idx]
    )
    print(f"Processed batch {i + 1}/{total_batches}")

print("Vector database indexing complete! ChromaDB is ready.")