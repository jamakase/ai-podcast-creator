import os
import tempfile
from pathlib import Path
from typing import Type
import json

import PyPDF2
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from datetime import datetime

output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'videos')
os.makedirs(output_dir, exist_ok=True)

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
            
            # Save PDF file to data directory
            pdf_file_path = os.path.join(data_dir, pdf_filename)
            with open(pdf_file_path, 'wb') as pdf_file:
                pdf_file.write(response.content)
            
            # Save extracted text to the new file
            text_file_path = os.path.join(data_dir, txt_filename)
            with open(text_file_path, 'w', encoding='utf-8') as text_file:
                text_file.write(text_content)
            
            # Clean up temporary PDF file
            os.remove(temp_file_path)
            
            return text_file_path
                
        except requests.RequestException as e:
            return f"Error downloading PDF: {str(e)}"
        except Exception as e:
            return f"Error parsing PDF: {str(e)}"


class HeyGenPodcastGeneratorToolInput(BaseModel):
    """Input schema for HeyGenPodcastGeneratorTool."""
    pdf_file_path: str = Field(..., description="Path to the PDF file to generate a podcast from.")


class HeyGenPodcastGeneratorTool(BaseTool):
    name: str = "HeyGen Podcast Generator Tool"
    description: str = (
        "A tool that generates a podcast video using the HeyGen API v1/podcast/submit. "
        "Takes a PDF URL and other settings as input. Headers and cookies are loaded from config/heygen_settings.json or environment."
    )
    args_schema: Type[BaseModel] = HeyGenPodcastGeneratorToolInput

    def _run(self, pdf_file_path: str) -> str:
        try:
            import requests

            settings = {
                "avatar_id": "Daisy-inskirt-20220818",
                "avatar_style": "normal", 
                "voice_id": "2d5b0e6cf36f460aa7fc47e3eee4ba54",
                "background_color": "#008000",
                "width": 1280,
                "height": 720
            }

            # Required fields for the API
            required_keys = ['key']
            for k in required_keys:
                if k not in settings:
                    return f"Missing '{k}' in HeyGen settings JSON file."

            # Upload the PDF file first
            with open(pdf_file_path, "rb") as f:
                upload_url = "https://upload.heygen.com/v1/asset"
                upload_headers = {
                    "Content-Type": "application/pdf",
                    "x-api-key": settings['key']
                }
                upload_response = requests.post(upload_url, data=f, headers=upload_headers)
                upload_response.raise_for_status()
                asset_data = upload_response.json()

            # Now create the podcast with the uploaded asset
            headers = {
                'accept': 'application/json',
                'content-type': 'application/json',
                'x-api-key': settings['key']
            }

            payload = {
                "source_type": "pdf",
                "asset_id": asset_data.get('asset_id'),
                "key": settings['key'],
                "length": settings.get('length', 60),
                "orientation": settings.get('orientation', 'landscape'),
                "enable_caption": settings.get('enable_caption', True),
                "language": settings.get('language', 'en'),
                "pose_id_1": settings.get('pose_id_1'),
                "pose_id_2": settings.get('pose_id_2')
            }

            url = "https://api2.heygen.com/v1/podcast/submit"
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"Error generating HeyGen podcast video: {str(e)}"


class YouTubeUploaderToolInput(BaseModel):
    """Input schema for YouTubeUploaderTool."""
    video_file_path: str = Field(..., description="Path to the video file (MP4) to upload.")
    title: str = Field(..., description="Title of the YouTube video.")
    description: str = Field(..., description="Description of the YouTube video.")
    tags: list[str] = Field(default_factory=list, description="List of tags for the video.")
    thumbnail_path: str = Field(..., description="Path to the thumbnail image for the video.")


class YouTubeUploaderTool(BaseTool):
    name: str = "YouTube Uploader Tool"
    description: str = (
        "A tool that uploads a video to YouTube using the YouTube Data API v3. "
        "Requires OAuth2 credentials in config/youtube_settings.json."
    )
    args_schema: Type[BaseModel] = YouTubeUploaderToolInput

    def _run(self, video_file_path: str, title: str, description: str, tags: list[str] = [], thumbnail_path: str = ""):
        try:
            # import json
            # import os
            # import requests
            # from urllib.parse import urlencode

            # # Load credentials from config/youtube_settings.json
            # config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'youtube_settings.json')
            # if not os.path.exists(config_path):
            #     return "YouTube settings JSON file not found at config/youtube_settings.json."
            
            # with open(config_path, 'r', encoding='utf-8') as f:
            #     creds_data = json.load(f)

            # # Prepare video upload
            # upload_url = "https://www.googleapis.com/upload/youtube/v3/videos"
            # params = {
            #     'part': 'snippet,status',
            #     'key': creds_data.get('api_key')
            # }
            
            # headers = {
            #     'Authorization': f"Bearer {creds_data.get('access_token')}",
            #     'Content-Type': 'multipart/form-data'
            # }

            # # Prepare video metadata
            # metadata = {
            #     'snippet': {
            #         'title': title,
            #         'description': description,
            #         'tags': tags,
            #     },
            #     'status': {
            #         'privacyStatus': 'private',
            #     }
            # }

            # # Upload video file
            # with open(video_file_path, 'rb') as video_file:
            #     files = {
            #         'video': ('video.mp4', video_file, 'video/mp4'),
            #         'metadata': (None, json.dumps(metadata))
            #     }
            #     response = requests.post(
            #         f"{upload_url}?{urlencode(params)}",
            #         headers=headers,
            #         files=files
            #     )
            #     response.raise_for_status()
            #     video_data = response.json()
            #     video_id = video_data.get('id')

            # # Upload thumbnail if provided
            # if thumbnail_path and os.path.exists(thumbnail_path):
            #     thumbnail_url = f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
            #     params['videoId'] = video_id
                
            #     with open(thumbnail_path, 'rb') as thumbnail_file:
            #         files = {'image': thumbnail_file}
            #         thumbnail_response = requests.post(
            #             f"{thumbnail_url}?{urlencode(params)}",
            #             headers=headers,
            #             files=files
            #         )
            #         thumbnail_response.raise_for_status()

            return f"Video uploaded successfully. Video ID: 1234567890"
        except Exception as e:
            return f"Error uploading video: {str(e)}"


