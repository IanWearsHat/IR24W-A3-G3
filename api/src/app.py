from fastapi import FastAPI, Form
from index import Index
import time

"""
structure for document return object:
    {
        "docs": [
            {
                "title": doc_title,
                "url": url,
                "content": first 50 words or so
                "file_path": path           # for the AI to read and summarize
            },
            {
                "title": doc_title,
                "url": url,
                "content": first 50 words or so
                "file_path": path           # for the AI to read and summarize
            },
        ]
    }
"""
app = FastAPI()
index = None


@app.on_event("startup")
async def startup_event():
    global index
    index = Index()


@app.on_event("shutdown")
async def shutdown_event():
    index.close_index_files()


@app.post("/process-query")
async def process_query(query: str = Form()):
    print(query, "received")
    past = time.time()

    doc_ids = index.get_query_intersection(query)
    urls = index.get_urls(doc_ids)

    now = time.time()
    print(f"{(now - past):.6f} seconds taken to process query")
    return {"urls": urls}
