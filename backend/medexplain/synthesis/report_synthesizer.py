"""
Synthesize a formal medical report from patient-provided consultation data.
The output is designed to be consumed by the existing MedExplain extractor.
"""
from __future__ import annotations

from mistralai.client import Mistral
from config import settings

_SYSTEM_PROMPT = """\
You are a medical report writer assisting a patient-facing health platform.

Your task is to transform information that a patient has provided about their recent \
doctor consultation into a formal, structured medical consultation report \
(similar to a compte rendu médical).

This report will be processed by a medical AI extraction system that expects \
clinical language organised into clear sections.

## Rules
1. Only use information that is explicitly provided. Never invent diagnoses, \
medications, test values, or clinical findings.
2. Write in English. Use proper medical terminology where appropriate, but you \
may include plain language descriptions alongside clinical terms.
3. Structure the report with these exact sections:
   - PATIENT AND CONSULTATION INFORMATION
   - CHIEF COMPLAINT AND REASON FOR VISIT
   - CLINICAL PRESENTATION / REPORTED SYMPTOMS
   - CLINICAL FINDINGS (use document content if available; otherwise write \
"No additional findings documented.")
   - WORKING DIAGNOSIS (infer only if clearly supported by symptoms or documents; \
otherwise write "Working diagnosis: presenting symptoms as described above.")
   - TREATMENT PLAN AND MEDICATIONS (only from documents or explicit patient mention; \
otherwise write "No medications prescribed at this time.")
   - FOLLOW-UP INSTRUCTIONS (only if mentioned; otherwise write "Follow-up to be \
scheduled as directed by physician.")
4. Use "Patient" as a placeholder wherever a patient name is needed (not "[PATIENT]").
5. Keep the report between 300 and 600 words.
6. Do not add disclaimers, preambles, or closing remarks — output the report only.
7. If the patient provided uploaded document content, integrate relevant findings \
naturally into the appropriate sections.
8. Always include patient demographics (first name, age, sex) in the \
PATIENT AND CONSULTATION INFORMATION section exactly as provided.
9. The WORKING DIAGNOSIS section MUST include an explicit severity assessment: \
"Severity: mild / moderate / severe — [brief rationale]". If severity cannot be \
determined from available information, default to "Severity: mild — based on \
reported presentation."
10. The FOLLOW-UP INSTRUCTIONS section MUST name a specialist or physician \
responsible for follow-up (e.g., "Follow-up with the attending General Practitioner").
"""


def synthesize_report(
    title: str,
    specialty: str,
    doctor_name: str,
    visit_date: str,
    symptoms: list[str],
    summary: str,
    document_content: str,
) -> str:
    """
    Call Mistral Large to produce a formal medical report from patient input.

    Returns:
        A plain-text medical report string ready to be passed to extract().
    """
    symptoms_str = ", ".join(symptoms) if symptoms else "Not specified"
    doc_section = document_content.strip() if document_content.strip() else "[No documents uploaded]"
    summary_section = summary.strip() if summary.strip() else "[No written notes provided]"

    user_message = f"""\
CONSULTATION INFORMATION:
- Case title: {title}
- Medical specialty: {specialty}
- Attending physician: {doctor_name}
- Date of consultation: {visit_date}
- Reported symptoms: {symptoms_str}

PATIENT DEMOGRAPHICS (use these values as-is in the report header):
- Patient first name: Patient (anonymous)
- Patient age: 35 years (demographic not collected)
- Patient sex: not specified

PATIENT NOTES (patient's own description of the visit):
{summary_section}

UPLOADED DOCUMENTS (extracted content):
{doc_section}

Please produce a formal medical consultation report based on the above information.
"""

    client = Mistral(api_key=settings.mistral_api_key)
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        timeout_ms=60_000,
    )

    return response.choices[0].message.content or ""
