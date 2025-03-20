import logging
from typing import Dict, Any, Optional
from .ai_chatbot import AIChatbot
from .voice_command import VoiceCommand
from .crm_integration import CRMIntegration
from .social_media import SocialMediaAutomation
from .messaging import MessagingAutomation
from .analytics import AnalyticsReporting

logger = logging.getLogger(__name__)

class PluginManager:
    def __init__(self, config: Dict[str, Any]):
        """Initialize plugin manager with configuration"""
        self.config = config
        self.plugins = {}
        self._initialize_plugins()
        
        logger.info("Plugin Manager initialized successfully")

    def _initialize_plugins(self):
        """Initialize all enabled plugins"""
        try:
            # Initialize AI Chatbot
            if self.config["plugins"]["ai_chatbot"]["enabled"]:
                self.plugins["ai_chatbot"] = AIChatbot(self.config)
                logger.info("AI Chatbot plugin initialized")

            # Initialize Voice Command
            if self.config["plugins"]["voice_command"]["enabled"]:
                self.plugins["voice_command"] = VoiceCommand(self.config)
                logger.info("Voice Command plugin initialized")

            # Initialize CRM Integration
            if any(self.config["plugins"]["crm"][crm]["enabled"] 
                  for crm in ["hubspot", "shopify", "stripe"]):
                self.plugins["crm"] = CRMIntegration(self.config)
                logger.info("CRM Integration plugin initialized")

            # Initialize Social Media Automation
            if any(self.config["plugins"]["social_media"][platform]["enabled"] 
                  for platform in ["linkedin", "twitter", "facebook"]):
                self.plugins["social_media"] = SocialMediaAutomation(self.config)
                logger.info("Social Media Automation plugin initialized")

            # Initialize Messaging Automation
            if any(self.config["plugins"]["messaging"][channel]["enabled"] 
                  for channel in ["email", "sms"]):
                self.plugins["messaging"] = MessagingAutomation(self.config)
                logger.info("Messaging Automation plugin initialized")

            # Initialize Analytics & Reporting
            if self.config["plugins"]["analytics"]["enabled"]:
                self.plugins["analytics"] = AnalyticsReporting(self.config)
                logger.info("Analytics & Reporting plugin initialized")

        except Exception as e:
            logger.error(f"Error initializing plugins: {str(e)}")
            raise

    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """Get a plugin instance by name"""
        return self.plugins.get(plugin_name)

    def get_active_plugins(self) -> Dict[str, Any]:
        """Get all active plugin instances"""
        return self.plugins

    def is_plugin_active(self, plugin_name: str) -> bool:
        """Check if a plugin is active"""
        return plugin_name in self.plugins

    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message through appropriate plugins"""
        response = {
            "processed": False,
            "responses": [],
            "errors": []
        }

        try:
            # Process with AI Chatbot
            if "ai_chatbot" in self.plugins:
                ai_response = await self.plugins["ai_chatbot"].process_message(
                    message["user_id"],
                    message["text"]
                )
                response["responses"].append({
                    "plugin": "ai_chatbot",
                    "response": ai_response
                })
                response["processed"] = True

            # Process automation commands
            if message.get("command"):
                if message["command"] == "voice" and "voice_command" in self.plugins:
                    voice_response = await self.plugins["voice_command"].process_voice_message(
                        message["voice_file"]
                    )
                    response["responses"].append({
                        "plugin": "voice_command",
                        "response": voice_response
                    })
                    response["processed"] = True

                elif message["command"].startswith("crm_") and "crm" in self.plugins:
                    crm_response = await self._handle_crm_command(message)
                    response["responses"].append({
                        "plugin": "crm",
                        "response": crm_response
                    })
                    response["processed"] = True

                elif message["command"].startswith("social_") and "social_media" in self.plugins:
                    social_response = await self._handle_social_command(message)
                    response["responses"].append({
                        "plugin": "social_media",
                        "response": social_response
                    })
                    response["processed"] = True

                elif message["command"].startswith("msg_") and "messaging" in self.plugins:
                    messaging_response = await self._handle_messaging_command(message)
                    response["responses"].append({
                        "plugin": "messaging",
                        "response": messaging_response
                    })
                    response["processed"] = True

                elif message["command"].startswith("analytics_") and "analytics" in self.plugins:
                    analytics_response = await self._handle_analytics_command(message)
                    response["responses"].append({
                        "plugin": "analytics",
                        "response": analytics_response
                    })
                    response["processed"] = True

            return response

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            response["errors"].append(str(e))
            return response

    async def _handle_crm_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle CRM-related commands"""
        try:
            crm_plugin = self.plugins["crm"]
            command = message["command"].replace("crm_", "")

            if command == "sync":
                return await crm_plugin.sync_all()
            elif command == "create_contact":
                return await crm_plugin.create_contact(message["data"])
            elif command == "get_customer":
                return await crm_plugin.get_customer_info(message["data"]["email"])
            else:
                raise ValueError(f"Unknown CRM command: {command}")

        except Exception as e:
            logger.error(f"Error handling CRM command: {str(e)}")
            raise

    async def _handle_social_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle social media-related commands"""
        try:
            social_plugin = self.plugins["social_media"]
            command = message["command"].replace("social_", "")

            if command == "post":
                return await social_plugin.post_to_all(message["data"])
            elif command == "analytics":
                return await social_plugin.get_analytics()
            else:
                raise ValueError(f"Unknown social media command: {command}")

        except Exception as e:
            logger.error(f"Error handling social media command: {str(e)}")
            raise

    async def _handle_messaging_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle messaging-related commands"""
        try:
            messaging_plugin = self.plugins["messaging"]
            command = message["command"].replace("msg_", "")

            if command == "email":
                return await messaging_plugin.send_email(
                    message["data"]["to"],
                    message["data"]["subject"],
                    message["data"]["content"]
                )
            elif command == "sms":
                return await messaging_plugin.send_sms(
                    message["data"]["to"],
                    message["data"]["message"]
                )
            elif command == "bulk_email":
                return await messaging_plugin.send_bulk_email(
                    message["data"]["recipients"],
                    message["data"]["subject"],
                    message["data"]["content"]
                )
            elif command == "bulk_sms":
                return await messaging_plugin.send_bulk_sms(
                    message["data"]["recipients"],
                    message["data"]["message"]
                )
            else:
                raise ValueError(f"Unknown messaging command: {command}")

        except Exception as e:
            logger.error(f"Error handling messaging command: {str(e)}")
            raise

    async def _handle_analytics_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics-related commands"""
        try:
            analytics_plugin = self.plugins["analytics"]
            command = message["command"].replace("analytics_", "")

            if command == "report":
                return await analytics_plugin.generate_report(
                    message["data"]["report_type"],
                    message["data"].get("start_date"),
                    message["data"].get("end_date"),
                    message["data"].get("filters")
                )
            else:
                raise ValueError(f"Unknown analytics command: {command}")

        except Exception as e:
            logger.error(f"Error handling analytics command: {str(e)}")
            raise
