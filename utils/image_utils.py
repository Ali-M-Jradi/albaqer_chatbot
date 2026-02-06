"""
Image processing utilities for gemstone identification
Handles validation, conversion, and optimization of images
"""

import base64
import io
from PIL import Image
from typing import Tuple, Optional


class ImageProcessor:
    """Handle image validation and processing for gemstone identification"""

    # Supported image formats
    SUPPORTED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}

    # Max image size: 10MB (reasonable for mobile uploads)
    MAX_SIZE_BYTES = 10 * 1024 * 1024

    # Recommended dimensions
    MIN_DIMENSION = 224  # Minimum width/height (Gemini requirement)
    MAX_DIMENSION = 4096  # Maximum width/height

    @staticmethod
    def decode_base64_image(base64_string: str) -> Image.Image:
        """
        Decode base64 string to PIL Image

        Flutter sends images as base64, this converts them to PIL Image objects

        Args:
            base64_string: Base64 encoded image string

        Returns:
            PIL Image object

        Raises:
            ValueError: If decoding fails or invalid format
        """
        try:
            # Remove data URL prefix if present (e.g., "data:image/jpeg;base64,")
            if "," in base64_string:
                base64_string = base64_string.split(",")[1]

            # Decode base64 to bytes
            image_bytes = base64.b64decode(base64_string)

            # Check size (prevent huge uploads)
            if len(image_bytes) > ImageProcessor.MAX_SIZE_BYTES:
                raise ValueError(
                    f"Image too large. Max size: {ImageProcessor.MAX_SIZE_BYTES / 1024 / 1024}MB"
                )

            # Open as PIL Image
            image = Image.open(io.BytesIO(image_bytes))

            # Validate format
            if image.format not in ImageProcessor.SUPPORTED_FORMATS:
                raise ValueError(
                    f"Unsupported format: {image.format}. "
                    f"Supported: {', '.join(ImageProcessor.SUPPORTED_FORMATS)}"
                )

            return image

        except Exception as e:
            raise ValueError(f"Failed to decode image: {str(e)}")

    @staticmethod
    def validate_image(image: Image.Image) -> Tuple[bool, Optional[str]]:
        """
        Validate image dimensions and properties

        Args:
            image: PIL Image object

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, "error message") if invalid
        """
        width, height = image.size

        # Check minimum dimensions
        if (
            width < ImageProcessor.MIN_DIMENSION
            or height < ImageProcessor.MIN_DIMENSION
        ):
            return False, (
                f"Image too small. Minimum: {ImageProcessor.MIN_DIMENSION}x"
                f"{ImageProcessor.MIN_DIMENSION}px. Your image: {width}x{height}px"
            )

        # Check maximum dimensions
        if (
            width > ImageProcessor.MAX_DIMENSION
            or height > ImageProcessor.MAX_DIMENSION
        ):
            return False, (
                f"Image too large. Maximum: {ImageProcessor.MAX_DIMENSION}x"
                f"{ImageProcessor.MAX_DIMENSION}px. Your image: {width}x{height}px"
            )

        # Check aspect ratio (not too extreme - prevent panoramas)
        aspect_ratio = max(width, height) / min(width, height)
        if aspect_ratio > 4:
            return False, (
                "Image aspect ratio too extreme (too wide or too tall). "
                "Please crop to a more square shape."
            )

        return True, None

    @staticmethod
    def resize_if_needed(image: Image.Image, max_size: int = 2048) -> Image.Image:
        """
        Resize image if larger than max_size while maintaining aspect ratio

        Gemini works better with optimized images (faster, lower cost)

        Args:
            image: PIL Image object
            max_size: Maximum dimension (width or height)

        Returns:
            Resized PIL Image (or original if already small enough)
        """
        width, height = image.size

        # Already small enough
        if width <= max_size and height <= max_size:
            return image

        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))

        # Use high-quality resampling
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    @staticmethod
    def prepare_for_gemini(image: Image.Image) -> Image.Image:
        """
        Prepare image for Gemini Vision API

        - Converts to RGB (removes transparency)
        - Resizes to optimal dimensions
        - Ensures correct format

        Args:
            image: PIL Image object

        Returns:
            Optimized PIL Image ready for Gemini
        """
        # Convert to RGB if needed (remove alpha channel/transparency)
        if image.mode in ("RGBA", "LA", "P"):
            # Create white background
            background = Image.new("RGB", image.size, (255, 255, 255))

            # Convert palette mode to RGBA first
            if image.mode == "P":
                image = image.convert("RGBA")

            # Paste image on white background (handles transparency)
            if image.mode in ("RGBA", "LA"):
                background.paste(image, mask=image.split()[-1])
            else:
                background.paste(image)

            image = background

        # Resize to optimal size (Gemini works well with 2048px max)
        # Faster processing + lower API cost
        image = ImageProcessor.resize_if_needed(image, max_size=2048)

        return image
