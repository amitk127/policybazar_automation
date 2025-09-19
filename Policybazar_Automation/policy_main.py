import os

from policy_navigation import PolicyBazaarNavigation
from policy_database import PolicyDatabase
from email_sender import EmailSender
import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format ='%(asctime)s - %(name)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class PolicyMain:



    POLICY_URL = os.environ.get('PolicyBazar_B2B_URL')
    DRIVER_PATH = os.environ.get('DriverPath')
    DB_USERNAME = os.environ.get('DB_Cred.Username')
    DB_PASSWORD = os.environ.get('DB_Cred.Password')
    DB_HOST = os.environ.get('DB_Cred.Parameter1')
    DB_PORT = os.environ.get('DB_Cred.Parameter2')
    DB_DATABASE_NAME = os.environ.get('DB_Cred.Encrypted1')
    DB_URL = f"postgresql://{DB_HOST}:{DB_PORT}/{DB_DATABASE_NAME}"
    BASE_DIRECTORY = os.environ.get('Directory')
    SCREENSHOT_DIR = os.path.join(BASE_DIRECTORY, 'Screenshot')

    SMTP_HOST = os.environ.get('Mail_Cred.Parameter1')
    SMTP_PORT = os.environ.get('Mail_Cred.Parameter2')
    USERNAME = os.environ.get('Mail_Cred.Username')
    PASSWORD = os.environ.get('Mail_Cred.Password')
    SENDERID = os.environ.get('SenderID')
    TO_EMAIL = os.environ.get('TO')


    email_config = {
        'SMTP_HOST': SMTP_HOST,
        'SMTP_PORT': SMTP_PORT,
        'USERNAME': USERNAME,
        'PASSWORD': PASSWORD,
        'SENDERID': SENDERID,
        'TO_EMAIL': TO_EMAIL
    }
    @staticmethod
    def main():
        driver = None
        connection = None

        try:
            driver = PolicyBazaarNavigation.policy_bazaar_initiate(
                PolicyMain.POLICY_URL,
                PolicyMain.DRIVER_PATH
            )

            connection = PolicyDatabase.get_connection(
                PolicyMain.DB_URL,
                PolicyMain.DB_USERNAME,
                PolicyMain.DB_PASSWORD
            )

            if not connection:
                logger.info("Failed to establish database connection")
                return
            ids = PolicyDatabase.get_ids(connection)

            if not ids:
                logger.info("No pending records found to process")
                return

            logger.info(f"Found {len(ids)} records to process")



            for record_id in ids:
                record_start_time = datetime.datetime.now().replace(microsecond=0)

                try:

                    PolicyDatabase.update_case_start_time(connection, record_id, record_start_time)
                    record = PolicyDatabase.get_policy_record(connection, record_id)
                    if record:
                        PolicyBazaarNavigation.navigation(connection, driver, record, PolicyMain.POLICY_URL, PolicyMain.SCREENSHOT_DIR, PolicyMain.email_config)
                        record_end_time = datetime.datetime.now().replace(microsecond=0)
                        duration = record_end_time - record_start_time
                        logger.info(f"Record {record_id} completed successfully in {duration}")
                        duration_str = str(duration)
                        PolicyDatabase.update_duration(connection, record_id, duration_str)
                    else:
                        logger.info(f"Record not found for ID: {record_id}")


                except Exception as e:

                    logger.info(f"Error processing record ID {record_id}: ")


                    error_end_time = datetime.datetime.now().replace(microsecond=0)
                    error_duration = error_end_time - record_start_time
                    duration_str = str(error_duration)

                    PolicyDatabase.update_case_end_time(connection, record_id, error_end_time)
                    PolicyDatabase.update_duration(connection, record_id, duration_str)


                    logger.info(f"Error processing record ID {record_id}:")

                    continue

            logger.info("Process Completed")

        except Exception as e:
            logger.info(f"Error in main process", exc_info=True)
            logger.info(f"Error in main process")

            EmailSender.send_error_email(None, "Main Process Failure", "N/A", "N/A", PolicyMain.email_config)

        finally:

            try:
                if driver:
                    driver.quit()
                    logger.info("WebDriver closed successfully")
            except Exception as e:

                logger.info(f"Error closing WebDriver")


            try:
                if connection:
                    connection.close()
                    logger.info("Database connection closed successfully")
            except Exception as e:

                logger.info(f"Error closing database connection: ")



if __name__ == "__main__":
    PolicyMain.main()