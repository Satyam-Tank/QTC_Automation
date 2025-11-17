import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, Response, BackgroundTasks

from app.core.config import settings
from app.processing import process_email_job

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="QTC Data Entry Agent - Prototype")
logger = logging.getLogger(__name__)

@app.get("/")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/notifications")
async def handle_notifications(
    request: Request,
    background_tasks: BackgroundTasks
) -> Response:
    
    # 1. Handle validationToken handshake
    validation_token = request.query_params.get("validationToken")
    if validation_token:
        logger.info("Received validation token handshake.")
        return Response(content=validation_token, media_type="text/plain", status_code=200)

    # 2. Process the notification
    try:
        body = await request.json()
        logger.info(f"Received notification: {body}")
    except Exception as e:
        logger.error(f"Error parsing notification payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 3. Validate and Enqueue
    if "value" in body:
        for notification in body["value"]:
            if notification.get("clientState") != settings.CLIENT_STATE_SECRET:
                logger.warning("Invalid client state. Skipping.")
                continue

            resource = notification.get("resource", "")
            
            # --- THIS IS THE FIX ---
            if "/messages/" in resource.lower():
            # --- THIS IS THE FIX ---
            
                # Get the last part of the resource string as the ID
                email_id = resource.split("/")[-1]
                logger.info(f"Adding job to background tasks for email: {email_id}")
                
                background_tasks.add_task(process_email_job, email_id)
            
            else:
                logger.warning(f"Unexpected resource format: {resource}")

    # 4. Respond immediately
    return Response(status_code=202, content="Accepted")
