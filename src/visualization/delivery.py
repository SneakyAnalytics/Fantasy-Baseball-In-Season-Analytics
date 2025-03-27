# src/visualization/delivery.py
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime

logger = logging.getLogger(__name__)

class ReportDelivery:
    """Handle delivery of reports through various channels."""
    
    @staticmethod
    def deliver_email(subject, body, recipients, sender=None, smtp_server=None, 
                     smtp_port=None, username=None, password=None, 
                     attachments=None, use_tls=True, html_content=None):
        """
        Send a report via email.
        
        Args:
            subject: Email subject
            body: Email body content (plain text)
            recipients: List of recipient email addresses
            sender: Sender email address (optional)
            smtp_server: SMTP server address (optional)
            smtp_port: SMTP server port (optional)
            username: SMTP authentication username (optional)
            password: SMTP authentication password (optional)
            attachments: List of file paths to attach (optional)
            use_tls: Whether to use TLS encryption (default: True)
            html_content: HTML version of the email (optional)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Import settings here to avoid circular imports
        from config import settings
        
        # Use settings for missing parameters
        if sender is None:
            sender = getattr(settings, 'EMAIL_FROM', None)
        if smtp_server is None:
            smtp_server = getattr(settings, 'EMAIL_SMTP_SERVER', None)
        if smtp_port is None:
            smtp_port = getattr(settings, 'EMAIL_SMTP_PORT', 587)
        if username is None:
            username = getattr(settings, 'EMAIL_USERNAME', None)
        if password is None:
            password = getattr(settings, 'EMAIL_PASSWORD', None)
        
        # Validate required parameters
        if not sender or not recipients or not smtp_server:
            logger.error("Missing required email parameters")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Add plain text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add HTML body if provided
            if html_content:
                msg.attach(MIMEText(html_content, 'html'))
            
            # If there are attachments, convert to mixed multipart
            if attachments:
                # Create a new mixed message
                mixed_msg = MIMEMultipart('mixed')
                # Copy the headers
                for key, value in msg.items():
                    mixed_msg[key] = value
                
                # Attach the alternative part (plain text and HTML)
                mixed_msg.attach(msg)
                
                # Add attachments
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as file:
                            part = MIMEApplication(file.read(), Name=os.path.basename(file_path))
                            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                            mixed_msg.attach(part)
                    else:
                        logger.warning(f"Attachment not found: {file_path}")
                
                # Replace the message with the mixed multipart
                msg = mixed_msg
            
            # Connect to server and send
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                server.starttls()
            
            # Login if credentials provided
            if username and password:
                server.login(username, password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {', '.join(recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    def save_to_file(content, file_path, append=False):
        """
        Save report content to a file.
        
        Args:
            content: Report content
            file_path: Path to save file
            append: Whether to append to existing file (default: False)
            
        Returns:
            bool: True if file was saved successfully, False otherwise
        """
        try:
            mode = 'a' if append else 'w'
            with open(file_path, mode) as f:
                f.write(content)
            
            logger.info(f"Report saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save report: {str(e)}")
            return False

    @staticmethod
    def log_to_history(report_type, summary, output_path):
        """
        Log report to history file for tracking.
        
        Args:
            report_type: Type of report (e.g., 'daily', 'weekly')
            summary: Brief summary of the report
            output_path: Path to the generated report
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        try:
            # Import settings here to avoid circular imports
            from config import settings
            
            # Determine history file location
            history_dir = getattr(settings, 'REPORT_DIR', 'reports')
            os.makedirs(history_dir, exist_ok=True)
            
            history_path = os.path.join(history_dir, 'report_history.log')
            
            # Format log entry
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"{timestamp} | {report_type} | {summary} | {output_path}\n"
            
            # Append to history file
            with open(history_path, 'a') as f:
                f.write(log_entry)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log to history: {str(e)}")
            return False