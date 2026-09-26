import os
import pandas as pd
from sqlalchemy import create_engine
import numpy as np

# 1. Load into Pandas directly from the extracted CSV
print("Loading local CSV into Pandas...")
full_csv_path = "books_data.csv"
df = pd.read_csv(full_csv_path)
print("Initial shape:", df.shape)

# 3. Clean essential columns
# The Amazon dataset uses 'Title', 'description', 'authors', 'categories', 'image'
df = df.rename(columns={
    "Title": "title",
    "image": "thumbnail",
    "ratingsCount": "ratings_count"
})

# Drop rows where essential data is missing
df = df.dropna(subset=["title", "description", "categories"])

# Fill optional missing values
df["categories"] = df["categories"].fillna("['Uncategorized']")
df["authors"] = df["authors"].fillna("['Unknown']")
df["thumbnail"] = df["thumbnail"].fillna("")

# Clean up the string representation of lists in Amazon dataset (e.g., "['Fiction']")
df["categories"] = df["categories"].str.replace(r"[\[\]']", "", regex=True)
df["authors"] = df["authors"].str.replace(r"[\[\]']", "", regex=True)

# Extract published year from publishedDate (e.g., "1998-05-01" -> 1998)
df["published_year"] = df["publishedDate"].str.extract(r'(\d{4})').fillna(0).astype(int)

# 4. Smart Sampling (Optional but recommended for speed)
# Let's sample 100,000 diverse books to keep processing fast while maintaining variety
if len(df) > 100000:
    print(f"Sampling 100,000 books from {len(df)} available...")
    df = df.sample(n=100000, random_state=42)

# Generate unique book_id
df["book_id"] = [f"amz_{i}" for i in range(len(df))]
df = df.drop_duplicates(subset=["title"])

print("Cleaned shape:", df.shape)

# 5. Save to PostgreSQL
print("Connecting to PostgreSQL...")
# Replace '1234' with your actual pgAdmin password if different
DATABASE_URL = "postgresql://postgres:1234@localhost:5432/litsense_db"
engine = create_engine(DATABASE_URL)

db_df = pd.DataFrame({
    "book_id": df["book_id"],
    "title": df["title"],
    "authors": df["authors"],
    "categories": df["categories"],
    "description": df["description"],
    "thumbnail": df["thumbnail"],
    "published_year": df["published_year"],
    "average_rating": 0.0, # Amazon dataset in this file doesn't have avg rating easily accessible without joining
    "ratings_count": pd.to_numeric(df.get("ratings_count", 0), errors="coerce").fillna(0).astype(int),
    "num_pages": 0 # Not available in this specific CSV, defaulting to 0
})

# We use if_exists="replace" here so we don't mix the old 7k dataset with the new Amazon one
print("Writing to PostgreSQL database (this might take a minute)...")
db_df.to_sql("books_metadata", engine, if_exists="replace", index=False)
print(f"Successfully inserted {len(db_df)} records into PostgreSQL!")