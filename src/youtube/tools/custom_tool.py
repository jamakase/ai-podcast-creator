import os
import tempfile
from pathlib import Path
from typing import Type
import json

import PyPDF2
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class PDFParserToolInput(BaseModel):
    """Input schema for PDFParserTool."""
    pdf_url: str = Field(..., description="URL to the PDF file to parse.")


class PDFParserTool(BaseTool):
    name: str = "PDF Parser Tool"
    description: str = (
        "A tool that extracts text content from PDF files accessed via URL. "
        "Useful for processing PDF documents and converting them to plain text format."
    )
    args_schema: Type[BaseModel] = PDFParserToolInput

    def _run(self, pdf_url: str) -> str:
        try:
            # Download PDF from URL
            response = requests.get(pdf_url)
            response.raise_for_status()  # Raise exception for bad status codes
            
            # Create a temporary file to store the PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            # Extract text from PDF
            text_content = ""
            with open(temp_file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text_content += page.extract_text()
            
            # Ensure data directory exists at project root
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # Generate a unique filename for the text file
            pdf_filename = os.path.basename(pdf_url).split('?')[0] or 'extracted'
            if not pdf_filename.lower().endswith('.pdf'):
                pdf_filename += '.pdf'
            txt_filename = pdf_filename[:-4] + '.txt'
            text_file_path = os.path.join(data_dir, txt_filename)
            
            # Save extracted text to the new file
            with open(text_file_path, 'w', encoding='utf-8') as text_file:
                text_file.write(text_content)
            
            # Clean up PDF file
            os.remove(temp_file_path)
            
            return text_file_path
                
        except requests.RequestException as e:
            return f"Error downloading PDF: {str(e)}"
        except Exception as e:
            return f"Error parsing PDF: {str(e)}"


class AudioGeneratorToolInput(BaseModel):
    """Input schema for AudioGeneratorTool."""
    text_file_path: str = Field(description="Path to the text file to convert to audio")
    voice_id: str = Field(default="en-US-Neural2-F", description="Voice ID for the audio generation")


class AudioGeneratorTool(BaseTool):
    name: str = "Audio Generator Tool"
    description: str = (
        "A tool that converts text content into audio using text-to-speech services. "
        "Takes a text file path and returns the path to the generated audio file."
    )
    args_schema: Type[BaseModel] = AudioGeneratorToolInput

    def _run(self, text_file_path: str, voice_id: str = "en-US-Neural2-F") -> str:
        try:
            # Read text content from file
            with open(text_file_path, 'r', encoding='utf-8') as file:
                text_content = file.read()

            # Initialize text-to-speech client
            client = texttospeech.TextToSpeechClient()

            # Set up the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=voice_id
            )

            # Set up the audio configuration
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            # Generate the audio content
            synthesis_input = texttospeech.SynthesisInput(text=text_content)
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            # Ensure data directory exists
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
            os.makedirs(data_dir, exist_ok=True)

            # Generate output filename
            base_name = os.path.basename(text_file_path)
            audio_filename = f"{os.path.splitext(base_name)[0]}.mp3"
            audio_file_path = os.path.join(data_dir, audio_filename)

            # Save the audio content to file
            with open(audio_file_path, "wb") as out:
                out.write(response.audio_content)

            return audio_file_path

        except Exception as e:
            return f"Error generating audio: {str(e)}"


class HeyGenPodcastGeneratorToolInput(BaseModel):
    """Input schema for HeyGenPodcastGeneratorTool."""
    input_text: str = Field(..., description="Text to be spoken in the video.")


class HeyGenPodcastGeneratorTool(BaseTool):
    name: str = "HeyGen Podcast Generator Tool"
    description: str = (
        "A tool that generates a podcast video using the HeyGen API. "
        "Takes only input_text; all other settings are loaded from a JSON config file."
    )
    args_schema: Type[BaseModel] = HeyGenPodcastGeneratorToolInput

    def _run(self, input_text: str) -> str:
        try:
            # Try to load settings from config/heygen_settings.json or heygen_settings.json at project root
            config_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'heygen_settings.json'),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'heygen_settings.json')
            ]
            settings = None
            for path in config_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                    break
            if not settings:
                return "HeyGen settings JSON file not found."
            required_keys = ["avatar_id", "avatar_style", "voice_id", "background_color", "width", "height", "api_key"]
            for key in required_keys:
                if key not in settings:
                    return f"Missing '{key}' in HeyGen settings JSON file."
            url = "https://api.heygen.com/v2/video/generate"
            headers = {
                "X-Api-Key": settings["api_key"],
                "Content-Type": "application/json"
            }
            payload = {
                "video_inputs": [
                    {
                        "character": {
                            "type": "avatar",
                            "avatar_id": settings["avatar_id"],
                            "avatar_style": settings["avatar_style"]
                        },
                        "voice": {
                            "type": "text",
                            "input_text": input_text,
                            "voice_id": settings["voice_id"]
                        },
                        "background": {
                            "type": "color",
                            "value": settings["background_color"]
                        }
                    }
                ],
                "dimension": {
                    "width": settings["width"],
                    "height": settings["height"]
                }
            }
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"Error generating HeyGen podcast video: {str(e)}"
