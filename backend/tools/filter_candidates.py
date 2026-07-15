import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import CandidateORM


async def filter_candidates(
    session: AsyncSession,
    min_years: float | None = None,
    location: str | None = None,
    skills_contains: str | None = None,
) -> list[dict]:
    # select only the output columns — never pulls the embedding off the wire
    stmt = select(
        CandidateORM.candidate_id,
        CandidateORM.name,
        CandidateORM.years_experience,
        CandidateORM.location,
        CandidateORM.skills,
        CandidateORM.current_role,
    )
    if min_years is not None:
        stmt = stmt.where(CandidateORM.years_experience >= min_years)
    if location is not None:
        stmt = stmt.where(CandidateORM.location.ilike(f"%{location}%"))
    if skills_contains is not None:
        stmt = stmt.where(CandidateORM.skills.ilike(f"%{skills_contains}%"))

    result = await session.execute(stmt)
    return [
        {**dict(row), "candidate_id": str(row["candidate_id"])}
        for row in result.mappings()
    ]


if __name__ == "__main__":
    import asyncio

    from db.database import AsyncSessionLocal

    async def demo():
        async with AsyncSessionLocal() as session:
            rows = await filter_candidates(session, min_years=3, location="kathmandu")
            for r in rows:
                print(r)
            assert rows, "expected at least one seeded Kathmandu candidate with 3+ years"
            assert all(r["years_experience"] >= 3 for r in rows)
            assert all("kathmandu" in r["location"].lower() for r in rows)

    asyncio.run(demo())
