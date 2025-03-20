import os
import logging
from typing import Dict, Any, Optional
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import asyncio
import openai  # ✅ Make sure this is installed and imported!

from modules import PluginManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, config: Dict[str, Any], plugin_manager: PluginManager):
        """Initialize the Telegram bot with configuration and plugin manager"""
        self.config = config
        self.telegram_config = config["telegram_bot"]
        self.plugin_manager = plugin_manager

        # ✅ Initialize OpenAI API key from your config or environment
        openai.api_key = os.getenv("OPENAI_API_KEY") or self.config.get("openai_api_key")

        # Initialize the Application
        self.application = ApplicationBuilder().token(self.telegram_config["token"]).build()

        # Register handlers
        self._register_handlers()

        logger.info("✅ Telegram bot initialized successfully")

    def _register_handlers(self):
        """Register message and command handlers"""

        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))

        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))

        # Error handler
        self.application.add_error_handler(self.error_handler)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command"""
        welcome_message = (
            "👋 Welcome to your AI-powered Business Assistant!\n\n"
            "I can help you with:\n"
            "🤖 AI Chat - Ask me anything\n"
            "🗣️ Voice Commands\n"
            "📊 CRM Management\n"
            "📱 Social Media Automation\n"
            "📧 Email & SMS Automation\n"
            "📈 Analytics & Reporting\n\n"
            "Type /help to see all available commands."
        )
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command"""
        help_message = (
            "🤖 *Available Commands:*\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/status - Check system status\n\n"
            "*Features:*\n"
            "• Send a message to chat with AI\n"
            "• Send a voice message for voice commands\n"
            "• Use #social to create social media posts\n"
            "• Use #email or #sms for outreach\n"
            "• Use #report for analytics\n"
        )
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /status command"""
        active_plugins = self.plugin_manager.get_active_plugins()

        status_message = "*System Status:*\n\n"
        for plugin_name in self.config["enabled_plugins"]:
            status = "✅ Enabled" if plugin_name in active_plugins else "❌ Disabled"
            status_message += f"• {plugin_name.replace('_', ' ').title()}: {status}\n"

        await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages"""
        try:
            message_text = update.message.text
            user_id = update.effective_user.id

            logger.info(f"Received message from user {user_id}: {message_text}")

            # ✅ Prioritize handling hashtag commands
            if message_text.startswith('#'):
                await self._handle_hashtag_command(update, context)
                return

            # ✅ Default to OpenAI chat response
            response = await self.ask_openai(message_text)
            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await update.message.reply_text(
                "Sorry, I encountered an error processing your message. Please try again later."
            )

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming voice messages"""
        try:
            voice_command = self.plugin_manager.get_plugin("voice_command")
            if not voice_command:
                await update.message.reply_text(
                    "❌ Voice commands are currently disabled. Please contact the administrator."
                )
                return

            voice_file = await update.message.voice.get_file()
            result = await voice_command.process_voice_message(voice_file)

            if result["success"]:
                await update.message.reply_text(result["response"])
            else:
                await update.message.reply_text(
                    f"Error processing voice command: {result.get('error', 'Unknown error')}"
                )

        except Exception as e:
            logger.error(f"Error handling voice message: {str(e)}")
            await update.message.reply_text(
                "Sorry, I encountered an error processing your voice message. Please try again later."
            )

    async def ask_openai(self, prompt: str) -> str:
        """Send prompt to OpenAI and return response"""
        try:
            logger.info(f"Sending prompt to OpenAI: {prompt}")

            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-4",  # or "gpt-3.5-turbo"
                messages=[{"role": "user", "content": prompt}]
            )
            reply = response["choices"][0]["message"]["content"]
            logger.info(f"OpenAI response: {reply}")
            return reply

        except Exception as e:
            logger.error(f"OpenAI API Error: {str(e)}")
            return "❌ Error: Unable to get a response from AI."

    async def _handle_hashtag_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle special hashtag commands"""
        message_text = update.message.text.lower()
        command = message_text.split()[0][1:]

        command_map = {
            'social': ('social_media', self._handle_social_command),
            'email': ('messaging', self._handle_email_command),
            'sms': ('messaging', self._handle_sms_command),
            'report': ('analytics', self._handle_report_command),
            'lead': ('lead_nurturing', self._handle_lead_command)
        }

        if command in command_map:
            plugin_name, handler = command_map[command]
            plugin = self.plugin_manager.get_plugin(plugin_name)

            if plugin:
                await handler(update, context, plugin)
            else:
                await update.message.reply_text(
                    f"❌ {plugin_name.replace('_', ' ').title()} is currently disabled."
                )
        else:
            await update.message.reply_text(
                f"Unknown command #{command}. Type /help to see available commands."
            )

    async def _handle_social_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plugin: Any):
        try:
            content = ' '.join(update.message.text.split()[1:])
            post_data = {
                "content": content,
                "platforms": ["linkedin", "twitter", "facebook"]
            }

            result = await plugin.post_to_all(post_data)

            if result["success"]:
                response = "✅ Posted to social media platforms:\n"
                for platform, data in result["platforms"].items():
                    if data.get("success"):
                        response += f"• {platform.title()}: Posted successfully\n"
                    else:
                        response += f"• {platform.title()}: Failed - {data.get('error', 'Unknown error')}\n"
            else:
                response = f"❌ Error posting to social media: {result.get('error', 'Unknown error')}"

            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error handling social command: {str(e)}")
            await update.message.reply_text("Error processing social media command")

    async def _handle_email_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plugin: Any):
        try:
            parts = update.message.text.split()
            if len(parts) < 4:
                await update.message.reply_text(
                    "Invalid email format. Use: #email recipient@example.com Subject Message"
                )
                return

            to_email = parts[1]
            subject = parts[2]
            content = ' '.join(parts[3:])

            result = await plugin.send_email(to_email, subject, content)

            if result["success"]:
                await update.message.reply_text("✅ Email sent successfully!")
            else:
                await update.message.reply_text(f"❌ Error sending email: {result.get('error')}")

        except Exception as e:
            logger.error(f"Error handling email command: {str(e)}")
            await update.message.reply_text("Error processing email command")

    async def _handle_sms_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plugin: Any):
        try:
            parts = update.message.text.split()
            if len(parts) < 3:
                await update.message.reply_text(
                    "Invalid SMS format. Use: #sms phone_number Message"
                )
                return

            phone_number = parts[1]
            message = ' '.join(parts[2:])

            result = await plugin.send_sms(phone_number, message)

            if result["success"]:
                await update.message.reply_text("✅ SMS sent successfully!")
            else:
                await update.message.reply_text(f"❌ Error sending SMS: {result.get('error')}")

        except Exception as e:
            logger.error(f"Error handling SMS command: {str(e)}")
            await update.message.reply_text("Error processing SMS command")

    async def _handle_report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plugin: Any):
        try:
            parts = update.message.text.split()
            report_type = parts[1] if len(parts) > 1 else "overview"

            result = await plugin.generate_report(report_type)

            if result["success"]:
                report_text = "*Analytics Report*\n\n"
                for key, value in result["data"].items():
                    report_text += f"• {key.replace('_', ' ').title()}: {value}\n"

                await update.message.reply_text(report_text, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(f"❌ Error generating report: {result.get('error')}")

        except Exception as e:
            logger.error(f"Error handling report command: {str(e)}")
            await update.message.reply_text("Error processing report command")

    async def _handle_lead_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plugin: Any):
        try:
            parts = update.message.text.split()
            if len(parts) < 3:
                await update.message.reply_text(
                    "Invalid lead command. Use: #lead add email@example.com"
                )
                return

            action = parts[1]
            email = parts[2]

            if action == "add":
                lead_data = {
                    "id": f"lead_{email}",
                    "email": email,
                    "source": "telegram",
                    "status": "new"
                }

                result = await plugin.nurture_lead(lead_data)

                if result["success"]:
                    await update.message.reply_text("✅ Lead nurturing campaign started!")
                else:
                    await update.message.reply_text(f"❌ Error starting campaign: {result.get('error')}")

            else:
                await update.message.reply_text(f"Unknown lead action: {action}")

        except Exception as e:
            logger.error(f"Error handling lead command: {str(e)}")
            await update.message.reply_text("Error processing lead command")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Error handling update {update}: {context.error}")
        if update and hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                "Sorry, an error occurred while processing your request. Please try again later."
            )

    def start_webhook(self, webhook_url: str, listen_address: str = "0.0.0.0", port: int = None):
        port = port or int(os.getenv("PORT", 8443))

        logger.info(f"🚀 Starting webhook on {listen_address}:{port} with URL {webhook_url}")

        self.application.run_webhook(
            listen=listen_address,
            port=port,
            url_path=f"{self.telegram_config['token']}",
            webhook_url=f"{webhook_url}/{self.telegram_config['token']}"
        )

    def start_polling(self):
        logger.info("🚀 Bot started in polling mode")
        self.application.run_polling()

    def stop(self):
        logger.info("Bot stopped")
        self.application.stop()


if __name__ == "__main__":
    from config import load_config

    config = load_config()
    plugin_manager = PluginManager()

    bot = TelegramBot(config, plugin_manager)

    webhook_url = os.getenv("WEBHOOK_URL", "https://your-app-name.up.railway.app")
    bot.start_webhook(webhook_url=webhook_url)
