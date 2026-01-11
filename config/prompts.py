"""
Prompt templates for LLM extraction.
Production-grade prompts optimized for accuracy and determinism.
"""

import json
from typing import Dict, Any

# Prompts are designed to:
# 1. Be deterministic (low temperature, top-p)
# 2. Prevent hallucination (explicit "do not infer" instructions)
# 3. Follow schema strictly
# 4. Handle missing values (return null)


INVOICE_EXTRACTION_PROMPT = """You are an expert invoice extractor.

CRITICAL INSTRUCTIONS:
- Output VALID JSON only — no prose, no markdown.
- Follow the schema exactly; do not add or drop fields.
- Use null when a value is missing or unclear.
- Do not invent values or totals. If numbers are unreadable, return null.
- Keep strings trimmed; avoid duplication.
- If you cannot comply, return an empty JSON object {}.

INPUT TEXT:
{text}

OUTPUT SCHEMA (return JSON matching this shape):
{{
  "invoice_number": "string|null",
  "invoice_date": "YYYY-MM-DD|null",
  "due_date": "YYYY-MM-DD|null",
  "vendor_name": "string|null",
  "customer_name": "string|null",
  "payment_terms": "string|null",
  "currency": "string|null",
  "items": [
    {{"description": "string|null", "quantity": "number|null", "unit_price": "number|null", "total": "number|null"}}
  ],
  "subtotal": "number|null",
  "tax_amount": "number|null",
  "total_amount": "number|null"
}}
"""


RECEIPT_EXTRACTION_PROMPT = """You are an expert document processing system specialized in receipt extraction.

CRITICAL INSTRUCTIONS:
- Extract ONLY information explicitly stated in the receipt
- Do not infer or calculate values
- Return null for missing fields
- Output valid JSON only
- Follow the schema exactly

TASK: Extract structured data from the receipt:

{text}

REQUIRED OUTPUT FORMAT (valid JSON):
{{
  "receipt_number": "extracted_number_or_null",
  "date_time": "extracted_datetime_or_null",
  "merchant_name": "store_name_or_null",
  "merchant_address": "address_or_null",
  "merchant_phone": "phone_or_null",
  "items": [
    {{"item_name": "name", "quantity": 1, "price": 0.00}}
  ],
  "subtotal": 0.00,
  "tax": 0.00,
  "total": 0.00,
  "payment_method": "method_or_null"
}}
"""


FORM_EXTRACTION_PROMPT = """You are an expert form processing system.

CRITICAL INSTRUCTIONS:
- Extract only fields that are explicitly filled out
- Read form labels and their corresponding values
- Return null for empty or unclear fields
- Output valid JSON matching the schema
- Do not infer missing information

TASK: Extract form data:

{text}

REQUIRED OUTPUT FORMAT (valid JSON):
{{
  "form_id": "form_identifier_or_null",
  "submission_date": "date_or_null",
  "form_fields": {{
    "field_name": "field_value_or_null"
  }}
}}
"""


GENERIC_EXTRACTION_PROMPT = """You are a document analysis system.

INSTRUCTIONS:
- Identify key information in the document
- Return structured data as JSON
- Do not infer or hallucinate values
- Use null for missing fields
- Follow the provided schema

DOCUMENT TEXT:

{text}

EXTRACT AND RETURN JSON:
"""


VALIDATION_PROMPT = """Review this document extraction and verify accuracy.

EXTRACTED DATA:
{extracted_data}

ORIGINAL TEXT (excerpt):
{text}

Provide JSON validation result:
{{
  "is_valid": true_or_false,
  "issues": ["issue1", "issue2"],
  "confidence": 0.0_to_1.0
}}
"""


CONSISTENCY_CHECK_PROMPT = """Check for consistency in extracted values.

EXTRACTED DATA:
{extracted_data}

Check for:
1. Date format consistency
2. Numeric values are reasonable
3. Related fields are logically consistent
4. No obvious typos or OCR errors

Return JSON:
{{
  "is_consistent": true_or_false,
  "issues": ["issue1"],
  "suggestions": ["suggestion1"]
}}
"""


class PromptTemplates:
    """Manages prompt templates for different document types."""
    
    _templates = {
        "invoice": INVOICE_EXTRACTION_PROMPT,
        "receipt": RECEIPT_EXTRACTION_PROMPT,
        "form": FORM_EXTRACTION_PROMPT,
        "general": GENERIC_EXTRACTION_PROMPT,
        "validation": VALIDATION_PROMPT,
        "consistency": CONSISTENCY_CHECK_PROMPT
    }
    
    @classmethod
    def get(cls, document_type: str) -> str:
        """Get prompt template for document type."""
        return cls._templates.get(
            document_type.lower(),
            cls._templates["general"]
        )
    
    @classmethod
    def get_validation_prompt(cls) -> str:
        """Get validation prompt."""
        return cls._templates["validation"]
    
    @classmethod
    def get_consistency_prompt(cls) -> str:
        """Get consistency check prompt."""
        return cls._templates["consistency"]
    
    @classmethod
    def render(
        cls,
        template_type: str,
        **kwargs
    ) -> str:
        """
        Render a prompt template with provided variables.
        
        Args:
            template_type: Type of template (invoice, receipt, etc.)
            **kwargs: Variables to substitute in template
            
        Returns:
            Rendered prompt
        """
        template = cls.get(template_type)
        return template.format(**kwargs)
