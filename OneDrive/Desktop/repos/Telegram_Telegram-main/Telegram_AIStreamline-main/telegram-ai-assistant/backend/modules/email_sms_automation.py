import logging
from typing import Dict, Any, List, Optional
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content, Subject
from twilio.rest import Client
import asyncio
from datetime import datetime
import aiohttp
from pathlib import Path
import json
import re

logger = logging.getLogger(__name__)

class EmailSMSAutomation:
    def __init__(self, config: Dict[str, Any]):
        """Initialize email and SMS automation with configuration"""
        self.config = config
        self.messaging_config = config["plugins"]["messaging"]
        
        # Initialize SendGrid client for email
        if self.messaging_config["email"]["enabled"]:
            self.sendgrid_client = sendgrid.SendGridAPIClient(
                api_key=self.messaging_config["email"]["smtp_password"]
            )
            self.default_from_email = self.messaging_config["email"]["smtp_user"]
            
        # Initialize Twilio client for SMS
        if self.messaging_config["sms"]["enabled"]:
            self.twilio_client = Client(
                self.messaging_config["sms"]["account_sid"],
                self.messaging_config["sms"]["auth_token"]
            )
            self.twilio_from_number = self.messaging_config["sms"]["from_number"]
        
        # Initialize message history
        self.message_history: List[Dict[str, Any]] = []
        
        # Initialize templates
        self.email_templates = self._load_email_templates()
        self.sms_templates = self._load_sms_templates()
        
        logger.info("Email & SMS Automation initialized successfully")

    def _load_email_templates(self) -> Dict[str, Any]:
        """Load email templates from configuration"""
        try:
            templates_path = Path(__file__).parent / "templates" / "email_templates.json"
            if templates_path.exists():
                with open(templates_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading email templates: {str(e)}")
            return {}

    def _load_sms_templates(self) -> Dict[str, Any]:
        """Load SMS templates from configuration"""
        try:
            templates_path = Path(__file__).parent / "templates" / "sms_templates.json"
            if templates_path.exists():
                with open(templates_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading SMS templates: {str(e)}")
            return {}

    async def send_email(self, to_email: str, subject: str, content: str, 
                        template_name: Optional[str] = None, template_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send an email"""
        try:
            if not self.messaging_config["email"]["enabled"]:
                raise ValueError("Email functionality is not enabled")
            
            # Use template if specified
            if template_name and template_name in self.email_templates:
                template = self.email_templates[template_name]
                content = self._process_template(template["content"], template_data or {})
                subject = self._process_template(template["subject"], template_data or {})
            
            # Validate email address
            if not self._validate_email(to_email):
                raise ValueError(f"Invalid email address: {to_email}")
            
            # Create message
            message = Mail(
                from_email=Email(self.default_from_email),
                to_emails=To(to_email),
                subject=Subject(subject),
                plain_text_content=Content("text/plain", content)
            )
            
            # Send email
            response = self.sendgrid_client.send(message)
            
            # Record in history
            self._record_message("email", {
                "to": to_email,
                "subject": subject,
                "content": content,
                "template": template_name if template_name else None,
                "status_code": response.status_code
            })
            
            return {
                "success": 200 <= response.status_code < 300,
                "message_id": response.headers.get('X-Message-Id'),
                "status_code": response.status_code
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def send_sms(self, to_number: str, message: str,
                      template_name: Optional[str] = None, template_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send an SMS"""
        try:
            if not self.messaging_config["sms"]["enabled"]:
                raise ValueError("SMS functionality is not enabled")
            
            # Use template if specified
            if template_name and template_name in self.sms_templates:
                template = self.sms_templates[template_name]
                message = self._process_template(template["content"], template_data or {})
            
            # Validate phone number
            if not self._validate_phone_number(to_number):
                raise ValueError(f"Invalid phone number: {to_number}")
            
            # Send SMS
            sms = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_from_number,
                to=to_number
            )
            
            # Record in history
            self._record_message("sms", {
                "to": to_number,
                "content": message,
                "template": template_name if template_name else None,
                "status": sms.status
            })
            
            return {
                "success": True,
                "message_id": sms.sid,
                "status": sms.status
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def send_bulk_email(self, recipients: List[Dict[str, Any]], subject: str, content: str,
                            template_name: Optional[str] = None) -> Dict[str, Any]:
        """Send bulk emails"""
        try:
            if not self.messaging_config["email"]["enabled"]:
                raise ValueError("Email functionality is not enabled")
            
            results = []
            for recipient in recipients:
                # Process recipient-specific template data
                template_data = recipient.get("template_data", {})
                template_data.update({
                    "name": recipient.get("name", ""),
                    "email": recipient["email"]
                })
                
                # Send individual email
                result = await self.send_email(
                    recipient["email"],
                    subject,
                    content,
                    template_name,
                    template_data
                )
                
                results.append({
                    "email": recipient["email"],
                    "success": result["success"],
                    "error": result.get("error")
                })
                
                # Rate limiting to avoid API limits
                await asyncio.sleep(0.1)
            
            return {
                "success": True,
                "results": results,
                "total_sent": len([r for r in results if r["success"]]),
                "total_failed": len([r for r in results if not r["success"]])
            }
            
        except Exception as e:
            logger.error(f"Error sending bulk emails: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def send_bulk_sms(self, recipients: List[Dict[str, Any]], message: str,
                           template_name: Optional[str] = None) -> Dict[str, Any]:
        """Send bulk SMS messages"""
        try:
            if not self.messaging_config["sms"]["enabled"]:
                raise ValueError("SMS functionality is not enabled")
            
            results = []
            for recipient in recipients:
                # Process recipient-specific template data
                template_data = recipient.get("template_data", {})
                template_data.update({
                    "name": recipient.get("name", ""),
                    "phone": recipient["phone"]
                })
                
                # Send individual SMS
                result = await self.send_sms(
                    recipient["phone"],
                    message,
                    template_name,
                    template_data
                )
                
                results.append({
                    "phone": recipient["phone"],
                    "success": result["success"],
                    "error": result.get("error")
                })
                
                # Rate limiting to avoid API limits
                await asyncio.sleep(0.1)
            
            return {
                "success": True,
                "results": results,
                "total_sent": len([r for r in results if r["success"]]),
                "total_failed": len([r for r in results if not r["success"]])
            }
            
        except Exception as e:
            logger.error(f"Error sending bulk SMS: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _process_template(self, template: str, data: Dict[str, Any]) -> str:
        """Process a template with provided data"""
        for key, value in data.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template

    def _validate_email(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format"""
        pattern = r'^\+?1?\d{9,15}$'
        return bool(re.match(pattern, phone))

    def _record_message(self, message_type: str, details: Dict[str, Any]) -> None:
        """Record message in history"""
        self.message_history.append({
            "type": message_type,
            "timestamp": datetime.now().isoformat(),
            "details": details
        })

    async def get_message_history(self, message_type: Optional[str] = None, 
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get message history with optional filtering"""
        history = self.message_history
        
        if message_type:
            history = [msg for msg in history if msg["type"] == message_type]
            
        if limit:
            history = history[-limit:]
            
        return history

    async def get_analytics(self) -> Dict[str, Any]:
        """Get messaging analytics"""
        email_messages = [msg for msg in self.message_history if msg["type"] == "email"]
        sms_messages = [msg for msg in self.message_history if msg["type"] == "sms"]
        
        return {
            "email": {
                "total_sent": len(email_messages),
                "successful": len([msg for msg in email_messages 
                                 if msg["details"].get("status_code", 0) < 300]),
                "failed": len([msg for msg in email_messages 
                             if msg["details"].get("status_code", 0) >= 300])
            },
            "sms": {
                "total_sent": len(sms_messages),
                "successful": len([msg for msg in sms_messages 
                                 if msg["details"].get("status") == "delivered"]),
                "failed": len([msg for msg in sms_messages 
                             if msg["details"].get("status") not in ["delivered", "sent"]])
            },
            "recent_messages": self.message_history[-5:]  # Last 5 messages
        }

    async def create_template(self, template_type: str, name: str, content: str,
                            subject: Optional[str] = None) -> Dict[str, Any]:
        """Create a new message template"""
        try:
            if template_type == "email":
                if not subject:
                    raise ValueError("Subject is required for email templates")
                    
                self.email_templates[name] = {
                    "subject": subject,
                    "content": content
                }
                
            elif template_type == "sms":
                self.sms_templates[name] = {
                    "content": content
                }
                
            else:
                raise ValueError(f"Invalid template type: {template_type}")
            
            # Save templates to file
            await self._save_templates()
            
            return {
                "success": True,
                "template_name": name,
                "type": template_type
            }
            
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _save_templates(self) -> None:
        """Save templates to files"""
        try:
            templates_dir = Path(__file__).parent / "templates"
            templates_dir.mkdir(exist_ok=True)
            
            # Save email templates
            email_templates_path = templates_dir / "email_templates.json"
            with open(email_templates_path, 'w') as f:
                json.dump(self.email_templates, f, indent=2)
            
            # Save SMS templates
            sms_templates_path = templates_dir / "sms_templates.json"
            with open(sms_templates_path, 'w') as f:
                json.dump(self.sms_templates, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving templates: {str(e)}")
            raise
