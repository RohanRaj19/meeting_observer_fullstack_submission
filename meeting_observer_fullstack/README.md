# Meeting Observer AI — Full-Stack Project

A client-style meeting intelligence application with:
- **Frontend:** React + Vite (Node.js)
- **Backend:** Python + Flask REST API
- **AI:** OpenAI Responses API through the official Python SDK
- **Storage:** SQLite for saved meeting analyses
- **Uploads:** TXT, MD, DOCX and PDF transcripts

The app converts meeting transcripts into an executive summary, decisions, risks, action items, owners, due dates, and an observer catch-up brief.

> **Important:** The OpenAI API key is never placed in the browser or frontend `.env`. It stays on the Python backend in `backend/.env`.

---

## 1. Requirements

Install:
- Python 3.10 or newer (Python 3.11 recommended)
- Node.js 20 or newer, including npm
- A text editor such as VS Code

Check versions:

```powershell
python --version
node --version
npm --version
```

## 2. Project structure

```text
meeting_observer_fullstack/
├── README.md
├── .gitignore
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── database.py
│   ├── ai_service.py
│   ├── transcript_service.py
│   ├── requirements.txt
│   ├── .env.example
│   └── instance/
│       └── .gitkeep
└── frontend/
    ├── package.json
    ├── index.html
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        └── styles.css
```

## 3. Configure the OpenAI API key

1. Open the OpenAI API platform: https://platform.openai.com/api-keys
2. Create a **secret API key**.
3. Copy the key once and keep it private.
4. In the project, open `backend`.
5. Copy `.env.example` and rename the copy to `.env`.
6. Open `backend/.env` and replace the placeholder:

```env
OPENAI_API_KEY=your_secret_api_key_here
OPENAI_MODEL=gpt-6.2-sol
FLASK_ENV=development
PORT=5000
DATABASE_PATH=instance/meeting_observer.db
MAX_CONTENT_LENGTH_MB=15
```

The model name is configurable. If your API account does not have access to the configured model, change `OPENAI_MODEL` to a model available to your API account.

**Never:**
- paste your key into React code;
- commit `backend/.env` to GitHub;
- share screenshots that show your key;
- use a ChatGPT subscription as a substitute for API billing. API usage is billed separately on the API platform.

## 4. Start the Python backend

Open PowerShell in the project root:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create your `.env` as explained above, then start Flask:

```powershell
python app.py
```

Backend URL:

```text
http://127.0.0.1:5000
```

Health check:

```text
http://127.0.0.1:5000/api/health
```

Keep this terminal open.

## 5. Start the Node.js frontend

Open a **second** PowerShell terminal in the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite. Normally:

```text
http://localhost:5173
```

Keep both terminals open while using the application.

## 6. How the AI connection works

```text
React UI (Node/Vite)
       |
       | transcript upload / text
       v
Flask REST API (Python)
       |
       | validates and extracts transcript text
       v
OpenAI Python SDK
       |
       | Responses API request + instructions
       v
OpenAI model
       |
       | structured JSON response
       v
Python validation + SQLite persistence
       |
       v
React renders summary, decisions, risks and actions
```

The browser sends the transcript to Flask. Flask reads `OPENAI_API_KEY` from its server environment and calls the OpenAI API. The API key is not sent to the browser.

## 7. How to use the app

1. Open the frontend.
2. Choose one of the sample meetings to inspect its saved brief, or use **Analyze transcript**.
3. Paste transcript text or upload TXT, MD, DOCX or PDF.
4. Enter a meeting title and select **Analyze with AI**.
5. The backend sends the transcript to the configured OpenAI model.
6. Review the generated summary, decisions, risks, action items, owners and due dates.
7. Analyses are saved in the local SQLite database and appear in the meeting library.

## 8. Troubleshooting

### `python` is not recognized
Try `py` instead:

```powershell
py -m venv venv
```

### PowerShell blocks virtual environment activation
Run this once in the current PowerShell window:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\activate
```

### `npm` is not recognized
Install Node.js LTS, close PowerShell, open it again, and check `node --version`.

### Frontend says it cannot connect to the backend
- Confirm the Flask terminal is still running.
- Open `http://127.0.0.1:5000/api/health`.
- Confirm the frontend is running at `http://localhost:5173`.

### API key or authentication error
- Confirm the file is named exactly `backend/.env`, not `.env.txt`.
- Check that the key is copied correctly and has not been revoked.
- Restart the Flask server after changing `.env`.
- Check API billing/credits and model access in your API platform account.

### Model not available
Change `OPENAI_MODEL` in `backend/.env` to a model available to your API project, then restart Flask.

### PDF/DOCX extraction issue
For best results, use text-based PDFs and DOCX files. Scanned image-only PDFs need OCR, which is not included in this starter project.

## 9. Stop the application

In each terminal, press:

```text
CTRL + C
```

## 10. Before submitting or publishing

- Do not include your real `.env` file or API key in the submission ZIP.
- Keep `.env.example` in the project.
- Include screenshots or a short demo video if required.
- This is a working educational prototype. A production enterprise deployment should add authentication, role-based access, audit logs, encrypted storage, retention controls, malware scanning, rate limiting, and human review for consequential decisions.
- Meeting transcripts can contain confidential or personal information. Obtain permission and follow your organization's data handling rules before sending them to an external AI service.

## 11. Main API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Backend health check |
| GET | `/api/meetings` | List saved and sample meetings |
| GET | `/api/meetings/<id>` | Get one meeting analysis |
| POST | `/api/analyze` | Analyze transcript text or uploaded file |

## 12. Suggested project explanation for your evaluator

“Meeting Observer AI is a full-stack application. The React frontend lets an employee select a meeting or upload a transcript. The Python Flask backend validates the input, extracts text from supported files, and securely calls the OpenAI Responses API using a server-side API key. The model returns a structured meeting brief containing a summary, decisions, risks and action items. The backend validates and stores the result in SQLite, and the frontend displays the information in an observer-focused dashboard.”
