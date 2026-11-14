# ai-search-api

A small FastAPI service that compares two ways of searching a product catalog stored in MariaDB:

- **Full-text search**: the classic keyword search, using MariaDB `FULLTEXT` indexes and `MATCH ... AGAINST`.
- **Vector search**: semantic search, using Google Gemini embeddings stored in MariaDB's native vector type through LangChain.

The catalog has 500 outdoor-gear products. Searching it both ways shows where keyword search breaks down.

## Keyword vs. meaning

The same query, `running shoes`, against both endpoints:

| `/products/text-search` | `/products/vector-search` |
|---|---|
| `[]` | SummitForge RiftRunner Trail Shoe |
| | SkyLevel Alta Run GTX |
| | SkyLevel Alta Runner Knit |
| | BluePeak RidgeGrip Shoe LV |
| | Horizon Trail Pace Runner GTX |
| | ... |

Full-text search returns nothing because no product name contains the exact words `running` or `shoes`. The catalog uses `Shoe`, `Run` and `Runner`, and `FULLTEXT` treats each of those as a different word. Vector search compares meaning instead of spelling, so it finds the running shoes anyway.

Full-text search still wins on exact terms such as a model name (`Fjella 700`): it is instant and doesn't call an external API.

## Stack

- [FastAPI](https://fastapi.tiangolo.com/): HTTP API and interactive docs
- [MariaDB](https://mariadb.org/) 11.7+: `FULLTEXT` indexes and the native `VECTOR` type (tested on MariaDB Cloud / SkySQL serverless)
- [LangChain](https://python.langchain.com/) with `langchain-mariadb` (`MariaDBStore`) and `langchain-google-genai`
- [Gemini](https://ai.google.dev/) `gemini-embedding-001`: 3072-dimension embeddings, free tier
- [uv](https://docs.astral.sh/uv/): dependency and environment management

## Getting started

### Prerequisites

- Python 3.13+ and [uv](https://docs.astral.sh/uv/getting-started/installation/)
- MariaDB Connector/C, required to build the `mariadb` Python driver. On Debian/Ubuntu:
  ```bash
  sudo apt install libmariadb-dev
  ```
- A MariaDB 11.7+ database
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey); the free tier is enough

### 1. Install

```bash
git clone git@github.com:l-terra/ai-search-api.git
cd ai-search-api
uv sync
```

### 2. Configure

```bash
cp .env.example .env
```

Fill in `.env`:

| Variable | Description |
|---|---|
| `DB_HOST` | MariaDB host |
| `DB_PORT` | MariaDB port |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password; special characters are fine |
| `DB_NAME` | Database name, e.g. `demo` |
| `GOOGLE_API_KEY` | Gemini API key |

### 3. Load the catalog

Run [`demo.sql`](demo.sql) against your database. It creates the `products` table with a `FULLTEXT` index and loads [`products.csv`](products.csv) with `LOAD DATA LOCAL INFILE`. Change the file path in the script to where the CSV is on your machine.

### 4. Run

```bash
uv run fastapi dev main.py
```

Open the interactive docs at <http://127.0.0.1:8000/docs>.

### 5. Generate the embeddings

Call `POST /products/ingest` once. It embeds every product name with Gemini and stores the vectors in MariaDB. The tables `langchain_collection` and `langchain_embedding` are created automatically on startup.

To stay under the Gemini free-tier limit of 100 texts per minute, ingestion sends 90 names at a time with a 60-second pause between batches. For 500 products it takes about 5 minutes.

> **Note:** every call adds the vectors again. Calling it twice duplicates the results in vector search.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/products/text-search?query=...` | Top 10 products ranked by full-text relevance |
| `GET` | `/products/vector-search?query=...` | Top 10 products ranked by semantic similarity |
| `POST` | `/products/ingest` | Embeds all products into the vector store |

```bash
curl "http://127.0.0.1:8000/products/vector-search?query=running%20shoes"
```

## Project structure

```
.
├── main.py          # FastAPI app: connections, vector store and endpoints
├── demo.sql         # Schema + CSV import
├── products.csv     # 500 sample products
├── pyproject.toml   # Dependencies
├── uv.lock          # Locked dependency versions
└── .env.example     # Required environment variables
```

## Next steps

- **Hybrid search**: run both searches and merge the rankings, e.g. with Reciprocal Rank Fusion, so exact matches and semantic matches both rank well.
- Make ingestion idempotent, so re-running it doesn't duplicate vectors.
- Embed more product context (category, description) instead of just the name.
