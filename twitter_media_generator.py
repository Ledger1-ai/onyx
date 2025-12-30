#!/usr/bin/env python3
"""
Twitter Media Generator
Simplified media generation functions for Twitter posting, extracted from Vader.py core logic
Removes Discord dependencies and focuses on Twitter-optimized media creation
"""

import os
import json
import requests
import logging
from typing import Dict, Optional, Tuple, Any
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import uuid
# MoviePy compatibility imports (v0/v1 editor shim vs v2 modular API)
try:
    # MoviePy v0/v1
    from moviepy import VideoFileClip, ImageClip, CompositeVideoClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("Warning: moviepy not found. Video editing features disabled.")
    # Fallback to MoviePy v2 specific imports if direct 'moviepy' import fails
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip
        from moviepy.video.VideoClip import ImageClip
        from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
        MOVIEPY_AVAILABLE = True # If v2 imports work, it's still available
    except ImportError:
        MOVIEPY_AVAILABLE = False
        print("Warning: moviepy v2 specific imports also failed. Video editing features remain disabled.")
import shutil
import subprocess
# Attempt to use bundled ffmpeg from imageio if system ffmpeg not found
try:
    from imageio_ffmpeg import get_ffmpeg_exe
except ImportError:
    get_ffmpeg_exe = None

# Pillow >=10 removed the ANTIALIAS constant; patch for backward compatibility
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)

# Configuration
try:
    # Load Azure OpenAI configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    AZURE_OPENAI_ENDPOINT = config.get('azure_openai_endpoint')
    AZURE_OPENAI_KEY = config.get('azure_openai_key')
    AZURE_OPENAI_DEPLOYMENT_NAME = config.get('azure_openai_deployment_name', 'dall-e-3')
    AZURE_SORA_DEPLOYMENT_NAME = config.get('azure_sora_deployment_name', 'sora-1.0-turbo')
    
    # Check if required config is available
    CONFIG_AVAILABLE = all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY])
    
except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
    # Try environment variable fallback
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "dall-e-3")
    AZURE_SORA_DEPLOYMENT_NAME = os.getenv("AZURE_SORA_DEPLOYMENT_NAME", "sora-1.0-turbo")
    if AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY:
        logger.info("Loaded Azure OpenAI config from environment variables")
        CONFIG_AVAILABLE = True
    else:
        logger.error(f"Configuration error: {e}")
        CONFIG_AVAILABLE = False

# Twitter image size constants
TWITTER_SIZES = {
    "standard": (1200, 675),  # 16:9 aspect ratio
    "square": (1080, 1080),   # 1:1 aspect ratio
    "portrait": (1080, 1350), # 4:5 aspect ratio
    "header": (1500, 500),    # 3:1 aspect ratio for headers
}

def is_media_available() -> bool:
    """Check if media generation is available"""
    return CONFIG_AVAILABLE

def get_twitter_image_size(size_type: str = "standard") -> Tuple[int, int]:
    """Get Twitter-optimized image dimensions"""
    return TWITTER_SIZES.get(size_type, TWITTER_SIZES["standard"])

