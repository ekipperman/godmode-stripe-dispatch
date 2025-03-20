import logging
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
from datetime import datetime
import json
from pathlib import Path
from sentry_config import capture_exception
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from .ai_chatbot import AIChatbot
from .content_automation import ContentAutomation
from .marketing_automation import MarketingAutomation
from .unified_payment_gateway import UnifiedPaymentGateway

logger = logging.getLogger(__name__)

class TelegramMarketingBot:
    def __init__(self, config: Dict[str, Any]):
        """Initialize Telegram marketing bot"""
        self.config = config
        self.bot_token = config["telegram"]["bot_token"]
        self.ai_chatbot = AIChatbot(config)
        self.content = ContentAutomation(config)
        self.marketing = MarketingAutomation(config)
        self.payment = UnifiedPaymentGateway(config)
        
        # Initialize tracking
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        self.group_tracking: Dict[int, Dict[str, Any]] = {}
        self.broadcast_tracking: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Telegram Marketing Bot initialized")

    async def start(self):
        """Start the Telegram bot"""
        try:
            self.application = Application.builder().token(self.bot_token).build()
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", self._handle_start))
            self.application.add_handler(CommandHandler("help", self._handle_help))
            self.application.add_handler(CommandHandler("onboard", self._handle_onboard))
            self.application.add_handler(CommandHandler("support", self._handle_support))
            
            # Add message handlers
            self.application.add_handler(MessageHandler(filters.TEXT, self._handle_message))
            self.application.add_handler(CallbackQueryHandler(self._handle_callback))
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            await self.application.run_polling()

        except Exception as e:
            logger.error(f"Error starting Telegram bot: {str(e)}")
            capture_exception(e)

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user_id = update.effective_user.id
            
            # Initialize user session
            self.user_sessions[user_id] = {
                "state": "welcome",
                "data": {},
                "started_at": datetime.now().isoformat()
            }
            
            # Generate welcome message
            welcome_content = await self.content.generate_website_content({
                "business_name": self.config["business"]["name"],
                "value_proposition": self.config["business"]["value_prop"],
                "section": "welcome"
            })
            
            # Create welcome keyboard
            keyboard = [
                [
                    InlineKeyboardButton("Start Onboarding", callback_data="onboard"),
                    InlineKeyboardButton("Learn More", callback_data="learn_more")
                ],
                [
                    InlineKeyboardButton("Get Support", callback_data="support"),
                    InlineKeyboardButton("View Pricing", callback_data="pricing")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                welcome_content["hero"]["description"],
                reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"Error handling start command: {str(e)}")
            capture_exception(e)
            await update.message.reply_text(
                "Sorry, something went wrong. Please try again later."
            )

    async def _handle_onboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /onboard command"""
        try:
            user_id = update.effective_user.id
            
            # Initialize onboarding session
            self.user_sessions[user_id] = {
                "state": "onboarding_start",
                "data": {
                    "step": 0,
                    "completed_steps": []
                },
                "started_at": datetime.now().isoformat()
            }
            
            # Get onboarding steps
            onboarding_steps = [
                {
                    "id": "welcome",
                    "title": "Welcome",
                    "description": "Let's get you started with our platform"
                },
                {
                    "id": "business_info",
                    "title": "Business Information",
                    "description": "Tell us about your business"
                },
                {
                    "id": "integrations",
                    "title": "Setup Integrations",
                    "description": "Connect your tools and services"
                },
                {
                    "id": "payment",
                    "title": "Payment Setup",
                    "description": "Choose your payment method"
                }
            ]
            
            # Create onboarding keyboard
            keyboard = [
                [InlineKeyboardButton("Start Setup", callback_data="onboard_start")],
                [InlineKeyboardButton("Skip for Now", callback_data="onboard_skip")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"Welcome to the onboarding process! We'll help you set up:\n\n" +
                "\n".join([f"✓ {step['title']}" for step in onboarding_steps]),
                reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"Error handling onboard command: {str(e)}")
            capture_exception(e)
            await update.message.reply_text(
                "Sorry, something went wrong. Please try again later."
            )

    async def _handle_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /support command"""
        try:
            user_id = update.effective_user.id
            
            # Initialize support session
            self.user_sessions[user_id] = {
                "state": "support",
                "data": {
                    "issue_type": None,
                    "description": None
                },
                "started_at": datetime.now().isoformat()
            }
            
            # Create support keyboard
            keyboard = [
                [
                    InlineKeyboardButton("Technical Issue", callback_data="support_tech"),
                    InlineKeyboardButton("Billing Issue", callback_data="support_billing")
                ],
                [
                    InlineKeyboardButton("Feature Request", callback_data="support_feature"),
                    InlineKeyboardButton("Other", callback_data="support_other")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "How can we help you today? Please select an option below:",
                reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"Error handling support command: {str(e)}")
            capture_exception(e)
            await update.message.reply_text(
                "Sorry, something went wrong. Please try again later."
            )

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        try:
            user_id = update.effective_user.id
            message_text = update.message.text
            
            if user_id not in self.user_sessions:
                # Initialize new session
                self.user_sessions[user_id] = {
                    "state": "chat",
                    "data": {},
                    "started_at": datetime.now().isoformat()
                }
            
            session = self.user_sessions[user_id]
            state = session["state"]
            
            if state == "onboarding_business_info":
                # Handle business info collection
                session["data"]["business_info"] = message_text
                await self._proceed_onboarding(update, context, user_id)
            
            elif state == "support_description":
                # Handle support ticket description
                session["data"]["description"] = message_text
                await self._create_support_ticket(update, context, user_id)
            
            else:
                # Handle general chat with AI
                response = await self.ai_chatbot.generate_response(message_text)
                await update.message.reply_text(response["message"])

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            capture_exception(e)
            await update.message.reply_text(
                "Sorry, something went wrong. Please try again later."
            )

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        try:
            query = update.callback_query
            user_id = query.from_user.id
            callback_data = query.data
            
            if callback_data.startswith("onboard_"):
                await self._handle_onboarding_callback(update, context, user_id, callback_data)
            
            elif callback_data.startswith("support_"):
                await self._handle_support_callback(update, context, user_id, callback_data)
            
            elif callback_data == "learn_more":
                await self._send_learn_more_info(update, context, user_id)
            
            elif callback_data == "pricing":
                await self._send_pricing_info(update, context, user_id)
            
            # Answer callback query
            await query.answer()

        except Exception as e:
            logger.error(f"Error handling callback: {str(e)}")
            capture_exception(e)
            await update.callback_query.message.reply_text(
                "Sorry, something went wrong. Please try again later."
            )

    async def _handle_onboarding_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                        user_id: int, callback_data: str):
        """Handle onboarding-related callbacks"""
        try:
            session = self.user_sessions[user_id]
            
            if callback_data == "onboard_start":
                # Start onboarding process
                session["state"] = "onboarding_business_info"
                await update.callback_query.message.reply_text(
                    "Great! Let's start with your business information.\n\n"
                    "Please tell us about your business (name, industry, size, etc.):"
                )
            
            elif callback_data == "onboard_skip":
                # Skip onboarding for now
                session["state"] = "chat"
                keyboard = [
                    [InlineKeyboardButton("Start Onboarding", callback_data="onboard_start")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.message.reply_text(
                    "No problem! You can start the onboarding process anytime using /onboard",
                    reply_markup=reply_markup
                )

        except Exception as e:
            logger.error(f"Error handling onboarding callback: {str(e)}")
            capture_exception(e)
            raise

    async def _handle_support_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     user_id: int, callback_data: str):
        """Handle support-related callbacks"""
        try:
            session = self.user_sessions[user_id]
            
            if callback_data.startswith("support_"):
                # Set issue type and request description
                issue_type = callback_data.replace("support_", "")
                session["state"] = "support_description"
                session["data"]["issue_type"] = issue_type
                
                await update.callback_query.message.reply_text(
                    "Please describe your issue in detail:"
                )

        except Exception as e:
            logger.error(f"Error handling support callback: {str(e)}")
            capture_exception(e)
            raise

    async def _proceed_onboarding(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                user_id: int):
        """Proceed with onboarding steps"""
        try:
            session = self.user_sessions[user_id]
            step = session["data"]["step"]
            
            if step == 0:
                # Business info collected, move to integrations
                keyboard = [
                    [
                        InlineKeyboardButton("CRM Integration", callback_data="integrate_crm"),
                        InlineKeyboardButton("Payment Setup", callback_data="integrate_payment")
                    ],
                    [InlineKeyboardButton("Skip Integrations", callback_data="integrate_skip")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                session["data"]["step"] = 1
                await update.message.reply_text(
                    "Great! Now let's set up your integrations:",
                    reply_markup=reply_markup
                )
            
            elif step == 1:
                # Integrations done, move to payment
                keyboard = [
                    [
                        InlineKeyboardButton("Credit Card", callback_data="payment_card"),
                        InlineKeyboardButton("Crypto", callback_data="payment_crypto")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                session["data"]["step"] = 2
                await update.message.reply_text(
                    "Almost done! Choose your preferred payment method:",
                    reply_markup=reply_markup
                )

        except Exception as e:
            logger.error(f"Error proceeding with onboarding: {str(e)}")
            capture_exception(e)
            raise

    async def _create_support_ticket(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   user_id: int):
        """Create a support ticket"""
        try:
            session = self.user_sessions[user_id]
            issue_type = session["data"]["issue_type"]
            description = session["data"]["description"]
            
            # Create ticket in system
            ticket_id = f"TICKET_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Reset session state
            session["state"] = "chat"
            
            await update.message.reply_text(
                f"Thank you for contacting support! Your ticket ID is: {ticket_id}\n\n"
                "Our team will get back to you shortly."
            )

        except Exception as e:
            logger.error(f"Error creating support ticket: {str(e)}")
            capture_exception(e)
            raise

    async def _send_learn_more_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   user_id: int):
        """Send learn more information"""
        try:
            # Generate learn more content
            content = await self.content.generate_website_content({
                "business_name": self.config["business"]["name"],
                "value_proposition": self.config["business"]["value_prop"],
                "section": "features"
            })
            
            keyboard = [
                [
                    InlineKeyboardButton("Start Free Trial", callback_data="onboard_start"),
                    InlineKeyboardButton("View Pricing", callback_data="pricing")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.message.reply_text(
                content["features"]["description"],
                reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"Error sending learn more info: {str(e)}")
            capture_exception(e)
            raise

    async def _send_pricing_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                user_id: int):
        """Send pricing information"""
        try:
            # Get pricing information
            pricing = {
                "basic": {
                    "name": "Basic",
                    "price": "$29/month",
                    "features": [
                        "AI Chatbot",
                        "Basic CRM Integration",
                        "Email Support"
                    ]
                },
                "pro": {
                    "name": "Professional",
                    "price": "$99/month",
                    "features": [
                        "Everything in Basic",
                        "Advanced AI Features",
                        "Priority Support"
                    ]
                },
                "enterprise": {
                    "name": "Enterprise",
                    "price": "Custom",
                    "features": [
                        "Everything in Pro",
                        "Custom Integrations",
                        "Dedicated Support"
                    ]
                }
            }
            
            # Format pricing message
            message = "📊 Our Pricing Plans:\n\n"
            for plan, details in pricing.items():
                message += f"🔹 {details['name']} - {details['price']}\n"
                for feature in details['features']:
                    message += f"  ✓ {feature}\n"
                message += "\n"
            
            keyboard = [
                [InlineKeyboardButton("Start Free Trial", callback_data="onboard_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.message.reply_text(
                message,
                reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"Error sending pricing info: {str(e)}")
            capture_exception(e)
            raise
