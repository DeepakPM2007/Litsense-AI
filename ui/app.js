const API_BASE = "http://localhost:8000/api/v1";

// Navigation
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
        
        e.target.classList.add('active');
        const targetId = e.target.getAttribute('data-target');
        document.getElementById(targetId).classList.add('active');
    });
});

// Helper: Render Books
function renderBooks(books, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    books.forEach(book => {
        const fallbackImg = "https://via.placeholder.com/200x300?text=No+Cover";
        const img = book.thumbnail ? book.thumbnail : fallbackImg;
        container.innerHTML += `
            <div class="book-card">
                <img src="${img}" alt="${book.title}" onerror="this.src='${fallbackImg}'">
                <div class="book-info">
                    <h3 class="book-title">${book.title}</h3>
                    <div class="book-author">${book.authors}</div>
                    <div class="book-desc">${book.description || "No description available."}</div>
                </div>
            </div>
        `;
    });
}

// 1. Semantic Search
document.getElementById('semantic-btn').addEventListener('click', async () => {
    const prompt = document.getElementById('semantic-input').value;
    if(!prompt) return;

    document.getElementById('semantic-loading').style.display = 'block';
    document.getElementById('semantic-explanation').style.display = 'none';
    document.getElementById('semantic-results').innerHTML = '';

    try {
        const res = await fetch(`${API_BASE}/recommend/semantic`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({prompt: prompt, top_k: 4})
        });
        const data = await res.json();
        
        document.getElementById('semantic-loading').style.display = 'none';
        
        const expl = document.getElementById('semantic-explanation');
        expl.style.display = 'block';
        expl.innerText = data.ai_explanation;
        
        renderBooks(data.results, 'semantic-results');
    } catch(err) {
        console.error(err);
        document.getElementById('semantic-loading').innerText = "An error occurred.";
    }
});

// 2. Learning Pathway
document.getElementById('pathway-btn').addEventListener('click', async () => {
    const topic = document.getElementById('pathway-input').value;
    if(!topic) return;

    document.getElementById('pathway-loading').style.display = 'block';
    document.getElementById('pathway-explanation').style.display = 'none';
    document.getElementById('pathway-results').innerHTML = '';

    try {
        const res = await fetch(`${API_BASE}/recommend/pathway`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({topic: topic})
        });
        const data = await res.json();
        
        document.getElementById('pathway-loading').style.display = 'none';
        
        const expl = document.getElementById('pathway-explanation');
        expl.style.display = 'block';
        expl.innerText = data.pathway_explanation;
        
        renderBooks(data.results, 'pathway-results');
    } catch(err) {
        console.error(err);
    }
});

// 3. Chat Sommelier
let chatHistory = [];
document.getElementById('chat-btn').addEventListener('click', async () => {
    const input = document.getElementById('chat-input');
    const msg = input.value;
    if(!msg) return;

    const historyContainer = document.getElementById('chat-history');
    
    // Add user message to UI
    historyContainer.innerHTML += `<div class="chat-msg user">${msg}</div>`;
    input.value = '';

    // Create a temporary loading message
    const loadingId = "load-" + Date.now();
    historyContainer.innerHTML += `<div class="chat-msg assistant" id="${loadingId}">Thinking...</div>`;
    historyContainer.scrollTop = historyContainer.scrollHeight;

    try {
        const res = await fetch(`${API_BASE}/recommend/chat`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                chat_history: chatHistory,
                latest_query: msg
            })
        });
        const data = await res.json();
        
        // Remove loading
        document.getElementById(loadingId).remove();

        // Add assistant reply to UI
        historyContainer.innerHTML += `<div class="chat-msg assistant">${data.reply}</div>`;
        
        // Render books in chat if any
        if (data.results && data.results.length > 0) {
            const gridId = "grid-" + Date.now();
            historyContainer.innerHTML += `<div id="${gridId}" class="books-grid"></div>`;
            renderBooks(data.results, gridId);
        }
        
        historyContainer.scrollTop = historyContainer.scrollHeight;

        // Save to history
        chatHistory.push({role: "user", content: msg});
        chatHistory.push({role: "assistant", content: data.reply});
        
    } catch(err) {
        console.error(err);
        document.getElementById(loadingId).innerText = "An error occurred.";
    }
});
