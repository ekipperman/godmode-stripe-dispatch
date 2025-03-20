import logging
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path
from google.cloud import speech
from google.cloud.speech_v1 import RecognitionConfig
import aiohttp
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class VoiceCommand:
    def __init__(self, config: Dict[str, Any]):
        """Initialize voice command processor with configuration"""
        self.config = config
        self.stt_config = config["plugins"]["voice_command"]["speech_to_text"]
        
        # Initialize Google Cloud Speech client
        if self.stt_config["provider"] == "google":
            self.speech_client = speech.SpeechClient.from_service_account_info({
                "type": "service_account",
                "project_id": self.stt_config.get("project_id"),
                "private_key_id": self.stt_config.get("private_key_id"),
                "private_key": self.stt_config.get("private_key"),
                "client_email": self.stt_config.get("client_email"),
                "client_id": self.stt_config.get("client_id"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": self.stt_config.get("client_x509_cert_url")
            })
        
        # Command patterns for natural language processing
        self.command_patterns = {
            "email": {
                "keywords": ["send", "email", "mail", "message"],
                "handler": self._handle_email_command
            },
            "social": {
                "keywords": ["post", "share", "publish"],
                "handler": self._handle_social_command
            },
            "analytics": {
                "keywords": ["analytics", "report", "stats", "statistics"],
                "handler": self._handle_analytics_command
            },
            "crm": {
                "keywords": ["contact", "customer", "lead", "deal"],
                "handler": self._handle_crm_command
            }
        }
        
        logger.info("Voice Command processor initialized successfully")

    async def process_voice_message(self, voice_file: Any) -> Dict[str, Any]:
        """Process a voice message and return the command response"""
        try:
            # Download and convert voice message
            voice_path = await self._download_voice_file(voice_file)
            
            # Convert speech to text
            text = await self._convert_speech_to_text(voice_path)
            
            # Process the command
            response = await self._process_command(text)
            
            # Cleanup temporary files
            self._cleanup_temp_files(voice_path)
            
            return {
                "success": True,
                "text": text,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Error processing voice message: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _download_voice_file(self, voice_file: Any) -> Path:
        """Download voice file to temporary location"""
        try:
            # Create temporary directory if it doesn't exist
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = temp_dir / f"voice_{timestamp}.ogg"
            
            # Download file using aiohttp
            async with aiohttp.ClientSession() as session:
                file_url = await voice_file.get_url()
                async with session.get(file_url) as response:
                    if response.status == 200:
                        with open(temp_path, 'wb') as f:
                            while True:
                                chunk = await response.content.read(8192)
                                if not chunk:
                                    break
                                f.write(chunk)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Error downloading voice file: {str(e)}")
            raise

    async def _convert_speech_to_text(self, voice_path: Path) -> str:
        """Convert speech to text using configured provider"""
        try:
            provider = self.stt_config["provider"]
            
            if provider == "google":
                return await self._google_speech_to_text(voice_path)
            else:
                raise ValueError(f"Unsupported STT provider: {provider}")
                
        except Exception as e:
            logger.error(f"Error in speech-to-text conversion: {str(e)}")
            raise

    async def _google_speech_to_text(self, voice_path: Path) -> str:
        """Convert speech to text using Google Speech-to-Text"""
        try:
            # Read the audio file
            with open(voice_path, "rb") as audio_file:
                content = audio_file.read()
            
            # Configure audio and recognition settings
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=16000,
                language_code="en-US",
                model="default",
                enable_automatic_punctuation=True
            )
            
            # Perform the transcription
            operation = self.speech_client.long_running_recognize(config=config, audio=audio)
            response = operation.result(timeout=90)
            
            # Extract the transcribed text
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript + " "
            
            return transcript.strip()
            
        except Exception as e:
            logger.error(f"Error in Google Speech-to-Text conversion: {str(e)}")
            raise

    async def _process_command(self, text: str) -> str:
        """Process the command from converted text"""
        text = text.lower()
        
        # Find matching command pattern
        for command_type, pattern in self.command_patterns.items():
            if any(keyword in text for keyword in pattern["keywords"]):
                return await pattern["handler"](text)
        
        return "I'm sorry, I couldn't recognize a specific command. Please try again with a clearer instruction."

    async def _handle_email_command(self, text: str) -> str:
        """Handle email-related commands"""
        # Extract email details using simple keyword matching
        # In a production environment, use NLP for better extraction
        words = text.split()
        try:
            to_index = words.index("to")
            subject_index = words.index("subject")
            
            recipient = words[to_index + 1]
            subject = " ".join(words[subject_index + 1:])
            
            return f"I'll help you send an email to {recipient} with subject: {subject}"
            
        except ValueError:
            return "Please specify both recipient and subject. For example: 'send email to john@example.com subject Meeting tomorrow'"

    async def _handle_social_command(self, text: str) -> str:
        """Handle social media-related commands"""
        platforms = ["linkedin", "twitter", "facebook"]
        mentioned_platforms = [p for p in platforms if p in text]
        
        if not mentioned_platforms:
            return "Please specify which social media platform to post to."
            
        return f"I'll help you create a post for {', '.join(mentioned_platforms)}"

    async def _handle_analytics_command(self, text: str) -> str:
        """Handle analytics-related commands"""
        timeframes = ["today", "week", "month", "year"]
        mentioned_timeframe = next((t for t in timeframes if t in text), None)
        
        if not mentioned_timeframe:
            return "Please specify a timeframe (today, week, month, or year) for the analytics report."
            
        return f"I'll generate an analytics report for the {mentioned_timeframe}"

    async def _handle_crm_command(self, text: str) -> str:
        """Handle CRM-related commands"""
        actions = {
            "add": "create a new contact",
            "find": "search for a contact",
            "update": "update contact information",
            "delete": "remove a contact"
        }
        
        action = next((a for a in actions.keys() if a in text), None)
        
        if not action:
            return "Please specify a CRM action (add, find, update, or delete)"
            
        return f"I'll help you {actions[action]} in the CRM system"

    def _cleanup_temp_files(self, voice_path: Path) -> None:
        """Clean up temporary files"""
        try:
            if voice_path.exists():
                voice_path.unlink()
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {str(e)}")

    async def get_supported_commands(self) -> list:
        """Get list of supported voice commands"""
        return [
            "send email to [recipient] with subject [subject]",
            "post to [platform] saying [content]",
            "show analytics for [timeframe]",
            "add contact [name] to CRM",
            "find contact [name] in CRM",
            "update contact [name] in CRM",
            "delete contact [name] from CRM"
        ]

    async def get_command_help(self, command: str) -> Optional[str]:
        """Get help text for a specific command"""
        help_texts = {
            "email": "Say 'send email to [recipient] with subject [subject]'",
            "social": "Say 'post to [platform] saying [content]'",
            "analytics": "Say 'show analytics for [timeframe]'",
            "crm": "Say 'add/find/update/delete contact [name] in CRM'"
        }
        return help_texts.get(command, "Command not found in help documentation")
