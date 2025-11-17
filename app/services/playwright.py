import logging
from contextlib import contextmanager
from playwright.sync_api import (
    sync_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Error as PlaywrightError
)
from typing import Generator

from app.core.config import settings
from app.models.qtc_models import QTCFormData

# Configure logging
logger = logging.getLogger(__name__)

# The target URL for the Power App
# --- TODO: Update this to the actual QTC App URL ---
QTC_APP_URL = "https://houseofshipping.sharepoint.com/sites/Team-DataScienceAI/..."

@contextmanager
def launch_playwright_context() -> Generator[tuple[Playwright, Browser, BrowserContext, Page], None, None]:
    """
    Manages the lifecycle of Playwright resources (start, launch, close).
    Uses the saved storage state to log in automatically.
    """
    if not settings.AUTH_JSON_PATH.exists():
        logger.error(f"FATAL: Playwright auth file not found at: {settings.AUTH_JSON_PATH}")
        raise FileNotFoundError(f"Storage state file not found: {settings.AUTH_JSON_PATH}")

    logger.info(f"Using storage state: {settings.AUTH_JSON_PATH}")
    logger.info("Launching Playwright...")
    
    pw_instance: Playwright | None = None
    browser: Browser | None = None
    context: BrowserContext | None = None
    
    try:
        pw_instance = sync_playplaywright().start()
        browser = pw_instance.chromium.launch(
            headless=True,  # Run headless in Docker
            slow_mo=50      # Add a small slow_mo for stability
        )
        
        logger.info("Browser launched. Creating new context with saved auth.")
        context = browser.new_context(
            storage_state=str(settings.AUTH_JSON_PATH)
        )
        page = context.new_page()
        
        # Yield the resources to the caller
        yield pw_instance, browser, context, page
        
    except PlaywrightError as e:
        logger.error(f"Playwright error during launch: {e}")
        raise
    except Exception as e:
        logger.error(f"Unhandled exception during Playwright setup: {e}")
        raise
    finally:
        # Graceful cleanup
        logger.info("Cleaning up Playwright resources...")
        try:
            if context:
                context.close()
            if browser:
                browser.close()
            if pw_instance:
                pw_instance.stop()
        except Exception as e:
            logger.warning(f"Ignoring error during Playwright shutdown: {e}")
        logger.info("Playwright stopped.")


class PlaywrightService:
    """
    A service to interact with the QTC Power App.
    """
    def __init__(self, data: QTCFormData):
        self.data = data

    def fill_qtc_form(self) -> str:
        """
        Launches an authenticated browser, navigates to the QTC app,
        and fills the form with the provided data.
        """
        logger.info(f"Starting browser automation for: {self.data.client_name}")
        
        try:
            with launch_playwright_context() as (pw, browser, context, page):
                
                logger.info(f"Navigating to QTC App URL: {QTC_APP_URL}")
                page.goto(QTC_APP_URL, wait_until="networkidle", timeout=60000)
                logger.info(f"Page loaded: {page.title()}")
                
                # --- TODO: This is where we implement the REAL logic ---
                # This logic is highly dependent on the Power App's HTML structure.
                # We need to find the locators (CSS Selectors, data-testid, etc.)
                # for each form field from the PDF.
                
                # Example (using locators):
                # logger.info(f"Setting Client Name: {self.data.client_name}")
                # page.locator("input[data-testid='client_name_field']").fill(self.data.client_name)
                
                # logger.info(f"Setting Product: {self.data.product}")
                # page.locator(f"button[data-value='{self.data.product}']").click()
                
                # logger.info(f"Setting POL: {self.data.port_of_loading}")
                # page.locator("input[data-testid='pol_field']").fill(self.data.port_of_loading)
                
                # logger.info(f"Setting POD: {self.data.port_of_discharge}")
                # page.locator("input[data-testid='pod_field']").fill(self.data.port_of_discharge)

                # logger.info(f"Setting Commodity: {self.data.commodity}")
                # page.locator("input[data-testid='commodity_field']").fill(self.data.commodity)
                
                # logger.info("All fields filled. Simulating submit.")
                # page.locator("button[data-testid='submit_button']").click()
                
                # --- Placeholder Logic ---
                logger.info("--- (START) PLACEHOLDER LOGIC ---")
                logger.info("Pretending to fill form...")
                page.wait_for_timeout(5000) # Simulate 5 seconds of work
                logger.info(f"Data used: {self.data.model_dump_json(indent=2)}")
                logger.info("Pretending to click submit...")
                page.wait_for_timeout(1000)
                logger.info("--- (END) PLACEHOLDER LOGIC ---")

                # --- Wait for submission confirmation ---
                # page.wait_for_selector("div[data-testid='success_message']", timeout=30000)
                
                success_message = f"Successfully submitted QTC for {self.data.client_name}"
                logger.info(success_message)
                
                return success_message

        except FileNotFoundError:
            # This is a critical failure, raised by launch_playwright_context
            return "Automation failed: Auth file not found."
        except Exception as e:
            logger.exception(f"Unhandled exception during form filling: {e}")
            # HIL Trigger: Notify human that automation failed
            return f"Automation failed: {str(e)}"

# --- Helper function for our job ---
def fill_qtc_form_job(data: QTCFormData) -> str:
    """
    A helper function that our processing.py job can call.
    """
    service = PlaywrightService(data=data)
    result = service.fill_qtc_form()
    return result
