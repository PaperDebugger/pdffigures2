from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from helpers import process_json
import subprocess
import os
import uuid
import shutil
import json
import asyncio
import logging
import tempfile

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Use a secure temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate a unique identifier for filenames
        unique_id = str(uuid.uuid4())
        input_filename = f"{unique_id}.pdf"
        input_path = os.path.join(temp_dir, input_filename)

        # Define prefixes for output files
        output_metadata_prefix = os.path.join(temp_dir, "data-")
        # output_figure_prefix = os.path.join(temp_dir, "figure-")

        os.makedirs(output_metadata_prefix, exist_ok=True)

        # Save the uploaded PDF file
        try:
            with open(input_path, "wb") as f:
                content = await file.read()
                f.write(content)
            logger.info(f"Saved PDF to {input_path}")
        except Exception as e:
            logger.error(f"Failed to save PDF: {e}")
            raise HTTPException(status_code=500, detail=f"Could not save the file: {e}")

        cmd = [
            "java",
            "-cp",
            "/app/pdffigures2.jar",
            "org.allenai.pdffigures2.FigureExtractorBatchCli",
            input_path,
            "-g",
            output_metadata_prefix,
        ]
        # cmd = [
        #     "java",
        #     "-jar",
        #     "/app/pdffigures2.jar",
        #     "-d",
        #     output_metadata_prefix,
        #     "-m",
        #     output_figure_prefix,
        #     input_path,
        # ]

        try:
            # Run pdffigures2 asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            # Log stdout and stderr
            if stdout:
                logger.info(f"pdffigures2 stdout: {stdout.decode()}")
            if stderr:
                logger.error(f"pdffigures2 stderr: {stderr.decode()}")

            if process.returncode != 0:
                raise HTTPException(status_code=500, detail="pdffigures2 processing failed")

            # Extract base filename without extension
            base_filename = os.path.splitext(input_filename)[0]

            # Construct the path to the output JSON file
            output_json_path = f"{output_metadata_prefix}{base_filename}.json"

            # Optional: Log the files in the temporary directory
            logger.info(f"Files in temp_dir: {os.listdir(temp_dir)}")

            # Read and parse the metadata JSON file
            with open(output_json_path, "r") as f:
                metadata = json.load(f)

            full_text = process_json(metadata)
            # Log success
            logger.info(f"Extraction successful for {file.filename}")

            # Return the metadata
            return {"metadata": metadata, "full_text": full_text}

        except Exception as e:
            logger.error(f"Error during processing: {e}")
            raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
