from fastapi import FastAPI, Form
from index import Index

app = FastAPI()

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
index = Index(
    r"C:\Users\ianbb\Documents\Code\121\IR24W-A3-G3\api\src\DEV_doc_ID_map.json",
    r"C:\Users\ianbb\Documents\Code\121\IR24W-A3-G3\api\src\DEV_inv_index.json",
)


async def process():
    print("started processing")
    doc_ids = index.get_query_intersection("cristina lopes")
    print("doc_ids", doc_ids)
    urls = index.get_top_urls(doc_ids)
    print("returning", urls)

    return urls

@app.post("/process-query")
async def process_query(query: str = Form()):
    urls = await process()
    return {"urls": urls}
