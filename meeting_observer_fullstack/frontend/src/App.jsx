import { useEffect, useMemo, useState } from "react";

async function apiRequest(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "The request failed.");
  }
  return data;
}

function App() {
  const [meetings, setMeetings] = useState([]);
  const [selectedMeeting, setSelectedMeeting] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [title, setTitle] = useState("");
  const [team, setTeam] = useState("General");
  const [transcript, setTranscript] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [apiHealth, setApiHealth] = useState(null);

  async function loadMeetings() {
    try {
      const data = await apiRequest("/api/meetings");
      setMeetings(data.meetings);
      if (data.meetings.length > 0 && selectedMeeting === null) {
        setSelectedMeeting(data.meetings[0]);
      }
    } catch (error) {
      setMessage(error.message);
    }
  }

  useEffect(() => {
    loadMeetings();
    apiRequest("/api/health")
      .then((data) => setApiHealth(data))
      .catch(() => setApiHealth({ status: "offline", openai_configured: false }));
  }, []);

  async function openMeeting(meetingId) {
    try {
      const data = await apiRequest(`/api/meetings/${meetingId}`);
      setSelectedMeeting(data.meeting);
      setActiveTab("overview");
      setMessage("");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function analyzeTranscript(event) {
    event.preventDefault();
    if (!transcript.trim() && !file) {
      setMessage("Paste transcript text or choose a transcript file.");
      return;
    }

    const formData = new FormData();
    formData.append("title", title.trim() || "Untitled meeting");
    formData.append("team", team.trim() || "General");
    formData.append("transcript", transcript);
    if (file) {
      formData.append("file", file);
    }

    setLoading(true);
    setMessage("Analyzing transcript with the configured OpenAI model…");
    try {
      const data = await apiRequest("/api/analyze", {
        method: "POST",
        body: formData
      });
      setSelectedMeeting(data.meeting);
      setTranscript("");
      setFile(null);
      setTitle("");
      setActiveTab("overview");
      setMessage("Analysis completed and saved to your local meeting library.");
      await loadMeetings();
      setSelectedMeeting(data.meeting);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  const analysis = selectedMeeting?.analysis || {};
  const actionItems = Array.isArray(analysis.action_items) ? analysis.action_items : [];
  const decisions = Array.isArray(analysis.decisions) ? analysis.decisions : [];
  const risks = Array.isArray(analysis.risks) ? analysis.risks : [];
  const topics = Array.isArray(analysis.key_topics) ? analysis.key_topics : [];
  const openQuestions = Array.isArray(analysis.open_questions) ? analysis.open_questions : [];

  const meetingDate = useMemo(() => {
    if (!selectedMeeting) return "";
    return selectedMeeting.date || selectedMeeting.created_at?.slice(0, 10) || "Recently analyzed";
  }, [selectedMeeting]);

  function renderOverview() {
    return (
      <>
        <div className="stat-grid">
          <Stat value={actionItems.length} label="Action items" />
          <Stat value={decisions.length} label="Decisions" />
          <Stat value={risks.length} label="Risks flagged" />
          <Stat value={analysis.meeting_outcome || "—"} label="Meeting outcome" />
        </div>
        <div className="content-grid">
          <section className="panel">
            <SectionLabel>EXECUTIVE SUMMARY</SectionLabel>
            <h2>What happened?</h2>
            <p className="summary-text">{analysis.summary || selectedMeeting?.summary || "Choose a meeting to view its summary."}</p>
            <div className="separator" />
            <SectionLabel>OBSERVER BRIEF</SectionLabel>
            <h2>What you need to know</h2>
            <p className="summary-text">{analysis.observer_brief || "The observer brief will appear here."}</p>
            <div className="separator" />
            <SectionLabel>KEY TOPICS</SectionLabel>
            <div className="chip-row">{topics.map((topic, index) => <span className="topic-chip" key={index}>{topic}</span>)}</div>
          </section>
          <section className="panel">
            <SectionLabel>RISK RADAR</SectionLabel>
            <h2>What needs attention?</h2>
            {risks.length ? risks.map((risk, index) => <RiskCard risk={risk} key={index} />) : <EmptyState text="No risks were extracted from this transcript." />}
          </section>
        </div>
      </>
    );
  }

  function renderActions() {
    return (
      <section className="panel">
        <SectionLabel>OWNERSHIP & FOLLOW-THROUGH</SectionLabel>
        <h2>Who is doing what?</h2>
        {actionItems.length ? actionItems.map((item, index) => (
          <div className="action-row" key={index}>
            <div className="action-mark">✓</div>
            <div className="action-main">
              <strong>{item.task}</strong>
              <span>Owner: {item.owner || "Not specified"}</span>
            </div>
            <div className="action-meta">
              <span>{item.due_date || "No due date"}</span>
              <span className="status-tag">{item.status || "Open"} · {item.priority || "Unrated"}</span>
            </div>
          </div>
        )) : <EmptyState text="No action items were identified." />}
      </section>
    );
  }

  function renderDecisions() {
    return (
      <section className="panel">
        <SectionLabel>DECISION LOG</SectionLabel>
        <h2>Decisions made in the room</h2>
        {decisions.length ? decisions.map((item, index) => (
          <div className="decision-row" key={index}>
            <span className="decision-check">✓</span>
            <div><strong>{item.decision}</strong><p>{item.context || "No additional context provided."}</p><small>Owner: {item.owner || "Not specified"}</small></div>
          </div>
        )) : <EmptyState text="No explicit decisions were identified." />}
      </section>
    );
  }

  function renderRisks() {
    return (
      <section className="panel">
        <SectionLabel>RISK RADAR</SectionLabel>
        <h2>Issues an observer should know</h2>
        {risks.length ? risks.map((risk, index) => (
          <div className="risk-detail" key={index}>
            <RiskCard risk={risk} />
            <p><b>Mitigation:</b> {risk.mitigation || "Not specified"}</p>
            <p><b>Owner:</b> {risk.owner || "Not specified"}</p>
          </div>
        )) : <EmptyState text="No risks were identified in the transcript." />}
        <div className="separator" />
        <SectionLabel>OPEN QUESTIONS</SectionLabel>
        {openQuestions.length ? <ul className="clean-list">{openQuestions.map((question, index) => <li key={index}>{question}</li>)}</ul> : <p className="muted">No open questions were extracted.</p>}
      </section>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">MO</div>
          <div><b>Meeting Observer</b><span>AI Workspace</span></div>
        </div>
        <div className="nav-caption">WORKSPACE</div>
        <button className="nav-item active">▦ <span>Meetings</span></button>
        <button className="nav-item" onClick={() => setActiveTab("actions")}>☷ <span>Action tracker</span></button>
        <button className="nav-item" onClick={() => setActiveTab("risks")}>⚑ <span>Risk radar</span></button>
        <button className="nav-item" onClick={() => setActiveTab("decisions")}>✓ <span>Decisions</span></button>
        <div className="sidebar-note">
          <span className="eyebrow">OBSERVER MODE</span>
          <b>Catch up without being there.</b>
          <p>Turn long conversations into clear, decision-ready briefs.</p>
        </div>
        <div className="sidebar-foot">FULL-STACK PROJECT · LOCAL DEMO</div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <div className="eyebrow">AI MEETING INTELLIGENCE</div>
            <h1>Your meeting catch-up center</h1>
            <p>Select a meeting you missed or upload a transcript to generate a new observer brief.</p>
          </div>
          <div className="user-avatar">RR</div>
        </header>

        <section className="hero">
          <div>
            <div className="hero-kicker">MEETING INTELLIGENCE · BUILT FOR THE ABSENT OBSERVER</div>
            <h2>Never be the person asking,<br />“What did I miss?”</h2>
            <p>Get the context, decisions, risks, owners and next steps from one clear workspace.</p>
          </div>
          <div className="hero-side">
            <div className="hero-icon">✦</div>
            <b>AI-powered catch-up</b>
            <span>Transcript → Insights → Action</span>
          </div>
        </section>

        {message && <div className="notice" role="status">{message}</div>}

        <section className="section-heading">
          <div><h2>Meeting library</h2><p>Choose a meeting you could not attend.</p></div>
          <span className="library-count">{meetings.length} meetings</span>
        </section>

        <div className="meeting-grid">
          {meetings.map((meeting) => (
            <button className={`meeting-card ${selectedMeeting?.id === meeting.id ? "selected" : ""}`} key={meeting.id} onClick={() => openMeeting(meeting.id)}>
              <div className="meeting-card-top"><span className="completed-badge">COMPLETED</span><span>{meeting.duration || "Saved analysis"}</span></div>
              <h3>{meeting.title}</h3>
              <p>{meeting.date || meeting.created_at?.slice(0, 10)} · {meeting.team || "General"}</p>
              <div className="meeting-counts"><span>{meeting.action_count ?? 0} actions</span><span>{meeting.decision_count ?? 0} decisions</span><span>{meeting.risk_count ?? 0} risks</span></div>
              <div className="card-link">Open observer brief <span>→</span></div>
            </button>
          ))}
        </div>

        {selectedMeeting && (
          <section className="brief-section">
            <div className="brief-heading">
              <div><div className="eyebrow">OBSERVER BRIEF · {meetingDate}</div><h2>{selectedMeeting.title}</h2><p>{selectedMeeting.team || "General"} · {selectedMeeting.source === "sample" ? "Illustrative sample meeting" : "Saved AI analysis"}</p></div>
              <span className="analysis-badge">● {selectedMeeting.source === "sample" ? "SAMPLE DATA" : "AI ANALYZED"}</span>
            </div>
            <div className="tabs">
              <button className={activeTab === "overview" ? "tab active" : "tab"} onClick={() => setActiveTab("overview")}>Overview</button>
              <button className={activeTab === "actions" ? "tab active" : "tab"} onClick={() => setActiveTab("actions")}>Action tracker</button>
              <button className={activeTab === "risks" ? "tab active" : "tab"} onClick={() => setActiveTab("risks")}>Risk radar</button>
              <button className={activeTab === "decisions" ? "tab active" : "tab"} onClick={() => setActiveTab("decisions")}>Decisions</button>
            </div>
            {activeTab === "overview" && renderOverview()}
            {activeTab === "actions" && renderActions()}
            {activeTab === "risks" && renderRisks()}
            {activeTab === "decisions" && renderDecisions()}
          </section>
        )}

        <section className="upload-section">
          <div className="upload-heading">
            <div className="eyebrow">NEW ANALYSIS</div>
            <h2>Turn a transcript into a meeting brief</h2>
            <p>Paste transcript text or upload a TXT, MD, DOCX or text-based PDF file.</p>
          </div>
          <form onSubmit={analyzeTranscript} className="upload-form">
            <div className="form-grid">
              <label>Meeting title<input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="e.g. Weekly project review" /></label>
              <label>Team / department<input value={team} onChange={(event) => setTeam(event.target.value)} placeholder="e.g. Product & Engineering" /></label>
            </div>
            <label className="file-label">Upload transcript file<input type="file" accept=".txt,.md,.docx,.pdf" onChange={(event) => setFile(event.target.files?.[0] || null)} /></label>
            {file && <div className="file-selected">Selected: {file.name}</div>}
            <div className="or-divider"><span>OR PASTE TRANSCRIPT</span></div>
            <textarea value={transcript} onChange={(event) => setTranscript(event.target.value)} placeholder="Paste the meeting transcript here. Include speaker names and timestamps when available." />
            <div className="form-footer">
              <span className="muted">Your API key stays on the Python backend.</span>
              <button className="primary-button" type="submit" disabled={loading}>{loading ? "Analyzing…" : "✦ Analyze with AI"}</button>
            </div>
          </form>
          <div className="backend-status">
            <span className={apiHealth?.status === "ok" ? "status-dot online" : "status-dot"}></span>
            Backend {apiHealth?.status === "ok" ? "connected" : "not connected"}
            <span className="status-divider">·</span>
            OpenAI {apiHealth?.openai_configured ? "key configured" : "key not configured"}
          </div>
        </section>
        <footer className="footer">Meeting Observer AI · React frontend · Python Flask backend · SQLite · OpenAI Responses API</footer>
      </main>
    </div>
  );
}

function Stat({ value, label }) {
  return <div className="stat-card"><b>{value}</b><span>{label}</span></div>;
}

function SectionLabel({ children }) {
  return <div className="section-label">{children}</div>;
}

function RiskCard({ risk }) {
  const level = (risk.level || "Medium").toLowerCase();
  return (
    <div className={`risk-card ${level}`}>
      <div className="risk-top"><span>{risk.level || "Unrated"} RISK</span><span>!</span></div>
      <strong>{risk.title}</strong>
      <p>{risk.description}</p>
    </div>
  );
}

function EmptyState({ text }) {
  return <div className="empty-state">{text}</div>;
}

export default App;
