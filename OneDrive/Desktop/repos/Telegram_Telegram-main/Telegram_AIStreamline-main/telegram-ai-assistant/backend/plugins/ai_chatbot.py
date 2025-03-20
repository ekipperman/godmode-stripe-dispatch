import logging
import openai
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AIChatbot:
    def __init__(self, config: Dict[str, Any]):
        """Initialize the AI chatbot with configuration"""
        self.config = config
        self.openai_config = config["ai"]["openai"]
        self.anythingllm_config = config["ai"]["anythingllm"]
        
        # Set OpenAI API key
        openai.api_key = self.openai_config["api_key"]
        
        # Initialize conversation history
        self.conversations: Dict[int, list] = {}  # user_id -> conversation history
        
        logger.info("AI Chatbot initialized successfully")

    async def process_message(self, user_id: int, message: str) -> str:
        """Process a message and return AI response"""
        try:
            # Initialize conversation history for new users
            if user_id not in self.conversations:
                self.conversations[user_id] = []
            
            # Add user message to conversation history
            self.conversations[user_id].append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Prepare conversation for OpenAI
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                *[{"role": msg["role"], "content": msg["content"]} 
                  for msg in self.conversations[user_id][-5:]]  # Keep last 5 messages for context
            ]
            
            # Get response from OpenAI
            response = await self._get_openai_response(messages)
            
            # Add AI response to conversation history
            self.conversations[user_id].append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I apologize, but I encountered an error processing your message. Please try again."

    def _get_system_prompt(self) -> str:
        """Get the system prompt for AI context"""
        return """You are an AI-powered business assistant with the following capabilities:
        - Answering questions about business operations
        - Helping with CRM, social media, and marketing tasks
        - Providing analytics and insights
        - Assisting with email and SMS automation
        
        Please be professional, concise, and helpful in your responses."""

    async def _get_openai_response(self, messages: list) -> str:
        """Get response from OpenAI API"""
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.openai_config["model"],
                messages=messages,
                temperature=self.openai_config["temperature"],
                max_tokens=self.openai_config["max_tokens"]
            )
            return response.choices[0].message.content.strip()
            
        except openai.error.RateLimitError:
            logger.warning("OpenAI rate limit reached, falling back to AnythingLLM")
            return await self._get_anythingllm_response(messages)
            
        except Exception as e:
            logger.error(f"Error getting OpenAI response: {str(e)}")
            raise

    async def _get_anythingllm_response(self, messages: list) -> str:
        """Fallback to AnythingLLM when OpenAI is unavailable"""
        # TODO: Implement AnythingLLM integration
        return "I apologize, but I'm currently operating in fallback mode. Please try again later."

    def clear_conversation(self, user_id: int) -> None:
        """Clear conversation history for a user"""
        if user_id in self.conversations:
            self.conversations.pop(user_id)
            logger.info(f"Cleared conversation history for user {user_id}")

    async def get_conversation_summary(self, user_id: int) -> Optional[str]:
        """Get a summary of the conversation with a user"""
        if user_id not in self.conversations or not self.conversations[user_id]:
            return None
            
        try:
            messages = [
                {"role": "system", "content": "Please provide a brief summary of the following conversation:"},
                *[{"role": msg["role"], "content": msg["content"]} 
                  for msg in self.conversations[user_id]]
            ]
            
            response = await self._get_openai_response(messages)
            return response
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {str(e)}")
            return None

    def get_conversation_history(self, user_id: int) -> list:
        """Get the conversation history for a user"""
        return self.conversations.get(user_id, [])
