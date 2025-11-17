import logging
import tempfile
import os
from pydantic import ValidationError
from app.models.qtc_models import QTCFormData

from app.services.graph_api import get_graph_service_sync, GraphApiService
from app.services.gemini import get_structured_data_from_ai
from app.services.playwright import fill_qtc_form_job
from app.parsing.email_parser import parse_full_email
from app.parsing.doc_processor import DocumentProcessor

logger = logging.getLogger(__name__)

def run_automation_job(validated_data: QTCFormData) -> None:
    try:
        logger.info(f"[AUTOMATION_START] Running for: {validated_data.client_name}")
        result = fill_qtc_form_job(validated_data) 
        logger.info(f"[AUTOMATION_END] Complete. Result: {result}")
    except Exception as e:
        logger.error(f"FATAL error in run_automation_job: {e}", exc_info=True)
        raise

def process_email_job(email_id: str) -> None:
    try:
        logger.info(f"[JOB_START] Processing email: {email_id}")
        
        logger.info("Authenticating to Microsoft Graph...")
        graph_service: GraphApiService = get_graph_service_sync()
        
        logger.info(f"Fetching email data for ID: {email_id}")
        email_data = graph_service.get_email_by_id(email_id)
        
        logger.info("Parsing email body...")
        parsed_email = parse_full_email(email_data)
        full_context = f"Email Subject: {parsed_email.get('subject', '')}\n\n"
        full_context += f"Email Body Table Data:\n{parsed_email.get('table_data', {})}\n\n"
        
        logger.info("Fetching attachments...")
        attachments = graph_service.get_attachments(email_id)
        doc_processor = DocumentProcessor()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for att in attachments:
                file_path = os.path.join(temp_dir, att['name'])
                logger.info(f"Processing attachment: {att['name']}")
                with open(file_path, 'wb') as f:
                    f.write(att['content_bytes'])
                
                processed_doc = doc_processor.process_document(file_path)
                if processed_doc and processed_doc['type'] != 'image':
                    full_context += f"--- Attachment: {att['name']} ---\n"
                    full_text = processed_doc.get('text', '')
                    if full_text:
                        full_context += full_text
                    full_context += "\n-----------------------------------\n\n"
                
        logger.info("Sending full context to Gemini for extraction...")
        extracted_json = get_structured_data_from_ai(full_context)
        
        try:
            validated_data = QTCFormData(**extracted_json)
            logger.info("Data validated by Pydantic.")
            run_automation_job(validated_data)
        except ValidationError as e:
            logger.error(f"Data validation failed: {e}", exc_info=False)
            logger.error(f"AI Output: {extracted_json}")
            pass
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            pass

        logger.info(f"[JOB_END] Finished processing: {email_id}")
    except Exception as e:
        logger.error(f"FATAL error in process_email_job: {e}", exc_info=True)
        raise
