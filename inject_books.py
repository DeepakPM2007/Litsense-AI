import pandas as pd
from sqlalchemy import create_engine, text
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# Hardcoded high-quality data to ensure the presentation works flawlessly
books_to_add = [
    {
        "book_id": "demo_1",
        "title": "Atomic Habits: An Easy & Proven Way to Build Good Habits & Break Bad Ones",
        "authors": "James Clear",
        "categories": "Self-Help, Personal Development",
        "description": "No matter your goals, Atomic Habits offers a proven framework for improving--every day. James Clear, one of the world's leading experts on habit formation, reveals practical strategies that will teach you exactly how to form good habits, break bad ones, and master the tiny behaviors that lead to remarkable results.",
        "thumbnail": "https://covers.openlibrary.org/b/id/12886417-L.jpg",
        "published_year": 2018,
        "average_rating": 4.8,
        "ratings_count": 150000,
        "num_pages": 320
    },
    {
        "book_id": "demo_2",
        "title": "Spring Boot in Action",
        "authors": "Craig Walls",
        "categories": "Computers, Programming, Java",
        "description": "Spring Boot in Action is a developer-focused guide to writing applications using Spring Boot. In it, you'll learn how to bypass configuration steps so you can focus on your application's behavior. Spring expert Craig Walls uses interesting and practical examples to teach you both how to use the default settings effectively and how to override and customize Spring Boot for your unique environment.",
        "thumbnail": "https://covers.openlibrary.org/b/id/7996503-L.jpg",
        "published_year": 2015,
        "average_rating": 4.5,
        "ratings_count": 5000,
        "num_pages": 288
    },
    {
        "book_id": "demo_3",
        "title": "Spring in Action, Sixth Edition",
        "authors": "Craig Walls",
        "categories": "Computers, Programming, Java",
        "description": "If you need to learn Spring, look no further than this widely beloved and comprehensive guide! Fully revised for Spring 5.3, and packed with interesting real-world examples to get your hands dirty with Spring. In Spring in Action, 6th Edition you will learn: Building reactive applications, Relational and NoSQL databases, Integrating via HTTP and REST-based services, and securing applications with Spring Security.",
        "thumbnail": "https://covers.openlibrary.org/b/id/12690967-L.jpg",
        "published_year": 2022,
        "average_rating": 4.7,
        "ratings_count": 3000,
        "num_pages": 520
    },
    {
        "book_id": "demo_4",
        "title": "Cloud Native Spring in Action",
        "authors": "Thomas Vitale",
        "categories": "Computers, Programming, Java, Cloud Computing",
        "description": "Cloud Native Spring in Action teaches you how to build robust web applications, integrate with RESTful services, and deploy to Kubernetes using Spring Boot. You'll master essential techniques like containerization with Docker and robust error handling.",
        "thumbnail": "https://covers.openlibrary.org/b/id/12781488-L.jpg",
        "published_year": 2023,
        "average_rating": 4.6,
        "ratings_count": 1200,
        "num_pages": 450
    },
    {
        "book_id": "demo_5",
        "title": "Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow",
        "authors": "Aurélien Géron",
        "categories": "Computers, Artificial Intelligence, Machine Learning",
        "description": "Through a series of recent breakthroughs, deep learning has boosted the entire field of machine learning. Now, even programmers who know close to nothing about this technology can use simple, efficient tools to implement programs capable of learning from data. This practical book shows you how.",
        "thumbnail": "https://covers.openlibrary.org/b/id/12836242-L.jpg",
        "published_year": 2022,
        "average_rating": 4.9,
        "ratings_count": 12000,
        "num_pages": 856
    }
]

df_new = pd.DataFrame(books_to_add)

print(f"Injecting {len(df_new)} perfect tech & modern books into PostgreSQL...")
DATABASE_URL = "postgresql://postgres:1234@localhost:5432/litsense_db"
engine = create_engine(DATABASE_URL)
# Delete these IDs first just in case we ran this before
with engine.connect() as conn:
    conn.execute(text("DELETE FROM books_metadata WHERE book_id LIKE 'demo_%'"))
    conn.commit()
    
df_new.to_sql("books_metadata", engine, if_exists="append", index=False)

print("Injecting into ChromaDB...")
client = chromadb.PersistentClient(path="./chroma_db")
embedding_func = SentenceTransformerEmbeddingFunction(
    model_name=r"D:\LLM Models\all-MiniLM-L6-v2",
    device="cuda"
)
collection = client.get_collection("books_catalog", embedding_function=embedding_func)

documents = df_new.apply(
    lambda row: f"Title: {row['title']}. Genre/Category: {row['categories']}. Synopsis: {row['description']}", 
    axis=1
).tolist()
ids = df_new["book_id"].tolist()
metadatas = df_new.apply(lambda row: {
    "title": row["title"],
    "authors": row["authors"],
    "categories": row["categories"]
}, axis=1).tolist()

collection.add(documents=documents, metadatas=metadatas, ids=ids)

print("Successfully injected modern books into your Recommendation Engine!")
