from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from sqlalchemy import create_engine, text
import pandas as pd
from typing import List, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline

app = FastAPI(title="LitSense AI Recommendation Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the static UI files
app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")

@app.get("/", include_in_schema=False)
def redirect_to_ui():
    return RedirectResponse(url="/ui")

DATABASE_URL = "postgresql://postgres:1234@localhost:5432/litsense_db"
engine = create_engine(DATABASE_URL)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_func = SentenceTransformerEmbeddingFunction(
    model_name=r"D:\LLM Models\all-MiniLM-L6-v2",
    device="cuda"
)
collection = chroma_client.get_collection("books_catalog", embedding_function=embedding_func)

# --- NEW: LLAMA 3.2 INITIALIZATION ---
print("Loading Llama 3.2 3B Instruct into VRAM (4-bit)...")
llama_path = r"D:\LLM Models\Llama-3.2-3B-Instruct"

quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

tokenizer = AutoTokenizer.from_pretrained(llama_path)
llm_model = AutoModelForCausalLM.from_pretrained(
    llama_path,
    device_map="auto",
    quantization_config=quant_config
)
# Use pipeline for easy text generation
llm_generator = pipeline("text-generation", model=llm_model, tokenizer=tokenizer)


class SemanticSearchRequest(BaseModel):
    prompt: str
    top_k: int = 3  # Lowered default to 3 to keep LLM generation fast


def fetch_books_from_db(book_ids: List[str]) -> List[dict]:
    if not book_ids: return []

    query = text("""
            SELECT book_id, title, authors, categories, description, thumbnail, average_rating, published_year, num_pages
            FROM books_metadata WHERE book_id = ANY(:book_ids)
        """)

    with engine.connect() as conn:
        df_results = pd.read_sql(query, conn, params={"book_ids": book_ids})

    book_dict = {}
    for row in df_results.to_dict(orient="records"):
        # Convert any NaN values to None for JSON compliance
        clean_row = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        book_dict[clean_row["book_id"]] = clean_row

    return [book_dict[b_id] for b_id in book_ids if b_id in book_dict]

# --- NEW: AI EXPLANATION GENERATOR ---
def generate_ai_explanation(user_query: str, books: List[dict]) -> str:
    if not books: return "No books found."

    titles = ", ".join([f"'{b['title']}'" for b in books])

    # Llama 3.2 prompt template
    system_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are LitSense AI, a smart book recommender. The user asked for: '{user_query}'. 
You found these books: {titles}. 
Write one concise, engaging paragraph (under 50 words) explaining why these specific books match their request.<|eot_id|><|start_header_id|>user<|end_header_id|>
Explain the recommendations.<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

    output = llm_generator(
        system_prompt,
        max_new_tokens=200,
        return_full_text=False,
        temperature=0.6
    )
    return output[0]['generated_text'].strip()


# --- API ROUTES ---
@app.post("/api/v1/recommend/semantic", tags=["Recommendations"])
def recommend_by_prompt(payload: SemanticSearchRequest):
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Search prompt cannot be empty.")

    results = collection.query(query_texts=[payload.prompt], n_results=payload.top_k)
    matched_ids = results["ids"][0] if results["ids"] else []
    recommendations = fetch_books_from_db(matched_ids)

    ai_summary = generate_ai_explanation(payload.prompt, recommendations)

    return {
        "mode": "semantic_prompt",
        "query": payload.prompt,
        "ai_explanation": ai_summary,
        "count": len(recommendations),
        "results": recommendations
    }


class PathwayRequest(BaseModel):
    topic: str

@app.post("/api/v1/recommend/pathway", tags=["Recommendations"])
def generate_pathway(payload: PathwayRequest):
    if not payload.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    # 1. Fetch exactly 3 books for the pathway
    results = collection.query(query_texts=[payload.topic], n_results=3)
    matched_ids = results["ids"][0] if results["ids"] else []
    recommendations = fetch_books_from_db(matched_ids)

    if len(recommendations) < 3:
         return {"pathway_explanation": "Not enough books found for this topic to create a pathway.", "results": recommendations}

    # Extract titles for the prompt
    title_1 = recommendations[0]['title']
    title_2 = recommendations[1]['title']
    title_3 = recommendations[2]['title']
    
    # 2. Ask LLM to structure a pathway using exactly these 3 books
    system_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are LitSense AI, a curriculum designer. The user wants to learn about '{payload.topic}'.
I have selected these 3 books for them:
1. {title_1}
2. {title_2}
3. {title_3}

Write a short, engaging learning pathway explaining how the user should read these 3 books in order, starting with the first as an introduction and ending with the third as advanced material.<|eot_id|><|start_header_id|>user<|end_header_id|>
Create the pathway.<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
    output = llm_generator(system_prompt, max_new_tokens=300, return_full_text=False, temperature=0.7)
    pathway_explanation = output[0]['generated_text'].strip()

    # Return exactly the 3 books we asked it to write about
    return {
        "topic": payload.topic,
        "pathway_explanation": pathway_explanation,
        "results": recommendations 
    }


class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    chat_history: List[ChatMessage]
    latest_query: str

@app.post("/api/v1/recommend/chat", tags=["Chatbot"])
def sommelier_chat(payload: ChatRequest):
    query_lower = payload.latest_query.strip().lower()
    words = query_lower.split()
    
    # 1. Simple heuristic for small talk/greetings
    chit_chat_words = {"hi", "hello", "hey", "hola", "greetings", "thanks", "thank you", "bye", "goodbye", "sup", "yo"}
    
    # If the user typed a very short message that looks like a greeting
    is_chit_chat = False
    if len(words) <= 4 and any(w in chit_chat_words for w in words):
        is_chit_chat = True
    
    recommendations = []
    titles = ""
    
    # 2. Only search the database if it's an actual book request
    if not is_chit_chat:
        results = collection.query(query_texts=[payload.latest_query], n_results=4)
        matched_ids = results["ids"][0] if results["ids"] else []
        recommendations = fetch_books_from_db(matched_ids)
        titles = ", ".join([f"'{b['title']}'" for b in recommendations]) if recommendations else "No matching books."

    # 3. Build conversational prompt for Llama 3.2
    prompt_str = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
    prompt_str += "You are LitSense AI, a friendly and professional book sommelier.\n"
    
    if is_chit_chat:
        prompt_str += "The user is just chatting or saying hello. Respond politely and ask them what kind of books or topics they are in the mood for today. Do not recommend any books yet.\n"
    else:
        prompt_str += f"Context: Database search returned these books: {titles}.\n"
        prompt_str += "Provide a brief, helpful, conversational response recommending these books. Keep it under 60 words.\n"
        
    prompt_str += "<|eot_id|>"
    
    # Add recent chat history (limit to last 4 messages to save context)
    recent_history = payload.chat_history[-4:]
    for msg in recent_history:
        prompt_str += f"<|start_header_id|>{msg.role}<|end_header_id|>\n{msg.content}<|eot_id|>"
        
    prompt_str += "<|start_header_id|>assistant<|end_header_id|>\n"

    output = llm_generator(prompt_str, max_new_tokens=150, return_full_text=False, temperature=0.7)
    reply = output[0]['generated_text'].strip()

    return {
        "reply": reply,
        "results": recommendations
    }


# (Keep your existing GET /api/v1/books and GET /api/v1/recommend/similar routes here)


@app.get("/api/v1/recommend/similar/{book_id}", tags=["Recommendations"])
def recommend_similar_books(book_id: str, top_k: int = Query(5, ge=1, le=20)):
    """Mode 2: 'More Like This' item-to-item similarity."""
    # Retrieve the source book's vector directly from ChromaDB
    existing = collection.get(ids=[book_id], include=["embeddings"])
    embeddings = existing.get("embeddings")

    if embeddings is None or len(embeddings) == 0:
        raise HTTPException(status_code=404, detail="Book not found in vector catalog.")

    source_vector = embeddings[0]

    # Query nearest neighbors (requesting top_k + 1 to exclude itself)
    results = collection.query(
        query_embeddings=[source_vector],
        n_results=top_k + 1
    )

    all_matched = results["ids"][0] if results["ids"] else []
    filtered_ids = [b_id for b_id in all_matched if str(b_id) != str(book_id)][:top_k]
    recommendations = fetch_books_from_db(filtered_ids)

    return {
        "mode": "book_to_book_similarity",
        "source_book_id": book_id,
        "count": len(recommendations),
        "results": recommendations
    }