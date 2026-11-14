import os
import time

import mariadb
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_mariadb import MariaDBStore
from sqlalchemy import URL, create_engine

load_dotenv()

host=os.environ["DB_HOST"]
port=int(os.environ["DB_PORT"])
user=os.environ["DB_USER"]
password=os.environ["DB_PASSWORD"]
db=os.environ["DB_NAME"]

connection = mariadb.connect(
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    db=os.environ["DB_NAME"],
    ssl=True,
)

engine = create_engine(
    URL.create(
        "mariadb+mariadbconnector",
        username=user,
        password=password,
        host=host,
        port=port,
        database=db,
    ),
    connect_args={"ssl": True},
)

vector_store = MariaDBStore(embeddings=GoogleGenerativeAIEmbeddings(model="gemini-embedding-001"),
                            embedding_length=3072,
                            datasource=engine,
                            collection_name="Product names"
                            )

# Free tier do Gemini: 100 textos/min para embeddings
INGEST_BATCH_SIZE = 90

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

@app.post("/products/ingest")
def ingest_product():
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM products;")
    products = [name for (name,) in cursor]
    for i in range(0, len(products), INGEST_BATCH_SIZE):
        if i > 0:
            time.sleep(60)
        vector_store.add_texts(products[i:i + INGEST_BATCH_SIZE])
    return "Ingestion complete"