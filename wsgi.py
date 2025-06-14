import threading
import time
from datetime import datetime, time as dt_time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_daily_tasks_at_scheduled_time(app, hour=2, minute=0):
    """
    Run daily tasks in a background thread at a specific time
    Default: 2 AM every day
    """
    logger.info(f"Background scheduler started. Will run daily tasks at {hour:02d}:{minute:02d}")
    
    while True:
        try:
            now = datetime.now()
            
            # Check if it's time to run the tasks
            if now.hour == hour and now.minute == minute:
                logger.info("Running scheduled daily tasks...")
                
                with app.app_context():
                    try:
                        from backend.tasks.scheduled_tasks import run_daily_tasks
                        run_daily_tasks()
                        logger.info("Daily tasks completed successfully")
                    except Exception as e:
                        logger.error(f"Error in scheduled task: {e}")
                
                # Sleep for 61 seconds to avoid running multiple times in the same minute
                time.sleep(61)
            else:
                # Check every 30 seconds
                time.sleep(30)
                
        except Exception as e:
            logger.error(f"Error in scheduler thread: {e}")
            time.sleep(60)

def run_hourly_alert_checks(app):
    """Run alert checks every hour"""
    logger.info("Starting hourly alert checker...")
    
    while True:
        try:
            # Wait for 1 hour
            time.sleep(3600)
            
            logger.info("Running hourly alert check...")
            
            with app.app_context():
                try:
                    from backend.services.alert_service import AlertService
                    alert_service = AlertService()
                    alert_service.check_and_create_alerts()
                    logger.info("Hourly alert check completed")
                except Exception as e:
                    logger.error(f"Error in hourly alert check: {e}")
                    
        except Exception as e:
            logger.error(f"Error in hourly checker thread: {e}")
            time.sleep(60)

def run_tasks_for_testing(app, minutes=5):
    """
    For testing: Run tasks every few minutes
    """
    logger.info(f"TEST MODE: Running daily tasks every {minutes} minutes")
    
    while True:
        try:
            logger.info("Running test scheduled tasks...")
            
            with app.app_context():
                try:
                    from backend.tasks.scheduled_tasks import run_daily_tasks
                    run_daily_tasks()
                    logger.info("Test tasks completed successfully")
                except Exception as e:
                    logger.error(f"Error in test task: {e}")
            
            # Sleep for the specified number of minutes
            time.sleep(minutes * 60)
            
        except Exception as e:
            logger.error(f"Error in test scheduler: {e}")
            time.sleep(60)

if __name__ == '__main__':
    from backend.app import create_app
    
    app = create_app('development')
    
    # Choose your automation method:
    
    # Option A: Run at specific time (2 AM) - PRODUCTION-LIKE
    # task_thread = threading.Thread(
    #     target=run_daily_tasks_at_scheduled_time, 
    #     args=(app, 2, 0)  # Run at 2:00 AM
    # )
    
    # Option B: Run every X hours - GOOD FOR TESTING
    # task_thread = threading.Thread(
    #     target=run_daily_tasks_every_x_hours, 
    #     args=(app, 1)  # Run every 1 hour
    # )
    
    # Option C: Run every few minutes - ONLY FOR TESTING
    task_thread = threading.Thread(
        target=run_tasks_for_testing, 
        args=(app, 5)  # Run every 5 minutes for testing
    )
    
    # Make thread daemon so it stops when main app stops
    task_thread.daemon = True
    task_thread.start()


     # ADD THIS: Run alert checks every hour (even in testing)
    alert_check_thread = threading.Thread(
        target=run_hourly_alert_checks,
        args=(app,)
    )
    alert_check_thread.daemon = True
    alert_check_thread.start()
    
    logger.info("Starting Flask app with background scheduler...")
    
    # Run the Flask app
    app.run(debug=True, use_reloader=False)  # use_reloader=False to avoid duplicate threads