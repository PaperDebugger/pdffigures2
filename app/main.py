import re
from fastapi import FastAPI, File, UploadFile, HTTPException, APIRouter
import os
from loguru import logger
from celery.result import AsyncResult
from celery_tasks import celery_app
from constants import UPLOAD_DIR, RESULTS_DIR, API_DIR
import json

# Create necessary directories
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(os.path.join(API_DIR, "logs"), exist_ok=True)

app = FastAPI(
    title="PDF Processing API",
    description="An API for processing PDFs",
    version="1.0.0",
    openapi_url="/v1/openapi.json",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
)

# Create API router for v1
v1_router = APIRouter(prefix="/v1")

# Configure logger
logger.add(os.path.join(API_DIR, "logs/api.log"), rotation="500 MB", level="INFO")


@v1_router.post("/pdfs/process")
async def extract(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    clean_filename = re.sub(r"[^\w\-_\.]", "_", file.filename)
    file_path = os.path.join(UPLOAD_DIR, clean_filename)

    # Save the uploaded PDF file
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"Saved PDF to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Could not save the file: {e}")

    try:
        # Start the celery task
        result = celery_app.send_task("process_pdf_task", args=[file_path])
        logger.info(f"Started Celery task {result.id}")
        return {"task_id": result.id}
    except Exception as e:
        logger.error(f"Error starting Celery task: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@v1_router.get("/pdfs/process/{task_id}")
def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    if task_result.state == "PENDING":
        return {"status": "pending"}
    elif task_result.state == "SUCCESS":
        result = task_result.result
        if "error" in result:
            return {"status": "failed", "error": result["error"]}
        else:
            return {"status": "completed", "result": result}
    elif task_result.state == "FAILURE":
        return {"status": "failed", "error": str(task_result.result)}
    else:
        return {"status": task_result.state}


@v1_router.get("/health")
async def health_check():
    """
    Perform a health check on the API.

    This endpoint checks the overall health of the API service. It can be used
    for monitoring and alerting purposes.

    Returns:
        dict: A dictionary indicating the health status of the API.
            {
                "status": "healthy"
            }
    """
    logger.info("Health check endpoint called")
    return {"status": "healthy"}


# Include the v1 router in the main app
app.include_router(v1_router)


@app.get("/")
async def root():
    """
    Root endpoint that provides a welcome message and directs users to the API endpoints.

    Returns:
        dict: A dictionary containing a welcome message.
    """
    return {"message": "Welcome to the PDF Processing API. Please use /api/v1/ endpoints."}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting FastAPI application")
    uvicorn.run(app, host="0.0.0.0", port=8000)
