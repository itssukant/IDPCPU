"""
Image preprocessing module for OCR optimization.
Includes deskewing, denoising, and binarization.
CPU-only operations using OpenCV.
"""

import logging
from typing import Tuple, Optional
import cv2
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """
    Preprocesses images to improve OCR accuracy.
    All operations are deterministic and CPU-based.
    """
    
    def __init__(
        self,
        deskew: bool = True,
        denoise: bool = True,
        binarization: bool = True,
        target_dpi: int = 300
    ):
        """
        Initialize preprocessor.
        
        Args:
            deskew: Enable skew correction
            denoise: Enable noise reduction
            binarization: Enable binary conversion
            target_dpi: Target DPI for resizing (default 300)
        """
        self.deskew = deskew
        self.denoise = denoise
        self.binarization = binarization
        self.target_dpi = target_dpi
        
    def process(self, image_path: str) -> np.ndarray:
        """
        Apply all preprocessing steps to an image.
        
        Args:
            image_path: Path to input image
            
        Returns:
            Preprocessed image as numpy array
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to read image: {image_path}")
        
        logger.info(f"Loaded image from {image_path}, shape: {image.shape}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Deskew if enabled
        if self.deskew:
            gray = self._deskew(gray)
            logger.debug("Applied deskew")
        
        # Denoise if enabled
        if self.denoise:
            gray = self._denoise(gray)
            logger.debug("Applied denoising")
        
        # Binarization if enabled
        if self.binarization:
            gray = self._binarize(gray)
            logger.debug("Applied binarization")
        
        return gray
    
    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Detect and correct image skew.
        Uses contour-based angle detection.
        """
        try:
            # Find contours
            coords = np.column_stack(np.where(image > 0))
            if len(coords) < 4:
                return image
            
            # Fit rotated bounding box
            angle = cv2.minAreaRect(coords)[2]
            
            # Adjust angle for correction
            if angle < -45:
                angle = 90 + angle

            # If the detected angle is effectively 0 or a full 90-degree turn,
            # skip rotation to avoid destroying content (e.g., turning the page
            # into a blank white canvas as seen with some lightly filled docs).
            if abs(angle) < 1 or abs(abs(angle) - 90) < 1:
                return image
            
            # Get image dimensions
            h, w = image.shape
            
            # Compute rotation matrix and apply
            rotation_matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
            rotated = cv2.warpAffine(
                image,
                rotation_matrix,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            
            logger.debug(f"Corrected skew angle: {angle:.2f} degrees")
            return rotated
        except Exception as e:
            logger.warning(f"Deskew failed: {e}, returning original image")
            return image
    
    def _denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Remove noise from image using bilateral filtering.
        Preserves edges while reducing noise.
        """
        try:
            # Apply bilateral filter (preserves edges, reduces noise)
            denoised = cv2.bilateralFilter(image, 9, 75, 75)
            
            # Apply morphological opening (removes small noise)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            denoised = cv2.morphologyEx(denoised, cv2.MORPH_OPEN, kernel, iterations=1)
            
            return denoised
        except Exception as e:
            logger.warning(f"Denoising failed: {e}, returning original image")
            return image
    
    def _binarize(self, image: np.ndarray) -> np.ndarray:
        """
        Convert grayscale image to binary using adaptive thresholding.
        Better for varied lighting conditions than global threshold.
        """
        try:
            # Apply adaptive threshold for better results with varying lighting
            binary = cv2.adaptiveThreshold(
                image,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                blockSize=11,
                C=2
            )
            
            # Optional: Apply morphological operations for cleaner result
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
            
            return binary
        except Exception as e:
            logger.warning(f"Binarization failed: {e}, returning original image")
            return image
    
    def process_batch(self, image_paths: list) -> dict:
        """
        Process multiple images.
        
        Args:
            image_paths: List of image paths
            
        Returns:
            Dictionary mapping path to preprocessed image
        """
        results = {}
        for path in image_paths:
            try:
                results[path] = self.process(path)
            except Exception as e:
                logger.error(f"Failed to process {path}: {e}")
        
        return results
