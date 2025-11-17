import atexit
import os
import requests
import asyncio
from typing import Optional, List
from msal import PublicClientApplication, ConfidentialClientApplication, SerializableTokenCache

# --- IMPORT SETTINGS FIRST ---
from app.core.config import settings

# --- Shared Configuration ---
AUTHORITY = f"https://login.microsoftonline.com/{settings.TENANT_ID}"

# --- Helper Function ---
def get_graph_client(access_token: str) -> requests.Session:
    """Returns a requests.Session with the provided access token."""
    if not access_token:
        raise ValueError("Access token cannot be empty")
    
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {access_token}"})
    return session

# --- Method for FULLY AUTOMATED Flow ---
def get_app_only_access_token() -> str:
    """Gets an app-only token using client credentials."""
    if not settings.CLIENT_SECRET:
        raise ValueError("CLIENT_SECRET must be set for the fully automated flow.")
    
    app = ConfidentialClientApplication(
        client_id=settings.CLIENT_ID,
        client_credential=settings.CLIENT_SECRET,
        authority=AUTHORITY
    )
    
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Could not acquire app-only token: {result.get('error_description')}")

# --- Method for SEMI-AUTOMATED Flow ---
token_cache = SerializableTokenCache()

def _load_token_cache() -> None:
    """Loads the token cache from the path specified in settings."""
    if os.path.exists(settings.TOKEN_CACHE_FILE):
        token_cache.deserialize(open(settings.TOKEN_CACHE_FILE, "r").read())
        
    atexit.register(
        lambda: open(settings.TOKEN_CACHE_FILE, "w").write(token_cache.serialize())
        if token_cache.has_state_changed
        else None
    )

# --- THIS IS THE FIX ---
# Only try to load the cache if we're not using the hardcoded token
if not settings.HARDCODED_ACCESS_TOKEN:
    _load_token_cache()

async def get_delegated_access_token(scopes: List[str]) -> str:
    """
    Gets a user-delegated token using a refresh token or interactive login.
    """
    app = PublicClientApplication(
        settings.CLIENT_ID, 
        authority=AUTHORITY, 
        token_cache=token_cache
    )
    accounts = app.get_accounts(username=settings.GRAPH_USER_IDENTIFIER)
    
    result = app.acquire_token_silent(scopes, account=accounts[0]) if accounts else None
    
    if not result:
        print("No cached token found. Starting device flow authentication...")
        flow = app.initiate_device_flow(scopes=scopes)
        if 'verification_uri' not in flow:
             raise KeyError(f"Failed to initiate device flow. Response: {flow}")
        print(f"To sign in, open a browser to {flow['verification_uri']} and enter the code: {flow['user_code']}")
        result = app.acquire_token_by_device_flow(flow)
    
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Could not acquire delegated token: {result.get('error_description')}")
