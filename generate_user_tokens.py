import asyncio
import sys
import logging
from app.services import graph_auth

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("token_generator")

async def main():
    """
    Runs the one-time device auth flow to get the
    initial refresh token and create user_tokens.json.
    """
    logger.info("Starting one-time auth flow...")
    
    scopes = ['User.Read', 'Mail.Read', 'Mail.Send', 'Mail.ReadWrite']
    
    try:
        await graph_auth.get_delegated_access_token(scopes=scopes)
        logger.info("\n" + "="*50)
        logger.info("✅ Successfully generated user_tokens.json!")
        logger.info("="*50 + "\n")
    except Exception as e:
        logger.error(f"\nAn error occurred during auth: {e}", exc_info=True)

if __name__ == "__main__":
    # Handle the Windows asyncio policy, just like in the -c command
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
