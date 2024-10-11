import os
import subprocess
import json
import shutil
import tempfile
from celery import Celery
from helpers import process_json, extract_sections
from constants import RESULTS_DIR
from loguru import logger

# Load environment variables if needed
from dotenv import load_dotenv

load_dotenv(".env")
# Create necessary directories
os.makedirs(RESULTS_DIR, exist_ok=True)
# Initialize Celery
celery_app = Celery(
    "pdf_processing", broker=os.getenv("PD_CELERY_BROKER_URL"), backend=os.getenv("PD_CELERY_RESULT_BACKEND")
)
celery_app.conf.broker_connection_retry_on_startup = True


@celery_app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


@celery_app.task(name="process_pdf_task", bind=True)
def process_pdf_task(self, file_path):
    try:
        # Use a secure temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy the file to the temp_dir
            input_filename = os.path.basename(file_path)
            input_path = os.path.join(temp_dir, input_filename)
            shutil.copyfile(file_path, input_path)
            logger.info(f"Copied file to {input_path}")

            # Define prefixes for output files
            output_metadata_prefix = os.path.join(temp_dir, "data-")
            os.makedirs(output_metadata_prefix, exist_ok=True)
            # Log the current working directory and its contents
            logger.info(f"Current working directory: {os.getcwd()}")
            logger.info(f"Contents of current directory: {os.listdir()}")

            cmd = [
                "java",
                "-jar",
                "/app/pdffigures2.jar",
                # "org.allenai.pdffigures2.FigureExtractorBatchCli",
                input_path,
                "-g",
                output_metadata_prefix,
            ]

            # Run pdffigures2 synchronously
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Log stdout and stderr
            if process.stdout:
                logger.info(f"pdffigures2 stdout: {process.stdout}")
            if process.stderr:
                logger.error(f"pdffigures2 stderr: {process.stderr}")

            if process.returncode != 0:
                raise Exception(f"pdffigures2 processing failed: {process.stderr}")

            # Extract base filename without extension
            base_filename = os.path.splitext(input_filename)[0]

            # Construct the path to the output JSON file
            output_json_path = f"{output_metadata_prefix}{base_filename}.json"

            # Read and parse the metadata JSON file
            with open(output_json_path, "r") as f:
                metadata = json.load(f)

            full_text = process_json(metadata)
            structred_content = extract_sections(full_text)
            results = {"metadata": metadata, "full_text": full_text, "structured_content": structred_content}

            # Save results to a file
            result_filename = f"{process_pdf_task.request.id}.json"
            result_path = os.path.join(RESULTS_DIR, result_filename)
            self.update_state(state="SUCCESS", meta=results)
            with open(result_path, "w") as f:
                json.dump(results, f)

            logger.info(f"Processing completed for task {process_pdf_task.request.id}")
            return {"result_file": result_filename}

    except Exception as e:
        logger.error(f"Error during processing: {e}")
        return {"error": str(e)}
