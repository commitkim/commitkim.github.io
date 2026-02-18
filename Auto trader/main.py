import os
import sys
import time
import schedule
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Set encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

import config
from trader import AutoTrader

import logging
from logging.handlers import TimedRotatingFileHandler

# Add project root to sys.path to access Dashboard scripts if needed
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

# Load .env file
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# Setup Logging
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

log_filename = datetime.now().strftime("%Y-%m-%d") + ".log"
log_filepath = os.path.join(LOG_DIR, log_filename)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_filepath, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def job():
    logging.info(f"Starting Trading Cycle")
    try:
        trader = AutoTrader(config)
        trader.run_cycle()
        
        # Trigger Canary Build (Build -> Test -> Deploy)
        # We use the existing batch script for this
        build_script = os.path.join(PROJECT_ROOT, 'build_test_deploy.bat')
        print(f"[Scheduler] Triggering Canary Build: {build_script}")
        os.system(f'"{build_script}" auto')
        
    except Exception as e:
        print(f"❌ Critical Error in Trading Job: {e}")
        traceback.print_exc()

def main():
    logging.info("🤖 Auto Trader Initializing...")
    
    # Load initial config to set schedule
    try:
        interval = config.TRADING['interval_minutes']
        logging.info(f"✅ Config loaded. Schedule interval: {interval} minutes.")
        
        # Schedule the job
        schedule.every(interval).minutes.do(job)
        
        # Run once immediately on startup
        job()
        
        print("🚀 Scheduler started. Press Ctrl+C to exit.")
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Auto Trader Stopped by User.")
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
