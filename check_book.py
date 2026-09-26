import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:1234@localhost:5432/litsense_db')
df = pd.read_sql("SELECT title, authors FROM books_metadata WHERE title ILIKE '%Atomic Habits%'", engine)
if not df.empty:
    print(df)
else:
    print("Not found in the 100k sample.")
