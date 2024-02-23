import logging

import uvicorn

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        port=8000,
        log_level="info",
        reload=True,
    )
