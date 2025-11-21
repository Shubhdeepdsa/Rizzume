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