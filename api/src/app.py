from fastapi import FastAPI, Form
from index import Index
from ranker import calculate_scores
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


class Timer:
    total_time = 0

    def __init__(self, message):
        self.message = message

    def __enter__(self):
        self.past = time.time()

    def __exit__(self, exc_type, exc_value, traceback):
        diff = time.time() - self.past
        print(f"{diff:.6f} seconds to process {self.message}")
        Timer.total_time += diff


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
def process_query(query: str = Form()):
    print(f'Query "{query}" received')
    total_time = 0

    with Timer("postings"):
        postings = index.get_postings_from_query(query)

    with Timer("intersecting postings"):
        intersecting = index._get_intersecting_postings(postings)

    with Timer("doc amount"):
        num_docs = index.get_doc_amount(postings)

    with Timer("scores"):
        scores = calculate_scores(query, postings, intersecting, num_docs)

    with Timer("getting urls"):
        docs = [k for k in list(scores.keys())[-10:]]
        urls = index.get_urls(docs)

    print(f"{Timer.total_time:.6f} seconds total".center(40, '='))
    print(scores)

    return {"urls": urls}
