from fastapi import FastAPI, Form

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

@app.post("/process-query")
async def process_query(query: str = Form()):
    print(query)

    
