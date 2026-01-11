"""
Local LLM inference wrapper using llama.cpp.
Handles all LLM operations offline with deterministic outputs.
No data sent to external services.
"""

import logging
import json
import re
from typing import Optional, Dict, Any
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class LLMExtractionResult:
    """Result from LLM-based extraction."""
    extracted_data: Dict[str, Any]
    raw_response: str
    confidence: float  # Based on parsing success
    tokens_used: int
    processing_time_seconds: float
    model_name: str
    error: Optional[str] = None


class LlamaInferenceEngine:
    """
    LLM inference engine using llama.cpp via llama-cpp-python.
    All operations are CPU-based and fully offline.
    """
    
    def __init__(
        self,
        model_path: str,
        context_tokens: int = 2048,
        max_tokens: int = 512,
        temperature: float = 0.1,
        top_p: float = 0.95,
        n_threads: int = 4,
        verbose: bool = False
    ):
        """
        Initialize LLM engine.
        
        Args:
            model_path: Path to GGUF model file
            context_tokens: Context window size
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.1 = deterministic)
            top_p: Nucleus sampling parameter
            n_threads: Number of CPU threads
            verbose: Enable verbose logging
        """
        self.model_path = model_path
        self.context_tokens = context_tokens
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.n_threads = n_threads
        self.verbose = verbose
        self.model = None
        self.model_name = "unknown"
        
        # Load model on initialization
        self._load_model()
    
    def _load_model(self):
        """Load the GGUF model."""
        try:
            from llama_cpp import Llama
            
            logger.info(f"Loading GGUF model from {self.model_path}")
            
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.context_tokens,
                n_threads=self.n_threads,
                verbose=self.verbose,
                use_mlock=True  # Keep model in memory
            )
            
            # Extract model name from metadata if available
            if hasattr(self.model, 'metadata') and self.model.metadata:
                self.model_name = self.model.metadata.get('general.name', 'unknown')
            
            logger.info(f"Successfully loaded GGUF model: {self.model_name}")
            
        except ImportError:
            raise ImportError(
                "llama-cpp-python not installed. "
                "Install with: pip install llama-cpp-python"
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def extract(
        self,
        prompt: str,
        json_schema: Optional[Dict[str, Any]] = None,
        sanitized_text: str = ""
    ) -> LLMExtractionResult:
        """
        Run LLM extraction with strict JSON output.
        
        Args:
            prompt: Prompt template with placeholders
            json_schema: JSON schema for validation
            sanitized_text: The actual text to process (injected into prompt)
            
        Returns:
            LLMExtractionResult with extracted data
        """
        if not self.model:
            return LLMExtractionResult(
                extracted_data={},
                raw_response="",
                confidence=0.0,
                tokens_used=0,
                processing_time_seconds=0,
                model_name=self.model_name,
                error="Model not loaded"
            )
        
        start_time = time.time()
        
        try:
            # Inject sanitized text into prompt
            full_prompt = prompt.replace("{text}", sanitized_text)
            
            logger.debug(f"Running LLM inference with prompt length: {len(full_prompt)}")
            
            # Run inference with strict parameters
            response = self.model(
                full_prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                stop=["}\n"],  # Stop after JSON object
                echo=False
            )
            
            raw_response = response["choices"][0]["text"].strip()
            tokens_used = response.get("usage", {}).get("completion_tokens", 0)
            
            logger.debug(f"LLM response: {raw_response[:200]}...")
            
            # Parse JSON response
            extracted_data, confidence = self._parse_json_response(raw_response, json_schema)
            
            processing_time = time.time() - start_time
            
            logger.info(
                f"LLM extraction complete in {processing_time:.2f}s, "
                f"extracted {len(extracted_data)} fields, confidence: {confidence:.2f}"
            )
            
            return LLMExtractionResult(
                extracted_data=extracted_data,
                raw_response=raw_response,
                confidence=confidence,
                tokens_used=tokens_used,
                processing_time_seconds=processing_time,
                model_name=self.model_name
            )
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            processing_time = time.time() - start_time
            
            return LLMExtractionResult(
                extracted_data={},
                raw_response="",
                confidence=0.0,
                tokens_used=0,
                processing_time_seconds=processing_time,
                model_name=self.model_name,
                error=str(e)
            )
    
    def _parse_json_response(
        self,
        response: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """
        Parse JSON from LLM response.
        Handles cases where response contains JSON within text.
        
        Args:
            response: Raw LLM response
            schema: Expected JSON schema for validation
            
        Returns:
            Tuple of (parsed_dict, confidence_score)
        """
        confidence = 0.0
        extracted_data = {}
        
        try:
            # Try to find JSON object in response
            # Look for { ... } pattern
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                extracted_data = json.loads(json_str)
                confidence = 1.0
                
                # Validate against schema if provided
                if schema:
                    # Check that all required keys exist
                    confidence = self._validate_schema(extracted_data, schema)
                
                logger.debug(f"Successfully parsed JSON from LLM response")
                
            else:
                logger.warning("No JSON found in LLM response")
                confidence = 0.0
        
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            confidence = 0.0
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            confidence = 0.0
        
        return extracted_data, confidence
    
    def _validate_schema(self, data: Dict, schema: Dict) -> float:
        """
        Validate extracted data against schema.
        
        Args:
            data: Extracted data
            schema: Expected schema with "properties" key
            
        Returns:
            Confidence score (0-1)
        """
        if "properties" not in schema:
            return 0.9
        
        required_fields = schema.get("required", [])
        properties = schema["properties"]
        
        # Count matched fields
        matched = 0
        total = len(properties)
        
        for field_name in properties:
            if field_name in data and data[field_name] is not None:
                matched += 1
        
        # Confidence based on field coverage
        confidence = matched / total if total > 0 else 0.0
        
        # Penalize if required fields are missing
        for req_field in required_fields:
            if req_field not in data or data[req_field] is None:
                confidence *= 0.8
        
        return min(confidence, 1.0)
    
    def generate_response(self, prompt: str) -> str:
        """
        Generate free-form response (not for extraction).
        Use for clarification or complex reasoning.
        """
        if not self.model:
            return ""
        
        try:
            response = self.model(
                prompt,
                max_tokens=self.max_tokens,
                temperature=0.3,  # Less deterministic for generation
                top_p=0.95,
                stop=["\n\n"]
            )
            return response["choices"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return ""


class PromptBuilder:
    """
    Build extraction prompts with JSON schema.
    Ensures consistent, deterministic prompting.
    """
    
    @staticmethod
    def build_extraction_prompt(
        schema: Dict[str, Any],
        system_instructions: str = ""
    ) -> str:
        """
        Build a prompt for structured extraction.
        
        Args:
            schema: JSON schema describing expected output
            system_instructions: Additional instructions
            
        Returns:
            Formatted prompt template
        """
        schema_str = json.dumps(schema, indent=2)
        
        prompt = f"""You are an expert document processing system. Your task is to extract structured information from the provided text.

INSTRUCTIONS:
- Extract ONLY information explicitly stated in the text
- Do not infer or hallucinate values
- Return NULL for missing values
- Strictly follow the JSON schema provided
- Output ONLY valid JSON, no other text

{system_instructions}

REQUIRED OUTPUT SCHEMA:
{schema_str}

TEXT TO PROCESS:
{{text}}

RESPONSE (valid JSON only):
"""
        
        return prompt
    
    @staticmethod
    def build_validation_prompt(
        extracted_data: Dict[str, Any],
        text: str
    ) -> str:
        """
        Build a prompt to validate extracted data against source text.
        
        Args:
            extracted_data: Previously extracted data
            text: Source text
            
        Returns:
            Validation prompt
        """
        prompt = f"""Review this extracted data and verify it matches the source text.

EXTRACTED DATA:
{json.dumps(extracted_data, indent=2)}

SOURCE TEXT:
{text}

Respond with a JSON object:
{{
    "is_correct": true/false,
    "issues": ["issue1", "issue2"],
    "confidence": 0.0-1.0
}}
"""
        
        return prompt
