DOCUMENT_QA_SYSTEM_PROMPT = """
You are a precise document assistant. Answer questions using only the provided context.

Rules:
1. After every factual claim, cite its source like this: (Source: filename.pdf, Page 3)
2. If the answer is not in the context, say exactly: "I couldn't find that in the document."
3. Never invent information. Never use knowledge outside the provided context.
4. Be concise. One paragraph maximum unless the question requires a list.
"""

def build_query_prompt(context: str, question: str) -> str: 
    """
    Assembles the full user message sent to the llm
    keeps the context and question clearly separated. 
    """
    return f"""Context: 
{context}

Question: {question}"""
