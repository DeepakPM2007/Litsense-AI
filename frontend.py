import streamlit as st
import requests

# API Base URL
API_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="LitSense AI", page_icon="📚", layout="wide")

st.title("📚 LitSense AI Recommendation Engine")
st.markdown("Your personal AI-powered book sommelier.")

# Sidebar navigation
mode = st.sidebar.radio(
    "Choose Discovery Mode:",
    ["🔍 Semantic Search", "🎓 Learning Pathway", "🍷 Book Sommelier Chat"]
)

def display_books(books):
    if not books:
        st.warning("No books found.")
        return
    
    cols = st.columns(len(books) if len(books) <= 4 else 4)
    for idx, book in enumerate(books):
        with cols[idx % 4]:
            st.image(book.get("thumbnail") or "https://via.placeholder.com/150", use_container_width=True)
            st.markdown(f"**{book.get('title')}**")
            st.caption(f"By {book.get('authors')}")
            with st.expander("Synopsis"):
                st.write(book.get("description", "No description available."))
            
            # Simple item-to-item similarity trigger (bonus feature)
            if st.button("More like this", key=f"similar_{book['book_id']}_{idx}"):
                st.session_state["search_mode"] = "similar"
                st.session_state["target_book_id"] = book["book_id"]
                st.rerun()

# ----------------- MODE 1: SEMANTIC SEARCH -----------------
if mode == "🔍 Semantic Search":
    st.header("Search by Vibe or Topic")
    query = st.text_input("What are you in the mood for?", placeholder="e.g., 'A gritty sci-fi novel about space politics'")
    
    # Handle "More like this" button click from previous renders
    if st.session_state.get("search_mode") == "similar" and st.session_state.get("target_book_id"):
        target_id = st.session_state["target_book_id"]
        st.info(f"Finding books similar to ID: {target_id}")
        with st.spinner("Analyzing vectors..."):
            res = requests.get(f"{API_URL}/recommend/similar/{target_id}?top_k=4")
            if res.status_code == 200:
                data = res.json()
                st.success("Here are similar books:")
                display_books(data.get("results", []))
        if st.button("Clear Similarity Search"):
            st.session_state["search_mode"] = None
            st.rerun()

    elif query:
        with st.spinner("LitSense AI is searching..."):
            res = requests.post(f"{API_URL}/recommend/semantic", json={"prompt": query, "top_k": 4})
            if res.status_code == 200:
                data = res.json()
                st.info(f"**AI Explanation:** {data.get('ai_explanation')}")
                display_books(data.get("results", []))
            else:
                st.error("Error connecting to backend API.")

# ----------------- MODE 2: LEARNING PATHWAY -----------------
elif mode == "🎓 Learning Pathway":
    st.header("Generate a Learning Curriculum")
    topic = st.text_input("What do you want to master?", placeholder="e.g., 'Artificial Intelligence', 'Personal Finance'")
    
    if topic:
        with st.spinner("AI is structuring your curriculum..."):
            res = requests.post(f"{API_URL}/recommend/pathway", json={"topic": topic})
            if res.status_code == 200:
                data = res.json()
                st.success("Pathway Generated!")
                st.markdown(f"### The Curriculum\n{data.get('pathway_explanation')}")
                st.markdown("### The Books")
                display_books(data.get("results", []))
            else:
                st.error("Make sure the backend is running and the new endpoint is deployed.")

# ----------------- MODE 3: BOOK SOMMELIER CHAT -----------------
elif mode == "🍷 Book Sommelier Chat":
    st.header("Chat with the Sommelier")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am the LitSense AI Sommelier. Tell me about the last book you loved, or what you're trying to learn today!"}
        ]
        
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "books" in message:
                display_books(message["books"])
                
    if prompt := st.chat_input("Ask for a recommendation..."):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                res = requests.post(f"{API_URL}/recommend/chat", json={
                    "chat_history": st.session_state.messages,
                    "latest_query": prompt
                })
                
                if res.status_code == 200:
                    data = res.json()
                    bot_reply = data.get("reply")
                    books = data.get("results", [])
                    
                    st.markdown(bot_reply)
                    if books:
                        display_books(books)
                        
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply, "books": books})
                else:
                    st.error("Error communicating with AI Sommelier.")
