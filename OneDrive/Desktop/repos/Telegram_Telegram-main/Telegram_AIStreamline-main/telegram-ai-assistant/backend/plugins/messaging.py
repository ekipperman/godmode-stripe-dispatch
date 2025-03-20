import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime
from twilio.rest import Client
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

class MessagingAutomation:
    def __init__(self, config: Dict[str, Any]):
        """Initialize messaging automation with configuration"""
        self.config = config
        self.messaging_config = config["plugins"]["messaging"]
        
        # Initialize email client
        if self.messaging_config["email"]["enabled"]:
            self._init_email_client()
        
        # Initialize SMS client (Twilio)
        if self.messaging_config["sms"]["enabled"]:
            self._init_sms_client()
        
        logger.info("Messaging Automation initialized successfully")

    def _init_email_client(self):
        """Initialize email client with SSL"""
        try:
            self.email_config = self.messaging_config["email"]
            self.email_context = ssl.create_default_context()
            logger.info("Email client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing email client: {str(e)}")
            self.email_config = None

    def _init_sms_client(self):
        """Initialize Twilio client for SMS"""
        try:
            sms_config = self.messaging_config["sms"]
            self.sms_client = Client(
                sms_config["account_sid"],
                sms_config["auth_token"]
            )
            self.sms_from_number = sms_config["from_number"]
            logger.info("SMS client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing SMS client: {str(e)}")
            self.sms_client = None

    async def send_email(self, 
                        to_email: str, 
                        subject: str, 
                        content: Dict[str, str],
                        template_name: Optional[str] = None) -> Dict[str, Any]:
        """Send an email using configured SMTP server"""
        try:
            if not self.email_config:
                raise Exception("Email client not initialized")

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.email_config["smtp_user"]
            message["To"] = to_email

            # Create HTML and plain text versions
            text_content = content.get("text", "")
            html_content = content.get("html", "") or self._convert_to_html(text_content)

            # Attach parts
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            message.attach(part1)
            message.attach(part2)

            # Send email
            with smtplib.SMTP(
                self.email_config["smtp_host"],
                self.email_config["smtp_port"]
            ) as server:
                server.starttls(context=self.email_context)
                server.login(
                    self.email_config["smtp_user"],
                    self.email_config["smtp_password"]
                )
                server.send_message(message)

            return {
                "status": "success",
                "to": to_email,
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def send_bulk_email(self, 
                            recipients: List[Dict[str, Any]], 
                            subject: str,
                            content: Dict[str, str],
                            template_name: Optional[str] = None) -> Dict[str, Any]:
        """Send bulk emails with personalization"""
        results = {
            "successful": [],
            "failed": [],
            "timestamp": datetime.now().isoformat()
        }

        for recipient in recipients:
            try:
                # Personalize content
                personalized_content = self._personalize_content(
                    content,
                    recipient
                )

                # Send email
                result = await self.send_email(
                    recipient["email"],
                    subject,
                    personalized_content,
                    template_name
                )

                if result["status"] == "success":
                    results["successful"].append(recipient["email"])
                else:
                    results["failed"].append({
                        "email": recipient["email"],
                        "error": result["error"]
                    })

            except Exception as e:
                logger.error(f"Error sending bulk email to {recipient['email']}: {str(e)}")
                results["failed"].append({
                    "email": recipient["email"],
                    "error": str(e)
                })

        return results

    async def send_sms(self, 
                      to_number: str, 
                      message: str) -> Dict[str, Any]:
        """Send SMS using Twilio"""
        try:
            if not self.sms_client:
                raise Exception("SMS client not initialized")

            # Send message
            message = self.sms_client.messages.create(
                body=message,
                from_=self.sms_from_number,
                to=to_number
            )

            return {
                "status": "success",
                "message_id": message.sid,
                "to": to_number,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def send_bulk_sms(self, 
                           recipients: List[Dict[str, Any]], 
                           message: str) -> Dict[str, Any]:
        """Send bulk SMS messages with personalization"""
        results = {
            "successful": [],
            "failed": [],
            "timestamp": datetime.now().isoformat()
        }

        for recipient in recipients:
            try:
                # Personalize message
                personalized_message = self._personalize_content(
                    {"text": message},
                    recipient
                )["text"]

                # Send SMS
                result = await self.send_sms(
                    recipient["phone"],
                    personalized_message
                )

                if result["status"] == "success":
                    results["successful"].append(recipient["phone"])
                else:
                    results["failed"].append({
                        "phone": recipient["phone"],
                        "error": result["error"]
                    })

            except Exception as e:
                logger.error(f"Error sending bulk SMS to {recipient['phone']}: {str(e)}")
                results["failed"].append({
                    "phone": recipient["phone"],
                    "error": str(e)
                })

        return results

    def _personalize_content(self, 
                           content: Dict[str, str], 
                           recipient: Dict[str, Any]) -> Dict[str, str]:
        """Personalize content with recipient data"""
        personalized = {}
        
        for content_type, text in content.items():
            personalized_text = text
            
            # Replace placeholders with recipient data
            for key, value in recipient.items():
                placeholder = f"{{{key}}}"
                if placeholder in text:
                    personalized_text = personalized_text.replace(
                        placeholder,
                        str(value)
                    )
            
            personalized[content_type] = personalized_text
        
        return personalized

    def _convert_to_html(self, text: str) -> str:
        """Convert plain text to simple HTML"""
        # Replace newlines with <br> tags
        html = text.replace("\n", "<br>")
        
        # Wrap in HTML structure
        html = f"""
        <html>
            <body>
                <div style="font-family: Arial, sans-serif; line-height: 1.6;">
                    {html}
                </div>
            </body>
        </html>
        """
        
        return html

    async def get_analytics(self) -> Dict[str, Any]:
        """Get messaging analytics"""
        analytics = {
            "email": await self._get_email_analytics(),
            "sms": await self._get_sms_analytics(),
            "timestamp": datetime.now().isoformat()
        }
        
        return analytics

    async def _get_email_analytics(self) -> Dict[str, Any]:
        """Get email analytics"""
        # This would typically integrate with your email service's analytics API
        # For now, returning placeholder data
        return {
            "total_sent": 0,
            "delivered": 0,
            "opened": 0,
            "clicked": 0,
            "bounced": 0
        }

    async def _get_sms_analytics(self) -> Dict[str, Any]:
        """Get SMS analytics from Twilio"""
        try:
            if not self.sms_client:
                raise Exception("SMS client not initialized")

            # Get messages from the past 30 days
            messages = self.sms_client.messages.list(
                limit=1000,
                date_sent_after=datetime.now().replace(
                    day=1
                ).isoformat()
            )

            analytics = {
                "total_sent": len(messages),
                "delivered": sum(1 for msg in messages if msg.status == "delivered"),
                "failed": sum(1 for msg in messages if msg.status == "failed"),
                "cost": sum(float(msg.price or 0) for msg in messages)
            }

            return analytics

        except Exception as e:
            logger.error(f"Error getting SMS analytics: {str(e)}")
            return {
                "error": str(e)
            }

    async def schedule_message(self, 
                             message_type: str,
                             recipient: Dict[str, Any],
                             content: Dict[str, Any],
                             schedule_time: datetime) -> Dict[str, Any]:
        """Schedule a message for future delivery"""
        try:
            # Calculate delay in seconds
            now = datetime.now()
            delay = (schedule_time - now).total_seconds()
            
            if delay < 0:
                raise ValueError("Schedule time must be in the future")

            # Create task for delayed sending
            if message_type == "email":
                asyncio.create_task(
                    self._delayed_email(
                        delay,
                        recipient["email"],
                        content["subject"],
                        content
                    )
                )
            elif message_type == "sms":
                asyncio.create_task(
                    self._delayed_sms(
                        delay,
                        recipient["phone"],
                        content["message"]
                    )
                )
            else:
                raise ValueError(f"Unknown message type: {message_type}")

            return {
                "status": "scheduled",
                "message_type": message_type,
                "recipient": recipient,
                "schedule_time": schedule_time.isoformat(),
                "timestamp": now.isoformat()
            }

        except Exception as e:
            logger.error(f"Error scheduling message: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _delayed_email(self, 
                           delay: float,
                           to_email: str,
                           subject: str,
                           content: Dict[str, str]):
        """Send an email after a delay"""
        await asyncio.sleep(delay)
        await self.send_email(to_email, subject, content)

    async def _delayed_sms(self,
                          delay: float,
                          to_number: str,
                          message: str):
        """Send an SMS after a delay"""
        await asyncio.sleep(delay)
        await self.send_sms(to_number, message)
