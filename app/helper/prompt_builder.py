def build_jd_question_user_prompt(jd_text: str) -> str:
    """
    Build the user prompt for 'JD -> questions' generation.
    Keeps the logic here so the service stays thin.
    """
    return f"""
Job Description:
\"\"\" 
{jd_text}
\"\"\"

Now convert this job description into questions in the required JSON format.
""".strip()


def build_rag_question_scoring_user_prompt(question: str, evidence_text: str) -> str:
    """
    Build the user prompt for scoring a single question using retrieved resume chunks.
    """
    return f"""
Question:
\"\"\"{question}\"\"\"

Resume evidence (one or more chunks):
\"\"\" 
{evidence_text}
\"\"\"

Using ONLY this evidence, answer the question, assign a score (0–10),
and explain your reasoning in the required JSON format.
""".strip()
