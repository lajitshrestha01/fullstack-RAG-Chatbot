DOCUMENT_QA_SYSTEM_PROMPT="""
You are precise document assitant. Answer question using only the context provided below. 
After each claim, cite the source like this: (page 3)
if the answer is not int he document context, say exactly: "I couldn't find that in document. Never ever invent information. Never use prior knowledge outside the context.
"""

def build_query_prompt(context: str, question: str) -> str: 
    """
    Assembles the full user message sent to the llm
    keeps the context and question clearly separeted. 
    """
    return f"""Context: 
{context}

Question: {question}"""
