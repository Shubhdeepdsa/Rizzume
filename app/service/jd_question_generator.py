# app/service/jd_question_generator.py

import json
from typing import Dict, Any

from pydantic import ValidationError

from app.helper.prompt_builder import build_jd_question_user_prompt
from app.prompts.jd_prompts import (
    JD_QUESTION_SYSTEM_PROMPT,
    JD_QUESTION_THIRD_PERSON_SYSTEM_PROMPT,
)
from app.schemas.jd_questions_schema import JDQuestions
from app.service.ollama_client import call_ollama_chat


def _extract_content_from_ollama_response(response: Dict[str, Any]) -> str:
    """
    Given an Ollama /api/chat response, extract the assistant content string.
    Expected shape:

    {
      "model": "...",
      "message": {
          "role": "assistant",
          "content": "..."
      },
      ...
    }
    """
    message = response.get("message") or {}
    content = message.get("content")

    if not isinstance(content, str):
        raise ValueError(f"Ollama response missing 'message.content': {response!r}")

    return content


def _parse_json_from_content(content: str) -> Dict[str, Any]:
    """
    Parse content as JSON. If the model wraps in ```json ... ``` we strip that.
    """
    text = content.strip()

    # Strip ```json ... ``` if present
    if text.startswith("```"):
        # remove starting ```
        text = text.lstrip("`")
        # often starts with 'json'
        if text.lower().startswith("json"):
            text = text[4:].strip()
        # remove trailing ```
        if text.endswith("```"):
            text = text[:-3].strip()

    return json.loads(text)


def generate_jd_questions(jd_text: str) -> JDQuestions:
    """
    High-level API:
      Input  : raw JD as text
      Output : JDQuestions (Pydantic model)

    Internally:
      - Builds messages
      - Calls Ollama via call_ollama_chat(...)
      - Extracts JSON content
      - Validates into JDQuestions
    """

    messages = [
        {"role": "system", "content": JD_QUESTION_THIRD_PERSON_SYSTEM_PROMPT},
        {"role": "user", "content": build_jd_question_user_prompt(jd_text)},
    ]

    # Low-level call: single place where we talk to Ollama
    response = call_ollama_chat(messages)

    content = _extract_content_from_ollama_response(response)

    try:
        raw_json = _parse_json_from_content(content)
    except json.JSONDecodeError as e:
        # You should log content somewhere, but for now raise.
        raise ValueError(
            f"Failed to parse Ollama content as JSON: {e}\nRaw content: {content[:500]}"
        )

    try:
        questions = JDQuestions.model_validate(raw_json)
    except ValidationError as e:
        # Again, log raw_json in real system
        raise ValueError(
            f"Response does not match JDQuestions schema: {e}\nRaw JSON: {raw_json}"
        )

    return questions
