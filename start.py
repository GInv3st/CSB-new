import logging
import os
import sys
import traceback
from dotenv import load_dotenv

logging.basicConfig(filename='bot.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Redirect stdout and stderr to the log file
sys.stdout = open('bot.log', 'a')
sys.stderr = open('bot.log', 'a')

logging.info("✅ Bot is starting...")

try:
    load_dotenv()
    from runner import main as run_main
    import asyncio
    asyncio.run(run_main())
    logging.info("✅ Bot run completed successfully.")
except Exception as e:
    logging.error("❌ Bot failed to start or run.")
    logging.error(traceback.format_exc())
    sys.exit(1)


