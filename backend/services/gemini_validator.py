
import os
import json
from google import genai
from pypdf import PdfReader


# -----------------------------------------
# Gemini configuration
# -----------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing")

client = genai.Client(api_key=GEMINI_API_KEY)


# -----------------------------------------
# Extract text from PDF
# -----------------------------------------

def extract_pdf_text(file_content: bytes) -> str:
    """
    Extract readable text from a PDF.
    """

    import io

    reader = PdfReader(io.BytesIO(file_content))

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    extracted_text = "\n".join(pages)

    # Prevent extremely large PDFs from consuming
    # excessive Gemini input tokens.
    return extracted_text[:20000]


# -----------------------------------------
# Gemini relevance check
# -----------------------------------------

def check_resource_relevance(
    file_content: bytes,
    title: str,
    subject: str,
    resource_type: str,
    description: str = "",
    tags: str = ""
) -> dict:

    pdf_text = extract_pdf_text(file_content)

    if not pdf_text.strip():
        return {
            "relevant": False,
            "confidence": 0,
            "reason": "Could not extract readable text from the PDF."
        }

    prompt = f"""
You are a strict document validator for a college student resource platform
called Campus Genie.

Your job is to determine whether the uploaded PDF actually matches the
information provided by the student.

STUDENT-PROVIDED INFORMATION

Title:
{title}

Subject:
{subject}

Resource Type:
{resource_type}

What's Inside:
{description}

Tags:
{tags}

PDF CONTENT:
--------------------
{pdf_text}
--------------------

Evaluate whether the PDF content is genuinely relevant to the student's
provided title, subject and description.

Do NOT reject a document just because the wording is different.

Accept reasonable variations, abbreviations, different formatting,
different terminology, or additional relevant material.

Reject the document if:
- The PDF is clearly about a different subject.
- The title/description claims content that is unrelated to the PDF.
- The PDF is clearly mislabeled.
- The PDF contains essentially unrelated material.

Return ONLY valid JSON in exactly this format:

{{
    "relevant": true,
    "confidence": 0.95,
    "reason": "Brief explanation"
}}

Rules:
- relevant must be true or false.
- confidence must be a number between 0 and 1.
- reason must be short and clear.
- Do not include markdown.
- Do not include ```json.
"""

    try:

        response = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt
        )

        response_text = response.output_text.strip()

        # -----------------------------------------
        # Remove accidental markdown formatting
        # -----------------------------------------

        if response_text.startswith("```"):
            response_text = response_text.replace("```json", "")
            response_text = response_text.replace("```", "")
            response_text = response_text.strip()

        result = json.loads(response_text)

        # -----------------------------------------
        # Validate Gemini response
        # -----------------------------------------

        if "relevant" not in result:
            raise ValueError("Gemini response missing 'relevant'")

        if "confidence" not in result:
            raise ValueError("Gemini response missing 'confidence'")

        if "reason" not in result:
            raise ValueError("Gemini response missing 'reason'")

        return {
            "relevant": bool(result["relevant"]),
            "confidence": float(result["confidence"]),
            "reason": str(result["reason"])
        }

    except Exception as e:

        print(
            "GEMINI VALIDATION ERROR:",
            repr(e)
        )

        raise RuntimeError(
            "Unable to validate the resource with Gemini."
        )

