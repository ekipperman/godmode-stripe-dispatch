import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PluginManager:
    def __init__(self, config: Dict[str, Any]):
        """Initialize plugin manager with configuration"""
        self.config = config
        self.plugins = {}
        self.plugins_config = self._load_plugins_config()
        self._initialize_plugins()
        
        logger.info("Plugin Manager initialized successfully")

    def _load_plugins_config(self) -> Dict[str, Any]:
        """Load plugins configuration from plugins_config.json"""
        try:
            config_path = Path(__file__).parent.parent / "plugins_config.json"
            with open(config_path, 'r') as f:
                plugins_config = json.load(f)
            
            # Validate the configuration structure
            if not isinstance(plugins_config, dict) or "enabled_plugins" not in plugins_config:
                raise ValueError("Invalid plugins configuration structure")
            
            return plugins_config["enabled_plugins"]
            
        except FileNotFoundError:
            logger.warning("plugins_config.json not found, using default configuration")
            return {
                "ai_chatbot": True,
                "voice_command": True,
                "crm_integration": True,
                "social_media_posting": True,
                "email_sms_automation": True,
                "lead_nurturing": True,
                "analytics_reporting": True
            }
        except json.JSONDecodeError:
            logger.error("Invalid JSON in plugins_config.json")
            raise
        except Exception as e:
            logger.error(f"Error loading plugins configuration: {str(e)}")
            raise

    def _initialize_plugins(self):
        """Initialize all enabled plugins"""
        try:
            # Import plugin modules here to avoid circular imports
            from .ai_chatbot import AIChatbot
            from .voice_command import VoiceCommand
            from .crm_integration import CRMIntegration
            from .social_media_posting import SocialMediaPosting
            from .email_sms_automation import EmailSMSAutomation
            from .lead_nurturing import LeadNurturing
            from .analytics_reporting import AnalyticsReporting

            # Initialize AI Chatbot
            if self.plugins_config.get("ai_chatbot", False):
                self.plugins["ai_chatbot"] = AIChatbot(self.config)
                logger.info("AI Chatbot plugin initialized")

            # Initialize Voice Command
            if self.plugins_config.get("voice_command", False):
                self.plugins["voice_command"] = VoiceCommand(self.config)
                logger.info("Voice Command plugin initialized")

            # Initialize CRM Integration
            if self.plugins_config.get("crm_integration", False):
                self.plugins["crm"] = CRMIntegration(self.config)
                logger.info("CRM Integration plugin initialized")

            # Initialize Social Media Posting
            if self.plugins_config.get("social_media_posting", False):
                self.plugins["social_media"] = SocialMediaPosting(self.config)
                logger.info("Social Media Posting plugin initialized")

            # Initialize Email & SMS Automation
            if self.plugins_config.get("email_sms_automation", False):
                self.plugins["messaging"] = EmailSMSAutomation(self.config)
                logger.info("Email & SMS Automation plugin initialized")

            # Initialize Lead Nurturing
            if self.plugins_config.get("lead_nurturing", False):
                self.plugins["lead_nurturing"] = LeadNurturing(self.config)
                logger.info("Lead Nurturing plugin initialized")

            # Initialize Analytics & Reporting
            if self.plugins_config.get("analytics_reporting", False):
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

    def reload_configuration(self) -> bool:
        """Reload plugins configuration"""
        try:
            self.plugins_config = self._load_plugins_config()
            self._initialize_plugins()
            return True
        except Exception as e:
            logger.error(f"Error reloading configuration: {str(e)}")
            return False

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
                await self._process_command(message, response)

            return response

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            response["errors"].append(str(e))
            return response

    async def _process_command(self, message: Dict[str, Any], response: Dict[str, Any]):
        """Process specific command types"""
        command = message["command"]
        
        command_handlers = {
            "voice": ("voice_command", self._handle_voice_command),
            "crm": ("crm", self._handle_crm_command),
            "social": ("social_media", self._handle_social_command),
            "msg": ("messaging", self._handle_messaging_command),
            "analytics": ("analytics", self._handle_analytics_command),
            "lead": ("lead_nurturing", self._handle_lead_command)
        }

        for prefix, (plugin_key, handler) in command_handlers.items():
            if command.startswith(prefix) and plugin_key in self.plugins:
                try:
                    result = await handler(message)
                    response["responses"].append({
                        "plugin": plugin_key,
                        "response": result
                    })
                    response["processed"] = True
                except Exception as e:
                    logger.error(f"Error handling {prefix} command: {str(e)}")
                    response["errors"].append(str(e))

    async def _handle_voice_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle voice command processing"""
        return await self.plugins["voice_command"].process_voice_message(
            message["voice_file"]
        )

    async def _handle_crm_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle CRM-related commands"""
        crm_plugin = self.plugins["crm"]
        command = message["command"].replace("crm_", "")

        command_map = {
            "sync": crm_plugin.sync_all,
            "create_contact": lambda: crm_plugin.create_contact(message["data"]),
            "get_customer": lambda: crm_plugin.get_customer_info(message["data"]["email"])
        }

        if command in command_map:
            return await command_map[command]()
        raise ValueError(f"Unknown CRM command: {command}")

    async def _handle_social_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle social media-related commands"""
        social_plugin = self.plugins["social_media"]
        command = message["command"].replace("social_", "")

        command_map = {
            "post": lambda: social_plugin.post_to_all(message["data"]),
            "analytics": social_plugin.get_analytics
        }

        if command in command_map:
            return await command_map[command]()
        raise ValueError(f"Unknown social media command: {command}")

    async def _handle_messaging_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle messaging-related commands"""
        messaging_plugin = self.plugins["messaging"]
        command = message["command"].replace("msg_", "")

        command_map = {
            "email": lambda: messaging_plugin.send_email(
                message["data"]["to"],
                message["data"]["subject"],
                message["data"]["content"]
            ),
            "sms": lambda: messaging_plugin.send_sms(
                message["data"]["to"],
                message["data"]["message"]
            ),
            "bulk_email": lambda: messaging_plugin.send_bulk_email(
                message["data"]["recipients"],
                message["data"]["subject"],
                message["data"]["content"]
            ),
            "bulk_sms": lambda: messaging_plugin.send_bulk_sms(
                message["data"]["recipients"],
                message["data"]["message"]
            )
        }

        if command in command_map:
            return await command_map[command]()
        raise ValueError(f"Unknown messaging command: {command}")

    async def _handle_analytics_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics-related commands"""
        analytics_plugin = self.plugins["analytics"]
        command = message["command"].replace("analytics_", "")

        if command == "report":
            return await analytics_plugin.generate_report(
                message["data"]["report_type"],
                message["data"].get("start_date"),
                message["data"].get("end_date"),
                message["data"].get("filters")
            )
        raise ValueError(f"Unknown analytics command: {command}")

    async def _handle_lead_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle lead nurturing commands"""
        lead_plugin = self.plugins["lead_nurturing"]
        command = message["command"].replace("lead_", "")

        if command == "nurture":
            return await lead_plugin.nurture_lead(message["data"])
        raise ValueError(f"Unknown lead nurturing command: {command}")
