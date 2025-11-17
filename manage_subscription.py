import sys
import asyncio
import logging
from datetime import datetime, timedelta, timezone
# --- UPDATED IMPORT ---
from app.services.graph_api import get_graph_service_async
from app.core.config import settings

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sub_manager")

async def manage_subscription():
    """
    CLI for managing Graph API webhook subscriptions.
    """
    try:
        logger.info("Attempting to authenticate with Microsoft Graph...")
        # --- UPDATED FUNCTION CALL ---
        service = await get_graph_service_async()
        logger.info("Authentication successful.")
    except Exception as e:
        logger.error(f"Error authenticating: {e}", exc_info=True)
        logger.error("Please ensure 'user_tokens.json' or 'HARDCODED_ACCESS_TOKEN' is valid.")
        return

    if len(sys.argv) < 2:
        print("\nUsage: python manage_subscription.py [create|list|delete|recreate]")
        return

    command = sys.argv[1].lower()

    # ... (Rest of the file is identical) ...
    try:
        logger.info("Fetching existing subscriptions...")
        existing = service.list_subscriptions()
    except Exception as e:
        logger.error(f"Error fetching subscriptions: {e}", exc_info=True)
        return

    if command == "list":
        if not existing:
            logger.info("No active subscriptions found.")
            return
        logger.info("Active Subscriptions:")
        for sub in existing:
            print(f"- ID: {sub['id']}")
            print(f"  Resource: {sub['resource']}")
            print(f"  Expires: {sub['expirationDateTime']}")
            print(f"  URL: {sub.get('notificationUrl')}")
            print(f"  State: {sub.get('clientState')}")
        return

    if command == "delete":
        if not existing:
            logger.info("No active subscriptions to delete.")
            return
        logger.info("Deleting all active subscriptions...")
        for sub in existing:
            try:
                service.delete_subscription(sub['id'])
                logger.info(f"Deleted: {sub['id']}")
            except Exception as e:
                logger.error(f"Failed to delete {sub['id']}: {e}", exc_info=True)
        return

    if command == "create":
        for sub in existing:
            if sub.get('notificationUrl') == settings.WEBHOOK_NOTIFICATION_URL:
                logger.warning("Subscription with this Notification URL already exists.")
                logger.warning("Run 'python manage_subscription.py recreate' to delete and re-add.")
                print(f"  ID: {sub['id']}")
                print(f"  Expires: {sub['expirationDateTime']}")
                return
        try:
            logger.info(f"Creating new subscription for {settings.WEBHOOK_NOTIFICATION_URL}...")
            new_sub = service.create_subscription()
            logger.info("Successfully created subscription:")
            print(f"  ID: {new_sub['id']}")
            print(f"  Expires: {new_sub['expirationDateTime']}")
        except Exception as e:
            logger.error(f"Error creating subscription: {e}", exc_info=True)
        return

    if command == "recreate":
        logger.info("Recreating subscription...")
        if existing:
            logger.info("Deleting existing subscriptions...")
            for sub in existing:
                try:
                    service.delete_subscription(sub['id'])
                    logger.info(f"Deleted: {sub['id']}")
                except Exception as e:
                    logger.error(f"Failed to delete {sub['id']}: {e}", exc_info=True)
        
        try:
            logger.info(f"Creating new subscription for {settings.WEBHOOK_NOTIFICATION_URL}...")
            new_sub = service.create_subscription()
            logger.info("Successfully created new subscription:")
            print(f"  ID: {new_sub['id']}")
            print(f"  Expires: {new_sub['expirationDateTime']}")
        except Exception as e:
            logger.error(f"Error creating subscription: {e}", exc_info=True)
        return
    
    logger.warning(f"Unknown command: {command}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(manage_subscription())
    
# docker exec 1855932c0710 python manage_subscription.py list