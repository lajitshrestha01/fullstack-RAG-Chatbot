import asyncio
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openai import AsyncOpenAI
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.models import CandidateORM
from ingestion.extract import CandidateExtraction, clean_pdf_text, extract_candidate

_embed_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
_sem = asyncio.Semaphore(4)  # at most 4 concurrent LLM extractions


def _process_pdf_sync(pdf_path: Path) -> CandidateExtraction:
    reader = PdfReader(pdf_path)
    text = clean_pdf_text("\n".join(p.extract_text() or "" for p in reader.pages))
    if not text.strip():
        raise ValueError("no extractable text in PDF")
    return extract_candidate(text)


async def _process_pdf(pdf_path: Path) -> CandidateExtraction:
    # extract_candidate / pypdf are sync -> run in a thread, gated by the semaphore
    async with _sem:
        return await asyncio.to_thread(_process_pdf_sync, pdf_path)


async def ingest_zip(zip_path: str, session: AsyncSession) -> dict:
    succeeded: list[tuple[str, CandidateExtraction]] = []
    failed: list[tuple[str, str]] = []

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp)  # zipfile sanitizes '..' and absolute paths
        pdfs = sorted(Path(tmp).rglob("*.pdf"))
        print(f"found {len(pdfs)} PDF(s) in {zip_path}")

        async def run_one(pdf: Path):
            try:
                extraction = await _process_pdf(pdf)
                print(f"[ok]     {pdf.name}: {extraction.name}")
                succeeded.append((pdf.name, extraction))
            except Exception as e:
                print(f"[FAILED] {pdf.name}: {type(e).__name__}: {e}")
                failed.append((pdf.name, f"{type(e).__name__}: {e}"))

        await asyncio.gather(*(run_one(p) for p in pdfs))

    if succeeded:
        # one embeddings call for the whole batch; resp.data preserves input order
        blobs = [f"{e.current_role}. Skills: {e.skills}." for _, e in succeeded]
        resp = await _embed_client.embeddings.create(model=settings.EMBED_MODEL, input=blobs)

        session.add_all(
            CandidateORM(
                name=e.name,
                years_experience=e.years_experience,
                skills=e.skills,
                location=e.location or None,
                current_role=e.current_role,
                embedding=item.embedding,
                extraction_confidence=e.extraction_confidence,
                extraction_notes=e.extraction_notes,
                needs_review=e.needs_review,
            )
            for (_, e), item in zip(succeeded, resp.data)
        )
        await session.commit()

    return {"succeeded": succeeded, "failed": failed}


if __name__ == "__main__":
    from db.database import AsyncSessionLocal

    CV_DIR = Path(__file__).resolve().parents[1] / "test_data" / "sample_cv"

    async def demo():
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "cvs.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                for pdf in sorted(CV_DIR.glob("*.pdf")):
                    zf.write(pdf, pdf.name)

            async with AsyncSessionLocal() as session:
                summary = await ingest_zip(str(zip_path), session)

        print(f"\n=== SUMMARY: {len(summary['succeeded'])} succeeded, "
              f"{len(summary['failed'])} failed ===")
        for fname, e in summary["succeeded"]:
            print(f"  inserted: {e.name:20} confidence={e.extraction_confidence}"
                  f"  needs_review={e.needs_review}  ({fname})")
        for fname, reason in summary["failed"]:
            print(f"  failed:   {fname}: {reason}")

    asyncio.run(demo())
