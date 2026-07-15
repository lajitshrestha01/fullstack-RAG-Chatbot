import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import instructor
from openai import OpenAI
from pydantic import BaseModel, Field, model_validator

from config import settings


class CandidateExtraction(BaseModel):
    name: str
    years_experience: float = Field(
        description="Total years of professional experience. Best estimate from dates/roles if not stated explicitly."
    )
    skills: str = Field(description="Comma-separated list of skills, e.g. 'React, Python, SQL'")
    location: str
    current_role: str
    extraction_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Your own estimate (0-1) of how reliable this extraction is overall.",
    )
    extraction_notes: str = Field(
        description="Explain any ambiguity, guesses, or missing info encountered during extraction."
    )
    needs_review: bool = Field(
        description="True if extraction_confidence < 0.6 or any key field is missing/guessed."
    )

    @model_validator(mode="after")
    def _force_review_on_low_confidence(self):
        # enforce the confidence rule deterministically, don't trust the LLM to
        if self.extraction_confidence < 0.6:
            self.needs_review = True
        return self


# pypdf artifacts -> plain ASCII; � shows up where the PDF font mis-maps a dash
_ARTIFACTS = str.maketrans({
    "�": "-",
    "–": "-", "—": "-", "−": "-",   # en/em dash, minus
    "‘": "'", "’": "'",                   # curly single quotes
    "“": '"', "”": '"',                   # curly double quotes
    " ": " ",                                   # non-breaking space
})


def clean_pdf_text(text: str) -> str:
    return text.translate(_ARTIFACTS)


_client = instructor.from_openai(
    OpenAI(api_key=settings.GROQ_API_KEY, base_url=settings.GROQ_BASE_URL),
    mode=instructor.Mode.JSON,
)


def extract_candidate(cv_text: str) -> CandidateExtraction:
    return _client.chat.completions.create(
        model=settings.GROQ_MODEL,
        response_model=CandidateExtraction,
        max_retries=2,
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract structured candidate data from raw CV text. "
                    "Be honest about uncertainty: estimate years_experience from dates "
                    "when not explicit, rate your overall extraction_confidence 0-1, "
                    "describe every guess or gap in extraction_notes, and set "
                    "needs_review=true if confidence is below 0.6 or a key field "
                    "(name, years, skills, location, role) is missing or guessed."
                ),
            },
            {"role": "user", "content": cv_text},
        ],
    )


if __name__ == "__main__":
    from pypdf import PdfReader

    pdf_path = (
        Path(__file__).resolve().parents[1]
        / "test_data" / "sample_cv" / "lajitShrestha_CV.pdf"
    )
    reader = PdfReader(pdf_path)
    cv_text = clean_pdf_text(
        "\n".join(page.extract_text() or "" for page in reader.pages)
    )
    print(f"read {pdf_path.name}: {len(reader.pages)} page(s), {len(cv_text)} chars\n")

    result = extract_candidate(cv_text)
    print(result.model_dump_json(indent=2))
