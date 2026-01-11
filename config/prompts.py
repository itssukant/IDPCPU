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


INVOICE_EXTRACTION_PROMPT = """You are an expert document processing system specialized in invoice extraction.

CRITICAL INSTRUCTIONS:
- Extract ONLY information explicitly present in the invoice
- Do not infer, estimate, or calculate values
- If a field is not clearly visible, return null
- Return valid JSON only, no markdown or explanations
- Strictly follow the provided schema
- Do not add or remove any fields from the schema

TASK: Extract structured data from the following invoice text:

{text}

REQUIRED OUTPUT FORMAT (valid JSON, no comments):
{{
  "invoice_number": "extracted_value_or_null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "vendor_name": "value_or_null",
  "vendor_address": "value_or_null",
  "vendor_tax_id": "value_or_null",
  "customer_name": "value_or_null",
  "customer_address": "value_or_null",
  "items": [
    {{"description": "item_name", "quantity": 0, "unit_price": 0, "total": 0}}
  ],
  "subtotal": 0.0,
  "tax_rate": 0.0,
  "tax_amount": 0.0,
  "total_amount": 0.0,
  "currency": "USD",
  "payment_terms": "value_or_null",
  "purchase_order_number": "value_or_null"
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
