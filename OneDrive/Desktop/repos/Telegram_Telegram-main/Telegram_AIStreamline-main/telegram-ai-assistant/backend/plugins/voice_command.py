import logging
import json
import tempfile
import os
from typing import Dict, Any, Optional, Tuple
import speech_recognition as sr
from pydub import AudioSegment
from google.cloud import speech_v1
from google.cloud.speech_v1 import types
import io

logger = logging.getLogger(__name__)

class VoiceCommand:
    def __init__(self, config: Dict[str, Any]):
        """Initialize the voice command processor with configuration"""
        self.config = config
        self.voice_config = config["plugins"]["voice_command"]
        self.stt_config = self.voice_config["speech_to_text"]
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        
        # Initialize Google Cloud Speech client if using Google
        if self.stt_config["provider"] == "google":
            self.speech_client = speech_v1.SpeechClient()
        
        logger.info("Voice Command processor initialized successfully")

    async def process_voice_message(self, voice_file_path: str) -> Tuple[bool, str]:
        """
        Process a voice message and return the transcribed text
        Returns: (success: bool, result: str)
        """
        try:
            # Convert voice message to suitable format
            audio_path = await self._convert_audio(voice_file_path)
            
            # Perform speech-to-text
            success, text = await self._speech_to_text(audio_path)
            
            # Clean up temporary files
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            if not success:
                return False, "Failed to process voice command. Please try again."
            
            # Process the command
            return await self._process_command(text)
            
        except Exception as e:
            logger.error(f"Error processing voice message: {str(e)}")
            return False, "An error occurred while processing your voice message."

    async def _convert_audio(self, voice_file_path: str) -> str:
        """Convert voice message to suitable audio format"""
        try:
            # Create temporary directory if it doesn't exist
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate temporary file path
            temp_path = os.path.join(temp_dir, f"audio_{os.path.basename(voice_file_path)}.wav")
            
            # Convert to WAV format
            audio = AudioSegment.from_file(voice_file_path)
            audio = audio.set_channels(1)  # Convert to mono
            audio = audio.set_frame_rate(16000)  # Set sample rate to 16kHz
            audio.export(temp_path, format="wav")
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Error converting audio: {str(e)}")
            raise

    async def _speech_to_text(self, audio_path: str) -> Tuple[bool, str]:
        """Convert speech to text using configured provider"""
        try:
            if self.stt_config["provider"] == "google":
                return await self._google_speech_to_text(audio_path)
            else:
                return await self._local_speech_to_text(audio_path)
                
        except Exception as e:
            logger.error(f"Error in speech to text conversion: {str(e)}")
            return False, str(e)

    async def _google_speech_to_text(self, audio_path: str) -> Tuple[bool, str]:
        """Use Google Cloud Speech-to-Text API"""
        try:
            # Read the audio file
            with io.open(audio_path, "rb") as audio_file:
                content = audio_file.read()
            
            # Configure audio and recognition settings
            audio = types.RecognitionAudio(content=content)
            config = types.RecognitionConfig(
                encoding=types.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
                enable_automatic_punctuation=True
            )
            
            # Perform the transcription
            response = self.speech_client.recognize(config=config, audio=audio)
            
            if not response.results:
                return False, "No speech detected"
            
            transcript = response.results[0].alternatives[0].transcript
            return True, transcript
            
        except Exception as e:
            logger.error(f"Error in Google speech to text: {str(e)}")
            return False, str(e)

    async def _local_speech_to_text(self, audio_path: str) -> Tuple[bool, str]:
        """Use local speech recognition (fallback)"""
        try:
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)  # Using Google's free API
                return True, text
                
        except sr.UnknownValueError:
            return False, "Could not understand audio"
        except sr.RequestError as e:
            return False, f"Error with speech recognition service: {str(e)}"

    async def _process_command(self, text: str) -> Tuple[bool, str]:
        """Process the transcribed command"""
        try:
            # Convert text to lowercase for easier matching
            text = text.lower()
            
            # Define command keywords and their handlers
            commands = {
                "status": self._handle_status_command,
                "report": self._handle_report_command,
                "post": self._handle_social_post_command,
                "email": self._handle_email_command,
                "help": self._handle_help_command
            }
            
            # Check for matching commands
            for keyword, handler in commands.items():
                if keyword in text:
                    return await handler(text)
            
            # If no specific command matched, treat as general query
            return True, f"Processed voice command: {text}"
            
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
            return False, "Error processing voice command"

    async def _handle_status_command(self, text: str) -> Tuple[bool, str]:
        """Handle status check commands"""
        return True, "System is operational. All services are running normally."

    async def _handle_report_command(self, text: str) -> Tuple[bool, str]:
        """Handle report generation commands"""
        return True, "Generating your report. Please wait for the results."

    async def _handle_social_post_command(self, text: str) -> Tuple[bool, str]:
        """Handle social media posting commands"""
        return True, "Preparing to create social media post. Please confirm the content."

    async def _handle_email_command(self, text: str) -> Tuple[bool, str]:
        """Handle email-related commands"""
        return True, "Email command received. Please specify the recipient and content."

    async def _handle_help_command(self, text: str) -> Tuple[bool, str]:
        """Handle help requests"""
        help_message = (
            "Available voice commands:\n"
            "- Check status\n"
            "- Generate report\n"
            "- Create post\n"
            "- Send email\n"
            "- Help"
        )
        return True, help_message