def generate_image(prompt: str, size: str = "1024x1024", quality: str = "standard") -> Dict[str, Any]:
    """
    Generate an image using Azure OpenAI DALL-E 3
    
    Args:
        prompt: Description of the image to generate
        size: Image size (1024x1024, 1792x1024, 1024x1792)
        quality: Image quality (standard, hd)
    
    Returns:
        Dict with success status, image_url, and other metadata
    """
    if not CONFIG_AVAILABLE:
        return {"success": False, "error": "Azure OpenAI configuration not available"}
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer C1f51fMYaWUZf2vFX72tsYOxIOHaT22MBw5x1CWVODXwrdA6n4ufJQQJ99BDACMsfrFXJ3w3AAAAACOGYsCS"
        }
        
        data = {
            "prompt": prompt,
            "size": "1024x1024",
            "quality": "high",
            "n": 1
        }
        
        url = "https://skyne-m9xuadtz-westus3.cognitiveservices.azure.com/openai/deployments/gpt-image-1/images/generations?api-version=2025-04-01-preview"
        
        logger.info(f"Generating image with prompt: {prompt[:100]}...")
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("data") and len(result["data"]) > 0:
                first_item = result["data"][0]

                # -----------------------------------------------------------
                # The API now returns the image as base-64 instead of a URL.
                # Convert that base-64 string to a local image file and
                # return the file *path* (still called image_url for backwards
                # compatibility with the rest of the code-base).
                # -----------------------------------------------------------
                if isinstance(first_item, dict):
                    base64_str = first_item.get("b64_json") or first_item.get("data")
                else:
                    base64_str = first_item

                image_url = None
                if isinstance(base64_str, str) and len(base64_str) > 100:
                    # Strip possible “data:image/png;base64,” prefix
                    if base64_str.startswith("data:image"):
                        base64_str = base64_str.split(",", 1)[-1]

                    image_bytes = base64.b64decode(base64_str)
                    file_name = f"generated_image_{uuid.uuid4().hex}.png"
                    with open(file_name, "wb") as f:
                        f.write(image_bytes)

                    image_url = os.path.abspath(file_name)
                    logger.info("Image generated successfully (saved locally)")
                else:
                    # Fallback – assume the service still returned a URL
                    image_url = first_item if isinstance(first_item, str) else first_item.get("url")

                return {
                    "success": True,
                    "image_url": image_url,
                    "prompt": prompt,
                    "size": size,
                    "quality": quality
                }
            else:
                return {"success": False, "error": "No image data in response"}
        else:
            error_msg = f"API request failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        error_msg = f"Image generation failed: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

