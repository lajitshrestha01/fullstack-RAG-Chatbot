import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from tools.filter_candidates import filter_candidates
from tools.search_cvs import search_cvs

_client = AsyncOpenAI(api_key=settings.GROQ_API_KEY, base_url=settings.GROQ_BASE_URL)
AGENT_MODEL = settings.GROQ_MODEL

MAX_ITERATIONS = 5

SYSTEM_PROMPT = """You are a recruiting assistant that helps recruiters surface candidates \
from a database. You surface and rank candidates — you NEVER make hiring decisions or \
recommend rejecting anyone; the recruiter decides.

You have two tools:
- filter_candidates: use for exact, structured criteria (minimum years of experience, \
location, a specific skill keyword).
- search_cvs: use for semantic/fit-based queries (role similarity, soft requirements, \
general suitability like "comfortable making UI decisions independently").

Many queries mix both kinds of criteria — in that case call BOTH tools and combine the \
results, e.g. intersect the structured matches with the semantically similar ones.

In your final answer, always explain which tool(s) you chose and why, then present the \
matching candidates with their key details."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "filter_candidates",
            "description": "Filter candidates by exact, structured criteria: minimum years of experience, location substring, or a skill keyword. Use for hard requirements like 'at least 3 years' or 'based in Nepal'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_years": {"type": "number", "description": "Minimum years of experience"},
                    "location": {"type": "string", "description": "Case-insensitive partial match on location, e.g. 'kathmandu' or 'remote'"},
                    "skills_contains": {"type": "string", "description": "Case-insensitive keyword to match in the skills list, e.g. 'react'"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_cvs",
            "description": "Semantic search over candidate CVs by embedding similarity. Use for fit-based or fuzzy queries like role similarity or general suitability, e.g. 'frontend developer who makes UI decisions independently'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural-language description of the ideal candidate"},
                    "top_k": {"type": "integer", "description": "Number of results to return (default 5)"},
                },
                "required": ["query"],
            },
        },
    },
]


async def _execute_tool(name: str, args: dict, session: AsyncSession):
    if name == "filter_candidates":
        allowed = {k: args[k] for k in ("min_years", "location", "skills_contains") if k in args}
        return await filter_candidates(session, **allowed)
    elif name == "search_cvs":
        return await search_cvs(args["query"], session, top_k=args.get("top_k", 5))
    else:
        # unknown tool: return an error result so the model can recover, never crash
        return {
            "error": f"Unknown tool '{name}'. Available tools: filter_candidates, search_cvs."
        }


async def run_sourcing_agent(query: str, session: AsyncSession) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    last_text = ""

    for iteration in range(1, MAX_ITERATIONS + 1):
        resp = await _client.chat.completions.create(
            model=AGENT_MODEL, messages=messages, tools=TOOLS
        )
        msg = resp.choices[0].message
        if msg.content:
            last_text = msg.content

        if not msg.tool_calls:  # OpenAI equivalent of stop_reason == "end_turn"
            print(f"[iter {iteration}] final answer")
            return msg.content or ""

        messages.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            }
        )

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
                print(f"[iter {iteration}] tool call: {name}({args})")
                result = await _execute_tool(name, args, session)
            except Exception as e:
                result = {"error": f"{type(e).__name__}: {e}"}
            print(f"[iter {iteration}] result: {json.dumps(result)[:500]}")
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)}
            )

    return (
        (last_text + "\n\n" if last_text else "")
        + f"[stopped after max iterations ({MAX_ITERATIONS}) without a final answer]"
    )


if __name__ == "__main__":
    import asyncio

    from db.database import AsyncSessionLocal

    QUERY = (
        "I need someone who can build our new customer dashboard - ideally based "
        "here in Nepal, at least 3 years in the role, and should feel comfortable "
        "making UI decisions independently"
    )

    async def demo():
        async with AsyncSessionLocal() as session:
            answer = await run_sourcing_agent(QUERY, session)
            print("\n=== FINAL ANSWER ===\n")
            print(answer)

    asyncio.run(demo())
