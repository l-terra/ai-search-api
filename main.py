import os

import mariadb
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

connection = mariadb.connect(
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    db=os.environ["DB_NAME"],
    ssl=True,
)

app = FastAPI()

@app.get("/products/text-search")
def text_search(query: str):
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT name 
        FROM products 
        ORDER BY MATCH(name) AGAINST(?)
        LIMIT 10;
        """, (query,)
    )
    return [name for (name,) in cursor]
