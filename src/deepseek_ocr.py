"""DeepSeek-OCR Agent Module

This module provides integration for DeepSeek-OCR as a competitive agent
in the EvoAgent framework. DeepSeek-OCR specializes in optical character
recognition and document understanding tasks.

Updated: Expose evolvable weight-like configuration knobs so the evolution
engine can update, merge, and mutate them to produce offspring (AZR pattern).
"""

import os
import time
from typing import Dict, Any, Optional
import base64
import requests


class DeepSeekOCRAgent:
    """DeepSeek-OCR Agent for OCR and document understanding tasks.
    
    Exposes an ocr(...) method that accepts raw image bytes. For evolutionary
    updates, higher-level wrappers (e.g., EvolvableDeepSeekOCR) can pass
    configuration controlling preprocessing and postprocessing.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek-ocr"):
        """
        Initialize DeepSeek-OCR agent.
        
        Args:
            api_key: DeepSeek API key (defaults to DEEPSEEK_API_KEY env var)
            model: Model identifier for DeepSeek-OCR
        """
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.model = model
        self.base_url = "https://api.deepseek.com/v1"
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
        }
    
    def ocr(self, image_bytes: bytes,
            resize_scale: float = 1.0,
            binarize_threshold: float = 0.5,
            language_hint: str = "en",
            enable_layout: bool = True,
            postprocess: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process an image with OCR capabilities using configurable knobs that are
        considered evolvable weights by the evolution engine.
        
        Args:
            image_bytes: Raw bytes of the image
            resize_scale: Optional pre-resize factor
            binarize_threshold: Optional binarization threshold
            language_hint: Language hint for OCR
            enable_layout: Whether to enable layout/structure extraction
            postprocess: Dict of post-processing flags/params
        
        Returns:
            Dict containing OCR results and metadata
        """
        self.stats["total_calls"] += 1
        
        try:
            # Placeholder preprocessing that would use resize_scale/binarize_threshold
            # to guide a local preprocessing pipeline before API call.
            payload = {
                "model": self.model,
                "image": base64.b64encode(image_bytes).decode("utf-8"),
                "options": {
                    "language_hint": language_hint,
                    "enable_layout": enable_layout,
                    "preprocess": {
                        "resize_scale": resize_scale,
                        "binarize_threshold": binarize_threshold,
                    },
                    "postprocess": postprocess or {},
                },
            }
            
            response = self._call_api(payload)
            
            # Extract OCR results from API response
            result = {
                "status": "success",
                "model": self.model,
                "text": response.get("text", ""),
                "confidence": response.get("confidence", 0.0),
                "metadata": {
                    "timestamp": time.time(),
                    "options": payload["options"],
                    "usage": response.get("usage", {}),
                },
            }
            
            # Track token usage if available
            if "usage" in response and "total_tokens" in response["usage"]:
                self.stats["total_tokens"] += response["usage"]["total_tokens"]
            
            self.stats["successful_calls"] += 1
            return result
            
        except Exception as e:
            self.stats["failed_calls"] += 1
            return {
                "status": "error",
                "error": str(e),
                "model": self.model,
            }
    
    def _call_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API call to DeepSeek-OCR service.
        
        Args:
            payload: Request payload containing image and options
        
        Returns:
            API response containing OCR results
        
        Raises:
            ValueError: If API key is not provided
            requests.HTTPError: If API request fails
            requests.Timeout: If request times out
            Exception: For other API-related errors
        """
        if not self.api_key:
            raise ValueError("DeepSeek API key not provided")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            # Make POST request to DeepSeek-OCR endpoint
            response = requests.post(
                f"{self.base_url}/ocr",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            # Raise exception for HTTP errors (4xx, 5xx)
            response.raise_for_status()
            
            # Parse and return JSON response
            result = response.json()
            
            return result
            
        except requests.Timeout:
            raise Exception("API request timed out after 60 seconds")
        except requests.HTTPError as e:
            # Extract error message from response if available
            error_msg = f"API request failed with status {response.status_code}"
            try:
                error_detail = response.json().get("error", {}).get("message", "")
                if error_detail:
                    error_msg += f": {error_detail}"
            except:
                pass
            raise Exception(error_msg) from e
        except requests.RequestException as e:
            raise Exception(f"API request failed: {str(e)}") from e
        except ValueError as e:
            raise Exception(f"Failed to parse API response: {str(e)}") from e
    
    def get_stats(self) -> Dict[str, Any]:
        """Return agent statistics."""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset agent statistics."""
        for key in self.stats:
            self.stats[key] = 0


def create_ocr_agent(api_key: Optional[str] = None) -> DeepSeekOCRAgent:
    """Factory function to create a DeepSeek-OCR agent."""
    return DeepSeekOCRAgent(api_key=api_key)


if __name__ == "__main__":
    # Example usage
    agent = create_ocr_agent()
    
    # Test with a sample image (fake bytes here as placeholder)
    result = agent.ocr(image_bytes=b"\x89PNG...", language_hint="en")
    print(f"OCR Result: {result}")
    print(f"Agent Stats: {agent.get_stats()}")
a
