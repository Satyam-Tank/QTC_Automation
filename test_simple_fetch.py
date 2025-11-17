import logging
import requests
from typing import Dict, Any

# Import settings to read the .env file
from app.core.config import settings

# --- Copied from your graph_auth_service.py ---
def get_graph_client(access_token: str) -> requests.Session:
    """Returns a requests.Session with the provided access token."""
    if not access_token:
        raise ValueError("Access token cannot be empty")
    
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {access_token}"})
    return session
# -----------------------------------------------

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TEST_EMAIL_ID = "AAMkADBjNDBiZmM4LTIyYWEtNDFlMC04NDNjLTIwMWI5ZTg4ODgzMgBGAAAAAABjtkV1MXemQIF_Wr5o4GqSBwCt3fqaL-viT5cVhhC5ll72AAAAAAEMAACt3fqaL-viT5cVhhC5ll72AAAA7_DiAAA="

class SimpleGraphApiService:
    """A simple service to test fetching one email."""

    def __init__(self, access_token: str = None):
        if not access_token:
            raise ValueError("Must provide 'access_token'")
        
        # Use the hardcoded token
        self.session = get_graph_client(access_token)
        logging.info("Initializing with hardcoded access token...")
        logging.info("✅ Session created successfully.")

    def get_email_by_id(self, email_id: str) -> Dict[str, Any]:
        # Get MAILBOX_UPN from our settings file
        mailbox_upn = settings.MAILBOX_UPN
        
        url = f"{GRAPH_BASE}/users/{mailbox_upn}/messages/{email_id}"
        logging.info(f"Hitting URL: {url}")
        
        response = self.session.get(url, timeout=30)
        
        # This will raise an error if it's 401
        response.raise_for_status() 
        return response.json()

def run_hardcoded_test():
    logging.info("\n--- 🧪 Running HARDCODED Token Test ---")
    
    # Get the token from our settings
    hardcoded_token = settings.HARDCODED_ACCESS_TOKEN
    
    if not hardcoded_token:
        logging.error("❌ HARDCODED_ACCESS_TOKEN not found in .env file. Skipping test.")
        return

    try:
        graph_service = SimpleGraphApiService(access_token=hardcoded_token)
        email = graph_service.get_email_by_id(TEST_EMAIL_ID)
        logging.info(f"✅✅✅ Success! Fetched email with subject: {email.get('subject')}")
    
    except Exception as e:
        logging.error(f"❌❌❌ Test Failed. Error: {e}", exc_info=False)
        if "401" in str(e):
            logging.error("\n---")
            logging.error("This is a 401 Unauthorized error. It confirms your token is invalid, expired, or does not have the 'Mail.ReadWrite' permission.")
            logging.error("Please get a new token from Graph Explorer with 'Mail.ReadWrite' and try again.")
            logging.error("---\n")
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run_hardcoded_test()
