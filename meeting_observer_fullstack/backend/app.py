from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAIError
from config import Config
from database import initialize_database, save_meeting, list_meetings, get_meeting
from transcript_service import extract_transcript_from_upload
from ai_service import analyze_transcript

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})
initialize_database(Config.DATABASE_PATH)

SAMPLE_MEETINGS = [
    {
        "id": "sample-product",
        "title": "Q4 Product Strategy",
        "date": "07 Oct 2026",
        "team": "Product & Engineering",
        "duration": "52 min",
        "attendees": 8,
        "summary": "The team aligned on the Q4 roadmap, prioritizing mobile onboarding and enterprise analytics. Engineering will validate capacity before sprint allocation.",
        "action_count": 3,
        "decision_count": 3,
        "risk_count": 2,
        "source": "sample",
        "analysis": {
            "summary": "The team aligned on the Q4 roadmap, prioritizing mobile onboarding and enterprise analytics. Engineering will validate capacity before sprint allocation.",
            "observer_brief": "Focus on the onboarding redesign first. Engineering capacity is the main dependency; enterprise analytics remains in discovery.",
            "key_topics": ["Q4 roadmap", "Mobile onboarding", "Enterprise analytics"],
            "decisions": [
                {"decision": "Mobile onboarding redesign is the top Q4 priority.", "context": "The team agreed to prioritize the user experience.", "owner": "Product team"},
                {"decision": "Enterprise analytics will enter discovery.", "context": "Requirements need clarification before full development.", "owner": "Product team"},
                {"decision": "Engineering capacity must be validated before sprint allocation.", "context": "Current commitments may affect delivery.", "owner": "Engineering"}
            ],
            "risks": [
                {"level": "High", "title": "Engineering capacity", "description": "Current sprint commitments may delay onboarding work.", "mitigation": "Complete a capacity review.", "owner": "Arjun Mehta"},
                {"level": "Medium", "title": "Analytics scope", "description": "Requirements are not fully defined.", "mitigation": "Run a discovery workshop.", "owner": "Daniel Wong"}
            ],
            "action_items": [
                {"task": "Validate Q4 engineering capacity", "owner": "Arjun Mehta", "due_date": "09 Oct 2026", "priority": "High", "status": "Open"},
                {"task": "Prepare onboarding redesign brief", "owner": "Priya Shah", "due_date": "12 Oct 2026", "priority": "High", "status": "In progress"},
                {"task": "Draft analytics discovery scope", "owner": "Daniel Wong", "due_date": "15 Oct 2026", "priority": "Medium", "status": "Open"}
            ],
            "open_questions": ["What engineering capacity can be allocated to the redesign?"],
            "attendees_mentioned": ["Arjun Mehta", "Priya Shah", "Daniel Wong"],
            "meeting_outcome": "Needs attention",
            "confidence_note": "Illustrative sample data, not generated from a real transcript."
        }
    },
    {
        "id": "sample-delivery",
        "title": "Client Delivery Review",
        "date": "06 Oct 2026",
        "team": "Delivery",
        "duration": "41 min",
        "attendees": 6,
        "summary": "The delivery team resolved an API dependency and agreed on a revised UAT window. Client approval timing remains a concern.",
        "action_count": 2,
        "decision_count": 3,
        "risk_count": 1,
        "source": "sample",
        "analysis": {
            "summary": "The delivery team resolved an API dependency and agreed on a revised UAT window. Client approval timing remains a concern.",
            "observer_brief": "The API dependency is resolved. UAT shifts by one day; confirm client approval before production release.",
            "key_topics": ["API integration", "UAT schedule", "Client approval"],
            "decisions": [
                {"decision": "API dependency is considered resolved.", "context": "Integration blocker has been addressed.", "owner": "Engineering"},
                {"decision": "UAT will start one day later.", "context": "The team wants to protect integration quality.", "owner": "Delivery"},
                {"decision": "Client approval checkpoint is required before production.", "context": "Release must not proceed without sign-off.", "owner": "Project lead"}
            ],
            "risks": [
                {"level": "Medium", "title": "Client approval timing", "description": "A delayed sign-off could affect the release window.", "mitigation": "Confirm the checkpoint and follow up early.", "owner": "Rohan Singh"}
            ],
            "action_items": [
                {"task": "Send revised UAT schedule", "owner": "Neha Kapoor", "due_date": "07 Oct 2026", "priority": "Medium", "status": "Done"},
                {"task": "Confirm client approval checkpoint", "owner": "Rohan Singh", "due_date": "08 Oct 2026", "priority": "High", "status": "Open"}
            ],
            "open_questions": ["Has the client confirmed the approval meeting?"],
            "attendees_mentioned": ["Neha Kapoor", "Rohan Singh"],
            "meeting_outcome": "Needs attention",
            "confidence_note": "Illustrative sample data, not generated from a real transcript."
        }
    }
]

@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "Meeting Observer API",
        "openai_configured": bool(Config.OPENAI_API_KEY),
        "model": Config.OPENAI_MODEL
    })

@app.get("/api/meetings")
def meetings():
    saved = list_meetings(Config.DATABASE_PATH)
    return jsonify({"meetings": SAMPLE_MEETINGS + saved})

@app.get("/api/meetings/<meeting_id>")
def meeting_detail(meeting_id):
    if meeting_id.startswith("sample-"):
        for meeting in SAMPLE_MEETINGS:
            if meeting["id"] == meeting_id:
                return jsonify({"meeting": meeting})
        return jsonify({"error": "Meeting not found."}), 404

    try:
        numeric_id = int(meeting_id)
    except ValueError:
        return jsonify({"error": "Invalid meeting ID."}), 400

    meeting = get_meeting(Config.DATABASE_PATH, numeric_id)
    if meeting is None:
        return jsonify({"error": "Meeting not found."}), 404
    return jsonify({"meeting": meeting})

@app.post("/api/analyze")
def analyze():
    title = request.form.get("title", "Untitled meeting").strip() or "Untitled meeting"
    team = request.form.get("team", "General").strip() or "General"
    transcript = request.form.get("transcript", "").strip()

    uploaded_file = request.files.get("file")
    if uploaded_file and uploaded_file.filename:
        try:
            transcript = extract_transcript_from_upload(uploaded_file)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    if not transcript:
        return jsonify({"error": "Paste transcript text or upload a supported transcript file."}), 400

    if len(transcript) < 40:
        return jsonify({"error": "The transcript is very short. Please provide more meeting content."}), 400

    try:
        analysis = analyze_transcript(
            transcript=transcript,
            title=title,
            team=team,
            api_key=Config.OPENAI_API_KEY,
            model=Config.OPENAI_MODEL
        )
        meeting_id = save_meeting(
            Config.DATABASE_PATH, title, team, transcript, analysis
        )
        return jsonify({
            "message": "Transcript analyzed successfully.",
            "meeting_id": meeting_id,
            "meeting": {
                "id": meeting_id,
                "title": title,
                "team": team,
                "summary": analysis.get("summary", ""),
                "analysis": analysis,
                "source": "saved"
            }
        })
    except OpenAIError as error:
        app.logger.exception("OpenAI API request failed")
        return jsonify({
            "error": "OpenAI API request failed. Check your API key, API billing, model access and network connection.",
            "details": str(error)
        }), 502
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 502
    except Exception:
        app.logger.exception("Unexpected analysis error")
        return jsonify({"error": "Unexpected server error. Check the backend terminal for details."}), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({"error": "File is too large. Increase MAX_CONTENT_LENGTH_MB in backend/.env if appropriate."}), 413

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=Config.PORT, debug=True)
