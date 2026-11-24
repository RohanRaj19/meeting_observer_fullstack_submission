import json
from openai import OpenAI

SYSTEM_INSTRUCTIONS = """
You are Meeting Observer AI, an enterprise meeting analyst.
Analyze only the transcript provided. Do not invent attendees, owners, dates,
decisions, commitments, or facts. If an owner or due date is not stated,
write "Not specified". Distinguish a confirmed decision from a suggestion.
A risk must be grounded in something said in the transcript. If no risks are
mentioned, return an empty risks array. Action items must be concrete tasks.
Return only valid JSON with exactly these top-level keys:
summary, observer_brief, key_topics, decisions, risks, action_items,
open_questions, attendees_mentioned, meeting_outcome, confidence_note.

Expected structure:
{
  "summary": "string",
  "observer_brief": "string",
  "key_topics": ["string"],
  "decisions": [{"decision":"string","context":"string","owner":"string"}],
  "risks": [{"level":"High|Medium|Low","title":"string","description":"string","mitigation":"string","owner":"string"}],
  "action_items": [{"task":"string","owner":"string","due_date":"string","priority":"High|Medium|Low","status":"Open|In progress|Done"}],
  "open_questions": ["string"],
  "attendees_mentioned": ["string"],
  "meeting_outcome": "On track|Needs attention|At risk|Unclear",
  "confidence_note": "string"
}
Keep the summary concise but informative. Use "Not specified" for unknown fields.
"""

def analyze_transcript(transcript, title, team, api_key, model):
    if not api_key:
        raise RuntimeError(
            "OpenAI API key is not configured. Add OPENAI_API_KEY to backend/.env and restart the backend."
        )

    client = OpenAI(api_key=api_key)
    user_input = (
        "Meeting title: " + title + "\n"
        "Team: " + (team or "Not specified") + "\n\n"
        "Analyze the following meeting transcript:\n\n"
        + transcript
    )

    response = client.responses.create(
        model=model,
        instructions=SYSTEM_INSTRUCTIONS,
        input=user_input
    )

    output_text = response.output_text.strip()
    if not output_text:
        raise RuntimeError("The AI returned an empty response. Please try again.")

    try:
        result = json.loads(output_text)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "The AI response was not valid JSON. Please retry the analysis."
        ) from error

    required_keys = [
        "summary", "observer_brief", "key_topics", "decisions", "risks",
        "action_items", "open_questions", "attendees_mentioned",
        "meeting_outcome", "confidence_note"
    ]
    for key in required_keys:
        if key not in result:
            result[key] = [] if key in {
                "key_topics", "decisions", "risks", "action_items",
                "open_questions", "attendees_mentioned"
            } else "Not specified"

    return result
