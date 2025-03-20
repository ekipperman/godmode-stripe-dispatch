import logging
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
from datetime import datetime
import json
from pathlib import Path
from sentry_config import capture_exception
from .whitelabel_config import WhitelabelConfig
from .email_sms_automation import EmailSMSAutomation

logger = logging.getLogger(__name__)

class ClientOnboarding:
    def __init__(self, config: Dict[str, Any]):
        """Initialize client onboarding automation"""
        self.config = config
        self.onboarding_config = config["plugins"]["onboarding"]
        self.whitelabel = WhitelabelConfig(config)
        self.automation = EmailSMSAutomation(config)
        
        # Load onboarding steps template
        self.steps_template = self._load_steps_template()
        
        # Initialize progress tracking
        self.progress_tracking: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Client Onboarding Automation initialized")

    def _load_steps_template(self) -> Dict[str, Any]:
        """Load onboarding steps template"""
        try:
            template_path = Path(__file__).parent / "templates" / "onboarding_steps.json"
            with open(template_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading onboarding steps template: {str(e)}")
            capture_exception(e)
            return {
                "steps": [
                    {
                        "id": "basic_info",
                        "name": "Basic Information",
                        "required": True,
                        "order": 1
                    },
                    {
                        "id": "branding",
                        "name": "Branding Setup",
                        "required": True,
                        "order": 2
                    },
                    {
                        "id": "features",
                        "name": "Feature Selection",
                        "required": True,
                        "order": 3
                    },
                    {
                        "id": "integrations",
                        "name": "Integration Setup",
                        "required": False,
                        "order": 4
                    }
                ]
            }

    async def initialize_client(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize new client onboarding"""
        try:
            client_id = client_data["client_id"]
            
            # Create initial whitelabel config
            config = await self.whitelabel.create_default_config(client_id)
            
            # Initialize progress tracking
            self.progress_tracking[client_id] = {
                "started_at": datetime.now().isoformat(),
                "current_step": "basic_info",
                "completed_steps": [],
                "pending_steps": [step["id"] for step in self.steps_template["steps"]],
                "status": "in_progress"
            }
            
            # Send welcome email
            await self._send_welcome_message(client_data)
            
            return {
                "success": True,
                "client_id": client_id,
                "config": config,
                "next_step": "basic_info"
            }

        except Exception as e:
            logger.error(f"Error initializing client: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def update_step(self, client_id: str, step_id: str, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update onboarding step data"""
        try:
            # Validate step exists
            if step_id not in [step["id"] for step in self.steps_template["steps"]]:
                raise ValueError(f"Invalid step ID: {step_id}")
            
            # Update whitelabel config based on step
            if step_id == "basic_info":
                await self.whitelabel.update_client_info(client_id, step_data)
            elif step_id == "branding":
                await self.whitelabel.update_branding(client_id, step_data)
            elif step_id == "features":
                await self.whitelabel.update_features(client_id, step_data)
            elif step_id == "integrations":
                await self.whitelabel.update_integrations(client_id, step_data)
            
            # Update progress tracking
            self._update_progress(client_id, step_id)
            
            # Send step completion notification
            await self._send_step_completion_message(client_id, step_id)
            
            # Get next step
            next_step = self._get_next_step(client_id)
            
            return {
                "success": True,
                "next_step": next_step,
                "progress": self.progress_tracking[client_id]
            }

        except Exception as e:
            logger.error(f"Error updating step: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    def _update_progress(self, client_id: str, completed_step: str) -> None:
        """Update client's onboarding progress"""
        progress = self.progress_tracking[client_id]
        
        # Move step from pending to completed
        if completed_step in progress["pending_steps"]:
            progress["pending_steps"].remove(completed_step)
            progress["completed_steps"].append(completed_step)
        
        # Update current step
        if progress["pending_steps"]:
            progress["current_step"] = progress["pending_steps"][0]
        else:
            progress["current_step"] = None
            progress["status"] = "completed"
            progress["completed_at"] = datetime.now().isoformat()

    def _get_next_step(self, client_id: str) -> Optional[str]:
        """Get client's next onboarding step"""
        progress = self.progress_tracking[client_id]
        return progress["current_step"]

    async def _send_welcome_message(self, client_data: Dict[str, Any]) -> None:
        """Send welcome email and SMS"""
        try:
            # Send welcome email
            await self.automation.send_email(
                template_id="welcome_email",
                recipient_email=client_data["contact_email"],
                data={
                    "client_name": client_data["name"],
                    "login_url": f"https://dashboard.yourplatform.com/{client_data['client_id']}"
                }
            )
            
            # Send welcome SMS if phone provided
            if "phone" in client_data:
                await self.automation.send_sms(
                    template_id="welcome_sms",
                    recipient_phone=client_data["phone"],
                    data={
                        "client_name": client_data["name"]
                    }
                )

        except Exception as e:
            logger.error(f"Error sending welcome message: {str(e)}")
            capture_exception(e)

    async def _send_step_completion_message(self, client_id: str, step_id: str) -> None:
        """Send step completion notification"""
        try:
            client_config = await self.whitelabel.load_client_config(client_id)
            
            # Send completion email
            await self.automation.send_email(
                template_id="step_completion_email",
                recipient_email=client_config["client_info"]["contact_email"],
                data={
                    "client_name": client_config["client_info"]["name"],
                    "step_name": next(step["name"] for step in self.steps_template["steps"] if step["id"] == step_id),
                    "next_step": self._get_next_step(client_id)
                }
            )

        except Exception as e:
            logger.error(f"Error sending step completion message: {str(e)}")
            capture_exception(e)

    async def send_reminder(self, client_id: str) -> Dict[str, Any]:
        """Send reminder for incomplete onboarding"""
        try:
            progress = self.progress_tracking.get(client_id)
            if not progress or progress["status"] == "completed":
                return {
                    "success": False,
                    "error": "No incomplete onboarding found"
                }
            
            client_config = await self.whitelabel.load_client_config(client_id)
            
            # Send reminder email
            await self.automation.send_email(
                template_id="onboarding_reminder_email",
                recipient_email=client_config["client_info"]["contact_email"],
                data={
                    "client_name": client_config["client_info"]["name"],
                    "current_step": progress["current_step"],
                    "pending_steps": len(progress["pending_steps"]),
                    "resume_url": f"https://dashboard.yourplatform.com/{client_id}/onboarding"
                }
            )
            
            return {
                "success": True,
                "message": "Reminder sent successfully"
            }

        except Exception as e:
            logger.error(f"Error sending reminder: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def get_progress(self, client_id: str) -> Dict[str, Any]:
        """Get client's onboarding progress"""
        try:
            progress = self.progress_tracking.get(client_id)
            if not progress:
                return {
                    "success": False,
                    "error": "Client not found"
                }
            
            return {
                "success": True,
                "progress": progress
            }

        except Exception as e:
            logger.error(f"Error getting progress: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def get_incomplete_onboardings(self) -> List[Dict[str, Any]]:
        """Get list of incomplete onboardings"""
        try:
            incomplete = []
            for client_id, progress in self.progress_tracking.items():
                if progress["status"] != "completed":
                    client_config = await self.whitelabel.load_client_config(client_id)
                    incomplete.append({
                        "client_id": client_id,
                        "name": client_config["client_info"]["name"],
                        "started_at": progress["started_at"],
                        "current_step": progress["current_step"],
                        "pending_steps": progress["pending_steps"]
                    })
            
            return incomplete

        except Exception as e:
            logger.error(f"Error getting incomplete onboardings: {str(e)}")
            capture_exception(e)
            return []
