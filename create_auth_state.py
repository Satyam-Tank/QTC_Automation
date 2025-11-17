import asyncio
from playwright.sync_api import sync_playwright

# --- TODO: Update this to the LOGIN page of your Power App ---
LOGIN_URL = "https://login.microsoftonline.com/" 
# A good URL is usually the app's URL itself, it will redirect to login.
# QTC_APP_URL = "https://houseofshipping.sharepoint.com/sites/Team-DataScienceAI/..."

AUTH_FILE = "auth.json"

def run_auth_flow():
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page()
        
        print(f"Navigating to login page: {LOGIN_URL}")
        page.goto(LOGIN_URL)
        
        print("\n" + "="*50)
        print("==> PLEASE LOG IN TO THE APPLICATION IN THE BROWSER <==")
        print("==> Complete any 2-Factor Authentication.")
        print("==> After you are fully logged in, press Enter in this terminal.")
        print("="*50 + "\n")
        
        input("Press Enter here after you have logged in...")
        
        print("Saving authentication state...")
        page.context.storage_state(path=AUTH_FILE)
        
        print(f"Successfully saved auth state to {AUTH_FILE}")
        browser.close()

if __name__ == "__main__":
    print(f"This script will generate '{AUTH_FILE}' for automated logins.")
    run_auth_flow()