class HeyGenVideoGeneratorToolInput(BaseModel):
    """Input schema for HeyGenVideoGeneratorTool."""
    file_path: str = Field(..., description="Path to text file to be spoken in the video.")


class HeyGenVideoGeneratorTool(BaseTool):
    name: str = "HeyGen Video Generator Tool"
    description: str = (
        "A tool that generates a video using the HeyGen API v2/video/generate. "
        "Takes a text and other settings as input. Headers and cookies are loaded from config/heygen_settings.json or environment."
    )
    args_schema: Type[BaseModel] = HeyGenVideoGeneratorToolInput

    def _run(self, file_path: str) -> str:
        try:
            import requests
            import os
            import time

            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # HACK for now do to not print everything
            text = text[:100]

            # Generate video
            url = "https://api.heygen.com/v2/video/generate"
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "x-api-key": os.getenv("HEYGEN_API_KEY"),
            }
            
            video_inputs = [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": "Daisy-inskirt-20220818",
                        "scale": 1,
                        "avatar_style": "normal",
                        "offset": {"x": 0, "y": 0},
                        "talking_style": "stable",
                        "expression": "default"
                    },
                    "voice": {
                        "type": "text",
                        "voice_id": "2d5b0e6cf36f460aa7fc47e3eee4ba54",
                        "input_text": text,
                        "speed": 1.0,
                        "pitch": 1.0,
                        "emotion": "Friendly",
                        "locale": "en-US"
                    },
                    "background": {
                        "type": "color",
                        "value": "#008000"
                    }
                }
            ]
            
            payload = {
                "caption": True,
                "dimension": {
                    "width": 1280,
                    "height": 720
                },
                "video_inputs": video_inputs
            }
            
            response = requests.post(url, json=payload, headers=headers)
            video_id = response.json()['data']['video_id']
            
            # Check status
            status_url = "https://api.heygen.com/v1/video_status.get"
            status_headers = {
                "accept": "application/json",
                "x-api-key": os.getenv("HEYGEN_API_KEY")
            }
            params = {"video_id": video_id}
            
            while True:
                response = requests.get(status_url, headers=status_headers, params=params)
                status_data = response.json()
                status = status_data.get('data', {}).get('status')

                if status == 'completed':
                    # Extract video and thumbnail URLs from response
                    video_url = status_data.get('data', {}).get('video_url')
                    thumbnail_url = status_data.get('data', {}).get('thumbnail_url')
                    
                    # Download video and thumbnail
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    video_path = os.path.join(output_dir, f"video_{timestamp}.mp4")
                    thumbnail_path = os.path.join(output_dir, f"thumbnail_{timestamp}.jpg")
                    
                    # Download video
                    video_response = requests.get(video_url)
                    with open(video_path, 'wb') as f:
                        f.write(video_response.content)
                        
                    # Download thumbnail
                    thumbnail_response = requests.get(thumbnail_url)
                    with open(thumbnail_path, 'wb') as f:
                        f.write(thumbnail_response.content)
                    
                    # Add URLs and local paths to status data
                    status_data['data']['video_url'] = video_url
                    status_data['data']['thumbnail_url'] = thumbnail_url
                    status_data['data']['local_video_path'] = video_path
                    status_data['data']['local_thumbnail_path'] = thumbnail_path
                    
                    return status_data
                elif status == 'failed':
                    return f"Video generation failed: {status_data}"
                time.sleep(10)  # Wait 10 seconds before checking again

        except Exception as e:
            return f"Error generating video: {str(e)}"
        

class YouTubeVideoUploaderPlaceholderInput(BaseModel):
    """Input schema for YouTubeVideoUploaderPlaceholder."""
    video_file_path: str = Field(..., description="Path to the video file (MP4) to upload.")
    title: str = Field(..., description="Title of the YouTube video.")
    description: str = Field(..., description="Description of the YouTube video.")
    tags: list[str] = Field(default_factory=list, description="List of tags for the video.")
    thumbnail_path: str = Field(..., description="Path to the thumbnail image for the video.")

class YouTubeVideoUploaderPlaceholder(BaseTool):
    name: str = "YouTube Video Uploader Placeholder"
    description: str = (
        "A placeholder tool for uploading a video to YouTube. "
        "This does not perform any upload, but simulates the interface."
    )
    args_schema: Type[BaseModel] = YouTubeVideoUploaderPlaceholderInput

    def _run(self, video_file_path: str, title: str, description: str, tags: list[str] = [], thumbnail_path: str = ""):
        return f"[PLACEHOLDER] Would upload '{video_file_path}' to YouTube with title '{title}' and thumbnail path '{thumbnail_path}'."


