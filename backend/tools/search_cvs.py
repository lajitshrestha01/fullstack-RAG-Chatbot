import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.models import CandidateORM

_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def search_cvs(
    query: str, session: AsyncSession, top_k: int = 5
) -> list[dict]:
    resp = await _client.embeddings.create(model=settings.EMBED_MODEL, input=query)
    query_vec = resp.data[0].embedding

    distance = CandidateORM.embedding.cosine_distance(query_vec).label("distance")
    stmt = (
        select(
            CandidateORM.candidate_id,
            CandidateORM.name,
            CandidateORM.current_role,
            CandidateORM.skills,
            CandidateORM.location,
            CandidateORM.years_experience,
            distance,
        )
        .where(CandidateORM.embedding.is_not(None))
        .order_by(distance.asc())
        .limit(top_k)
    )

    result = await session.execute(stmt)
    out = []
    for row in result.mappings():
        d = dict(row)
        d["candidate_id"] = str(d["candidate_id"])
        d["similarity_score"] = round(1 - d.pop("distance"), 4)
        out.append(d)
    return out


if __name__ == "__main__":
    import asyncio

    from db.database import AsyncSessionLocal

    async def demo():
        async with AsyncSessionLocal() as session:
            for q in [
                "machine learning and NLP experience",
                "frontend developer comfortable with React",
            ]:
                print(f"\n== {q} ==")
                rows = await search_cvs(q, session)
                for i, r in enumerate(rows, 1):
                    print(
                        f"{i}. {r['similarity_score']:.4f}  {r['name']:18} "
                        f"{r['current_role']}  [{r['skills']}]"
                    )
                assert rows and rows[0]["similarity_score"] >= rows[-1]["similarity_score"]

    asyncio.run(demo())
