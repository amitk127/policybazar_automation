import smtplib
import os
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import logging
logger = logging.getLogger(__name__)

class EmailSender:


    @staticmethod
    def send_error_email(attachment_path, error_type, record_id, car_number, email_config):

        try:
            SMTP_HOST = email_config['SMTP_HOST']
            SMTP_PORT = email_config['SMTP_PORT']
            USERNAME = email_config['USERNAME']
            PASSWORD = email_config['PASSWORD']
            SENDERID = email_config['SENDERID']
            TO_EMAIL = email_config['TO_EMAIL']


            msg = MIMEMultipart()

            msg['From'] = SENDERID
            msg['To'] = TO_EMAIL
            msg['Subject'] = f"Error in PolicyBazaar B2B - ID: {record_id}, Car: {car_number}"

            body = f"""Hello Team,
            
An error occurred during the PolicyBazaar automation process.
Error Details:
Error Type: {error_type}
ID: {record_id}
Car Number: {car_number}

Please see the attached screenshot for more details (if available).

Regards,
RPA BOT."""

            msg.attach(MIMEText(body, 'plain'))

            if attachment_path and attachment_path.strip():
                if os.path.exists(attachment_path) and os.access(attachment_path, os.R_OK):
                    with open(attachment_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())

                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(attachment_path)}'
                    )
                    msg.attach(part)
                    logger.info(f"Attachment added to email: {attachment_path}")
                else:
                    logger.info(f"Attachment file not found or not readable: {attachment_path}")
                    body += "\nNote: Screenshot attachment was not found or not readable."
                    msg.attach(MIMEText(body, 'plain'))
                    msg = MIMEMultipart()
                    msg['From'] = SENDERID
                    msg['To'] = TO_EMAIL
                    msg['Subject'] = f"Error in PolicyBazaar B2B - ID: {record_id}, Car: {car_number}"

            else:
                logger.info("No attachment provided for email.")

            tls_context = ssl.create_default_context()
            tls_context.maximum_version = ssl.TLSVersion.TLSv1_2

            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls(context=tls_context)
            server.login(USERNAME, PASSWORD)

            text = msg.as_string()
            server.sendmail(SENDERID, TO_EMAIL, text)
            server.quit()

            logger.info(f"Error email sent successfully" +
                  (f" with attachment: {attachment_path}" if attachment_path else ""))

        except Exception as e:
            logger.info(f"Error sending email: {str(e)}")