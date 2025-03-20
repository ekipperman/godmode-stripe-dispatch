import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import json
from pathlib import Path
from email_sms_automation import EmailSMSAutomation

logger = logging.getLogger(__name__)

class LeadNurturing:
    def __init__(self, config: Dict[str, Any]):
        """Initialize lead nurturing with configuration"""
        self.config = config
        self.nurturing_config = config["plugins"]["lead_nurturing"]
        
        # Initialize messaging module for communications
        self.messaging = EmailSMSAutomation(config)
        
        # Load campaign templates
        self.campaign_templates = self._load_campaign_templates()
        
        # Initialize lead tracking
        self.leads: Dict[str, Dict[str, Any]] = {}
        self.campaigns: Dict[str, Dict[str, Any]] = {}
        
        # Load existing data
        self._load_data()
        
        # Start background task for campaign processing
        self.processing = True
        asyncio.create_task(self._process_campaigns())
        
        logger.info("Lead Nurturing initialized successfully")

    def _load_campaign_templates(self) -> Dict[str, Any]:
        """Load campaign templates from configuration"""
        try:
            templates_path = Path(__file__).parent / "templates" / "nurturing_campaigns.json"
            if templates_path.exists():
                with open(templates_path, 'r') as f:
                    return json.load(f)
            return self._get_default_templates()
        except Exception as e:
            logger.error(f"Error loading campaign templates: {str(e)}")
            return self._get_default_templates()

    def _get_default_templates(self) -> Dict[str, Any]:
        """Get default campaign templates"""
        return {
            "welcome_series": {
                "name": "Welcome Series",
                "steps": [
                    {
                        "delay_days": 0,
                        "type": "email",
                        "template": "welcome_email",
                        "subject": "Welcome to Our Service!",
                        "content": "Hi {name},\n\nWelcome aboard! We're excited to have you..."
                    },
                    {
                        "delay_days": 3,
                        "type": "email",
                        "template": "getting_started",
                        "subject": "Getting Started Guide",
                        "content": "Hi {name},\n\nHere are some tips to get started..."
                    },
                    {
                        "delay_days": 7,
                        "type": "email",
                        "template": "follow_up",
                        "subject": "How are you finding our service?",
                        "content": "Hi {name},\n\nWe'd love to hear your feedback..."
                    }
                ]
            },
            "re_engagement": {
                "name": "Re-engagement Campaign",
                "steps": [
                    {
                        "delay_days": 0,
                        "type": "email",
                        "template": "miss_you",
                        "subject": "We miss you!",
                        "content": "Hi {name},\n\nWe noticed you haven't been around lately..."
                    },
                    {
                        "delay_days": 5,
                        "type": "email",
                        "template": "special_offer",
                        "subject": "Special Offer Just for You",
                        "content": "Hi {name},\n\nHere's a special offer to welcome you back..."
                    }
                ]
            }
        }

    def _load_data(self) -> None:
        """Load existing lead and campaign data"""
        try:
            data_dir = Path(__file__).parent / "data"
            data_dir.mkdir(exist_ok=True)
            
            # Load leads
            leads_path = data_dir / "leads.json"
            if leads_path.exists():
                with open(leads_path, 'r') as f:
                    self.leads = json.load(f)
            
            # Load campaigns
            campaigns_path = data_dir / "campaigns.json"
            if campaigns_path.exists():
                with open(campaigns_path, 'r') as f:
                    self.campaigns = json.load(f)
                    
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")

    async def _save_data(self) -> None:
        """Save lead and campaign data"""
        try:
            data_dir = Path(__file__).parent / "data"
            data_dir.mkdir(exist_ok=True)
            
            # Save leads
            leads_path = data_dir / "leads.json"
            with open(leads_path, 'w') as f:
                json.dump(self.leads, f, indent=2)
            
            # Save campaigns
            campaigns_path = data_dir / "campaigns.json"
            with open(campaigns_path, 'w') as f:
                json.dump(self.campaigns, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")

    async def nurture_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start nurturing a new lead"""
        try:
            lead_id = lead_data["id"]
            
            # Store lead information
            self.leads[lead_id] = {
                "email": lead_data["email"],
                "name": lead_data.get("name", ""),
                "phone": lead_data.get("phone", ""),
                "source": lead_data.get("source", "unknown"),
                "status": lead_data.get("status", "new"),
                "created_at": datetime.now().isoformat(),
                "last_contact": None,
                "engagement_score": 0,
                "campaign_history": []
            }
            
            # Start welcome campaign
            campaign_id = await self._start_campaign(lead_id, "welcome_series")
            
            # Save data
            await self._save_data()
            
            return {
                "success": True,
                "lead_id": lead_id,
                "campaign_id": campaign_id
            }
            
        except Exception as e:
            logger.error(f"Error nurturing lead: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _start_campaign(self, lead_id: str, campaign_template: str) -> str:
        """Start a campaign for a lead"""
        try:
            if campaign_template not in self.campaign_templates:
                raise ValueError(f"Invalid campaign template: {campaign_template}")
            
            campaign_id = f"campaign_{lead_id}_{len(self.leads[lead_id]['campaign_history']) + 1}"
            
            # Create campaign instance
            self.campaigns[campaign_id] = {
                "lead_id": lead_id,
                "template": campaign_template,
                "status": "active",
                "current_step": 0,
                "started_at": datetime.now().isoformat(),
                "next_action_at": datetime.now().isoformat(),
                "completed_steps": []
            }
            
            # Add to lead's campaign history
            self.leads[lead_id]["campaign_history"].append({
                "campaign_id": campaign_id,
                "template": campaign_template,
                "started_at": datetime.now().isoformat(),
                "status": "active"
            })
            
            return campaign_id
            
        except Exception as e:
            logger.error(f"Error starting campaign: {str(e)}")
            raise

    async def _process_campaigns(self) -> None:
        """Process active campaigns"""
        while self.processing:
            try:
                current_time = datetime.now()
                
                for campaign_id, campaign in self.campaigns.items():
                    if campaign["status"] != "active":
                        continue
                    
                    # Check if it's time for next action
                    next_action = datetime.fromisoformat(campaign["next_action_at"])
                    if current_time >= next_action:
                        await self._execute_campaign_step(campaign_id)
                
                # Save data after processing
                await self._save_data()
                
                # Wait before next processing cycle
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error processing campaigns: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _execute_campaign_step(self, campaign_id: str) -> None:
        """Execute a step in a campaign"""
        try:
            campaign = self.campaigns[campaign_id]
            lead = self.leads[campaign["lead_id"]]
            template = self.campaign_templates[campaign["template"]]
            current_step = template["steps"][campaign["current_step"]]
            
            # Prepare message data
            message_data = {
                "name": lead["name"],
                "email": lead["email"],
                "phone": lead["phone"]
            }
            
            # Send message based on type
            if current_step["type"] == "email":
                result = await self.messaging.send_email(
                    lead["email"],
                    current_step["subject"],
                    current_step["content"],
                    current_step.get("template"),
                    message_data
                )
            elif current_step["type"] == "sms":
                result = await self.messaging.send_sms(
                    lead["phone"],
                    current_step["content"],
                    current_step.get("template"),
                    message_data
                )
            
            # Record step completion
            campaign["completed_steps"].append({
                "step": campaign["current_step"],
                "executed_at": datetime.now().isoformat(),
                "success": result["success"],
                "details": result
            })
            
            # Update campaign status
            campaign["current_step"] += 1
            if campaign["current_step"] >= len(template["steps"]):
                campaign["status"] = "completed"
                # Update lead's campaign history
                for camp in lead["campaign_history"]:
                    if camp["campaign_id"] == campaign_id:
                        camp["status"] = "completed"
                        camp["completed_at"] = datetime.now().isoformat()
            else:
                # Schedule next step
                next_step = template["steps"][campaign["current_step"]]
                campaign["next_action_at"] = (
                    datetime.now() + timedelta(days=next_step["delay_days"])
                ).isoformat()
            
            # Update lead's last contact
            lead["last_contact"] = datetime.now().isoformat()
            
            # Update engagement score
            if result["success"]:
                lead["engagement_score"] += 1
            
        except Exception as e:
            logger.error(f"Error executing campaign step: {str(e)}")
            # Mark campaign as failed
            campaign["status"] = "failed"
            campaign["error"] = str(e)

    async def get_lead_status(self, lead_id: str) -> Dict[str, Any]:
        """Get status of a lead"""
        try:
            if lead_id not in self.leads:
                raise ValueError(f"Lead not found: {lead_id}")
            
            lead = self.leads[lead_id]
            active_campaigns = [
                camp for camp in lead["campaign_history"]
                if camp["status"] == "active"
            ]
            
            return {
                "success": True,
                "lead": lead,
                "active_campaigns": active_campaigns
            }
            
        except Exception as e:
            logger.error(f"Error getting lead status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_campaign_status(self, campaign_id: str) -> Dict[str, Any]:
        """Get status of a campaign"""
        try:
            if campaign_id not in self.campaigns:
                raise ValueError(f"Campaign not found: {campaign_id}")
            
            return {
                "success": True,
                "campaign": self.campaigns[campaign_id]
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def pause_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Pause an active campaign"""
        try:
            if campaign_id not in self.campaigns:
                raise ValueError(f"Campaign not found: {campaign_id}")
            
            campaign = self.campaigns[campaign_id]
            if campaign["status"] == "active":
                campaign["status"] = "paused"
                campaign["paused_at"] = datetime.now().isoformat()
                
                # Update lead's campaign history
                lead = self.leads[campaign["lead_id"]]
                for camp in lead["campaign_history"]:
                    if camp["campaign_id"] == campaign_id:
                        camp["status"] = "paused"
                
                await self._save_data()
                
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "status": "paused"
                }
            else:
                return {
                    "success": False,
                    "error": f"Campaign is not active (current status: {campaign['status']})"
                }
            
        except Exception as e:
            logger.error(f"Error pausing campaign: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def resume_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Resume a paused campaign"""
        try:
            if campaign_id not in self.campaigns:
                raise ValueError(f"Campaign not found: {campaign_id}")
            
            campaign = self.campaigns[campaign_id]
            if campaign["status"] == "paused":
                campaign["status"] = "active"
                campaign["resumed_at"] = datetime.now().isoformat()
                
                # Update lead's campaign history
                lead = self.leads[campaign["lead_id"]]
                for camp in lead["campaign_history"]:
                    if camp["campaign_id"] == campaign_id:
                        camp["status"] = "active"
                
                await self._save_data()
                
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "status": "active"
                }
            else:
                return {
                    "success": False,
                    "error": f"Campaign is not paused (current status: {campaign['status']})"
                }
            
        except Exception as e:
            logger.error(f"Error resuming campaign: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.processing = False
