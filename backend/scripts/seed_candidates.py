"""One-off seed script: fake candidates with real OpenAI embeddings.

Run from anywhere:  python backend/scripts/seed_candidates.py
"""
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from openai import AsyncOpenAI

from db.database import AsyncSessionLocal
from db.models import CandidateORM

EMBED_MODEL = "text-embedding-3-small"

CANDIDATES = [
    {
        "name": "Aarav Shrestha",
        "years_experience": 5,
        "skills": "React, TypeScript, Next.js, Tailwind CSS",
        "location": "Kathmandu",
        "current_role": "Senior Frontend Developer",
        "summary": "Led the rebuild of a fintech dashboard serving 40k daily users, cutting page load time by 60%. Mentors two junior devs and owns the component library.",
    },
    {
        "name": "Priya Sharma",
        "years_experience": 3,
        "skills": "Python, Django, PostgreSQL, Redis",
        "location": "Remote",
        "current_role": "Backend Developer",
        "summary": "Built and maintains billing and subscription APIs for a SaaS product with 99.9% uptime. Introduced Redis caching that halved median API latency.",
    },
    {
        "name": "Bibek Thapa",
        "years_experience": 7,
        "skills": "Python, PyTorch, scikit-learn, pandas, MLflow",
        "location": "Kathmandu",
        "current_role": "Machine Learning Engineer",
        "summary": "Shipped a demand-forecasting model that reduced inventory waste by 18% for a retail chain. Owns the training pipeline end to end, from feature store to deployment.",
    },
    {
        "name": "Sneha Karki",
        "years_experience": 2,
        "skills": "React, Node.js, Express, MongoDB",
        "location": "Pokhara",
        "current_role": "Fullstack Developer",
        "summary": "Delivered a booking platform for local tour operators as a two-person team, handling both the REST API and the React frontend. Comfortable owning features end to end.",
    },
    {
        "name": "Rohan Maharjan",
        "years_experience": 8,
        "skills": "Node.js, TypeScript, AWS, Kubernetes, microservices",
        "location": "Remote",
        "current_role": "Staff Backend Engineer",
        "summary": "Decomposed a payments monolith into twelve services on EKS, cutting deploy time from hours to minutes. Regularly on-call and drives incident postmortems.",
    },
    {
        "name": "Anisha Gurung",
        "years_experience": 1,
        "skills": "Python, SQL, pandas, Power BI",
        "location": "Kathmandu",
        "current_role": "Junior Data Analyst",
        "summary": "Automated weekly sales reporting with Python, saving the ops team a full day per week. Building dashboards in Power BI for three departments.",
    },
    {
        "name": "Dipesh Adhikari",
        "years_experience": 4,
        "skills": "Python, Django, Django REST Framework, Celery, Docker",
        "location": "Lalitpur",
        "current_role": "Backend Developer",
        "summary": "Maintains a logistics API processing 200k shipments a month, with Celery workers for label generation and notifications. Dockerized the legacy deploy and set up CI.",
    },
    {
        "name": "Maya Tamang",
        "years_experience": 6,
        "skills": "Python, NLP, transformers, spaCy, MLOps",
        "location": "Remote",
        "current_role": "Senior Data Scientist",
        "summary": "Built a resume-parsing and matching system using transformer embeddings for a recruitment startup. Published two internal libraries for text preprocessing now used across teams.",
    },
    {
        "name": "Kiran Basnet",
        "years_experience": 3,
        "skills": "React, Redux, Jest, CSS",
        "location": "Bangalore",
        "current_role": "Frontend Developer",
        "summary": "Works on the checkout flow of a high-traffic e-commerce site, with heavy focus on A/B testing and accessibility. Raised unit test coverage of the cart module from 20% to 85%.",
    },
]


async def main():
    client = AsyncOpenAI()
    blobs = [
        f"{c['current_role']}. Skills: {c['skills']}. {c['summary']}"
        for c in CANDIDATES
    ]
    # one API call for all blobs; order of resp.data matches input order
    resp = await client.embeddings.create(model=EMBED_MODEL, input=blobs)

    async with AsyncSessionLocal() as session:
        rows = []
        for c, item in zip(CANDIDATES, resp.data):
            row = CandidateORM(
                name=c["name"],
                years_experience=c["years_experience"],
                skills=c["skills"],
                location=c["location"],
                current_role=c["current_role"],
                embedding=item.embedding,
                extraction_confidence=1.0,
                extraction_notes="seed data",
                needs_review=False,
            )
            session.add(row)
            rows.append(row)
        await session.commit()
        for row in rows:
            print(f"inserted: {row.name}  ({row.candidate_id})")


if __name__ == "__main__":
    asyncio.run(main())
