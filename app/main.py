import logging
import os

from fastapi import FastAPI

# 1. Setup Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Production Service")


# 2. The Prototype Endpoints
@app.get("/")
def read_root():
    return {"message": "Welcome to the Internal API", "status": "active"}


@app.get("/data")
def get_data():
    logger.info("Data endpoint accessed")
    return {"items": ["unit_01", "unit_02"], "authorized": True}


# 3. The "Production" Health Check
@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0", "environment": os.getenv("ENV", "dev")}
