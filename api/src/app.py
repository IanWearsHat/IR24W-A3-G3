from fastapi import FastAPI, Form

from index import Index
from ranker import calculate_scores


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
    """Gets and ranks urls given a query."""
    print(f'Query "{query}" received')

    postings = index.get_postings_from_query(query)
    intersecting = index.get_intersecting_postings(postings)
    num_docs = index.get_doc_amount(postings)

    if num_docs == 0:
        return {"urls": []}

    scores = calculate_scores(query, postings, intersecting, num_docs)

    docs = [k for k in list(scores.keys())[-10:]]
    urls = index.get_urls(docs)
    urls = urls[::-1]

    return {"urls": urls}
