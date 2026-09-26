# 📚 LitSense AI Recommendation Engine

LitSense AI is an intelligent, RAG-augmented book recommendation engine and learning pathway generator. It moves beyond simple keyword matching by using vector embeddings to understand the true semantic "vibe" of a user's request, and pairs it with Generative AI to provide conversational recommendations.

## ✨ Features

*   **🔍 Semantic "Vibe" Search:** Search for books based on abstract concepts, moods, or specific technical topics. (e.g., *"A gritty sci-fi novel about space politics"*).
*   **🎓 Learning Pathway Generator:** Selects a progressive curriculum of books (Beginner, Intermediate, Advanced) and uses AI to explain how to study them.
*   **🍷 Book Sommelier Chatbot:** A conversational agent that remembers chat history, gracefully handles small talk, and recommends books based on evolving context.
*   **🎨 Custom SPA Frontend:** A sleek, Netflix-style Single Page Application built with vanilla HTML/CSS/JS, fully integrated into the backend.

## 🛠️ Tech Stack

*   **Backend:** FastAPI (Python)
*   **Database:** PostgreSQL (Metadata storage)
*   **Vector Store:** ChromaDB (Semantic search embeddings)
*   **Embeddings:** `all-MiniLM-L6-v2` (SentenceTransformers)
*   **Generative AI:** `Llama-3.2-3B-Instruct` (Local LLM via Hugging Face Pipeline)
*   **Frontend:** Vanilla JS, CSS (Design Tokens), HTML

## 🚀 How to Run Locally

### Prerequisites
1.  Python 3.10+
2.  PostgreSQL running locally (Database name: `litsense_db`)
3.  A dedicated GPU (CUDA) is highly recommended for running the local Llama 3.2 model and generating vector embeddings.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/DeepakPM2007/Litsense-AI.git
    cd Litsense-AI
    ```

2.  **Install dependencies:**
    *(Ensure you have PyTorch installed with CUDA support)*
    ```bash
    pip install fastapi uvicorn chromadb pandas sqlalchemy psycopg2-binary sentence-transformers transformers accelerate bitsandbytes
    ```

3.  **Populate the Database:**
    You can use the provided data scripts to inject books into Postgres and ChromaDB.
    ```bash
    python inject_books.py
    ```

4.  **Start the Server:**
    ```bash
    uvicorn main:app --reload
    ```

5.  **Access the UI:**
    Open your web browser and navigate to `http://localhost:8000`. The backend will automatically serve the custom web interface.

---
*Developed as an Advanced AI/ML Mini-Project.*