def generate_video(prompt: str, width: str = "1080", height: str = "1920") -> Dict[str, Any]:
    """
    Generate a video using Azure OpenAI Sora
    
    Args:
        prompt: Description of the video to generate
        width: Video width in pixels
        height: Video height in pixels
    
    Returns:
        Dict with success status, video_url, and other metadata
    """
    if not CONFIG_AVAILABLE:
        return {"success": False, "error": "Azure OpenAI configuration not available"}
    
    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_KEY
        }
        
        data = {
            "prompt": prompt,
            "width": int(width),
            "height": int(height)
        }
        
        url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_SORA_DEPLOYMENT_NAME}/videos/generations?api-version=2024-12-01-preview"
        
        logger.info(f"Generating video with prompt: {prompt[:100]}...")
        
        response = requests.post(url, headers=headers, json=data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("data") and len(result["data"]) > 0:
                video_url = result["data"][0]["url"]
                logger.info("Video generated successfully")
                return {
                    "success": True,
                    "video_url": video_url,
                    "prompt": prompt,
                    "width": width,
                    "height": height
                }
            else:
                return {"success": False, "error": "No video data in response"}
        else:
            error_msg = f"API request failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        error_msg = f"Video generation failed: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

def download_image(image_url: str, save_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Download an image from a URL
    
    Args:
        image_url: URL of the image to download
        save_path: Optional path to save the image
    
    Returns:
        Dict with success status and local file path
    """
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        if save_path:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return {"success": True, "file_path": save_path}
        else:
            # Return image data as bytes
            return {"success": True, "image_data": response.content}
            
    except Exception as e:
        error_msg = f"Image download failed: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

def resize_for_twitter(image_path: str, target_size: str = "standard") -> Dict[str, Any]:
    """
    Resize an image for optimal Twitter posting
    
    Args:
        image_path: Path to the source image
        target_size: Twitter size type (standard, square, portrait, header)
    
    Returns:
        Dict with success status and resized image path
    """
    try:
        target_width, target_height = get_twitter_image_size(target_size)
        
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate dimensions maintaining aspect ratio
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height
            
            if img_ratio > target_ratio:
                # Image is wider, fit to height
                new_height = target_height
                new_width = int(target_height * img_ratio)
            else:
                # Image is taller, fit to width
                new_width = target_width
                new_height = int(target_width / img_ratio)
            
            # Resize and crop to exact dimensions
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Center crop to target dimensions
            left = (new_width - target_width) // 2
            top = (new_height - target_height) // 2
            right = left + target_width
            bottom = top + target_height
            
            img_cropped = img_resized.crop((left, top, right, bottom))
            
            # Save resized image
            output_path = image_path.replace('.', f'_twitter_{target_size}.')
            img_cropped.save(output_path, 'JPEG', quality=95)
            
            logger.info(f"Image resized for Twitter ({target_size}): {output_path}")
            return {
                "success": True,
                "output_path": output_path,
                "dimensions": (target_width, target_height),
                "target_size": target_size
            }
            
    except Exception as e:
        error_msg = f"Image resize failed: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

def add_text_overlay(image_url: str, text: str, position: str = "bottom") -> Dict[str, Any]:
    """
    Add text overlay to an image (simplified version of branding)
    
    Args:
        image_url: URL or path to the source image
        text: Text to overlay
        position: Position of text (top, bottom, center)
    
    Returns:
        Dict with success status and processed image info
    """
    try:
        # Download image if it's a URL
        if image_url.startswith('http'):
            download_result = download_image(image_url)
            if not download_result["success"]:
                return download_result
            image_data = download_result["image_data"]
            img = Image.open(io.BytesIO(image_data))
        else:
            img = Image.open(image_url)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Create drawing context
        draw = ImageDraw.Draw(img)
        
        # Calculate font size based on image dimensions
        font_size = max(img.width // 30, 20)
        
        try:
            # Try to load a nice font, fall back to default if not available
            font = ImageFont.truetype("arial.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position
        if position == "top":
            x = (img.width - text_width) // 2
            y = 20
        elif position == "center":
            x = (img.width - text_width) // 2
            y = (img.height - text_height) // 2
        else:  # bottom
            x = (img.width - text_width) // 2
            y = img.height - text_height - 20
        
        # Add text with outline for better visibility
        outline_width = 2
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx*dx + dy*dy <= outline_width*outline_width:
                    draw.text((x + dx, y + dy), text, font=font, fill="black")
        
        # Draw main text
        draw.text((x, y), text, font=font, fill="white")
        
        # Save processed image
        output_path = "temp_overlay_image.jpg"
        img.save(output_path, 'JPEG', quality=95)
        
        logger.info(f"Text overlay added: {text}")
        return {
            "success": True,
            "output_path": output_path,
            "text": text,
            "position": position
        }
        
    except Exception as e:
        error_msg = f"Text overlay failed: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

def enhance_image(image_path: str, enhancement_type: str = "auto") -> Dict[str, Any]:
    """
    Apply basic image enhancements
    
    Args:
        image_path: Path to the source image
        enhancement_type: Type of enhancement (auto, contrast, brightness, saturation)
    
    Returns:
        Dict with success status and enhanced image path
    """
    try:
        from PIL import ImageEnhance
        
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            enhanced_img = img.copy()
            
            if enhancement_type == "auto" or enhancement_type == "contrast":
                # Enhance contrast
                enhancer = ImageEnhance.Contrast(enhanced_img)
                enhanced_img = enhancer.enhance(1.1)
            
            if enhancement_type == "auto" or enhancement_type == "brightness":
                # Slightly increase brightness
                enhancer = ImageEnhance.Brightness(enhanced_img)
                enhanced_img = enhancer.enhance(1.05)
            
            if enhancement_type == "auto" or enhancement_type == "saturation":
                # Enhance color saturation
                enhancer = ImageEnhance.Color(enhanced_img)
                enhanced_img = enhancer.enhance(1.1)
            
            # Save enhanced image
            output_path = image_path.replace('.', f'_enhanced.')
            enhanced_img.save(output_path, 'JPEG', quality=95)
            
            logger.info(f"Image enhanced ({enhancement_type}): {output_path}")
            return {
                "success": True,
                "output_path": output_path,
                "enhancement_type": enhancement_type
            }
            
    except Exception as e:
        error_msg = f"Image enhancement failed: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

# Main functions for Twitter agent integration
__all__ = [
    'generate_image',
    'generate_video', 
    'resize_for_twitter',
    'add_text_overlay',
    'enhance_image',
    'download_image',
    'get_twitter_image_size',
    'is_media_available'
]

# ---------------------------------------------------------------------------
# Video post-processing helpers (overlay frame + background music)
# ---------------------------------------------------------------------------

def _resolve_ffmpeg() -> str:
    """Return a working ffmpeg executable path."""
    return (
        shutil.which("ffmpeg")
        or os.getenv("FFMPEG_PATH")
        or (get_ffmpeg_exe() if get_ffmpeg_exe else None)
        or "ffmpeg"
    )


def download_video(video_url: str, save_path: str = "downloaded_video.mp4") -> Dict[str, Any]:
    """Download a video file from a URL."""
    try:
        resp = requests.get(video_url, timeout=120)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(resp.content)
        logger.info(f"Video downloaded to {save_path}")
        return {"success": True, "file_path": save_path}
    except Exception as e:
        err = f"Video download failed: {e}"
        logger.error(err)
        return {"success": False, "error": err}


def process_video(
    video_path: str,
    overlay_path: Optional[str] = None,
    music_path: Optional[str] = None,
    output_path: str = "processed_video.mp4",
) -> Dict[str, Any]:
    """Overlay a frame on a video and optionally add a background music track.

    Args:
        video_path: Path to source mp4 video.
        overlay_path: PNG/JPG overlay that should fully cover the frame (same aspect ratio).
        music_path: Path to an mp3 (or other audio) file to mux into the final video.
        output_path: Destination mp4.
    """
    try:
        # Ensure temp names
        temp_no_audio = output_path + ".tmp.mp4"

        # Load video
        video = VideoFileClip(video_path)

        if overlay_path and os.path.exists(overlay_path):
            try:
                overlay = ImageClip(overlay_path).set_duration(video.duration)
                overlay = overlay.resize(video.size).set_opacity(1.0)
                final_clip = CompositeVideoClip([video.set_opacity(1.0), overlay])
                logger.info("Overlay applied to video")
            except Exception as e:
                logger.warning(f"Overlay failed ({e}), using original video")
                final_clip = video
        else:
            final_clip = video

        # Export without audio first (avoid audio subprocess issues)
        logger.info("Exporting intermediate video (no audio)…")
        final_clip.write_videofile(temp_no_audio, verbose=False, logger=None)

        # Close MoviePy clips to release handles
        video.close()
        if final_clip is not video:
            final_clip.close()

        # If music provided, mux it in using ffmpeg
        if music_path and os.path.exists(music_path):
            ffmpeg_exe = _resolve_ffmpeg()
            cmd = [
                ffmpeg_exe,
                "-i", temp_no_audio,
                "-i", music_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                "-y",
                output_path,
            ]
            logger.info("Adding background music with ffmpeg…")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning(
                    f"FFmpeg error, keeping silent video. stderr: {result.stderr.strip()}"
                )
                # Replace output with silent video
                if os.path.exists(output_path):
                    os.remove(output_path)
                os.replace(temp_no_audio, output_path)
            else:
                os.remove(temp_no_audio)
        else:
            logger.info("No music provided – keeping silent video")
            if os.path.exists(output_path):
                os.remove(output_path)
            os.replace(temp_no_audio, output_path)

        logger.info(f"Final video saved to {output_path}")
        return {"success": True, "output_path": output_path}

    except Exception as e:
        err = f"Video processing failed: {e}"
        logger.error(err, exc_info=True)
        return {"success": False, "error": err}


# Export new utilities
__all__ += [
    'download_video',
    'process_video',
]
