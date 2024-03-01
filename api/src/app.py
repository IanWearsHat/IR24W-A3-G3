from fastapi import FastAPI

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


@app.get("/hello")
async def root():
    return {"message": "Hello World"}
