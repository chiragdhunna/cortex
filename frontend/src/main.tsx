import { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

type Job = {
  id: string;
  status: string;
  stage: string;
  error?: string;
  category: string;
  formats: string[];
};

const api = import.meta.env.VITE_API_URL || "http://localhost:8000";

const CATEGORY_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  interview: { label: "Interview Prep", icon: "🎯", color: "var(--accent-interview)" },
  exam: { label: "Exam Prep", icon: "📚", color: "var(--accent-exam)" },
  understanding: { label: "Deep Understanding", icon: "🧠", color: "var(--accent-understanding)" },
};

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  queued: { label: "Queued", color: "#6b7280" },
  transcribing: { label: "Transcribing", color: "#f59e0b" },
  generating_notes: { label: "Generating Notes", color: "#8b5cf6" },
  formatting: { label: "Formatting", color: "#3b82f6" },
  done: { label: "Complete", color: "#10b981" },
  failed: { label: "Failed", color: "#ef4444" },
};

const STAGE_LABELS: Record<string, string> = {
  queued: "Awaiting processing",
  ingestion: "Extracting content from source",
  generation: "Running category-aware LLM generation",
  formatting: "Rendering output formats",
  done: "All stages complete",
};

const FORMAT_LABELS: Record<string, { label: string; icon: string }> = {
  markdown: { label: "Markdown", icon: "📝" },
  pdf: { label: "PDF", icon: "📄" },
  anki_csv: { label: "Anki CSV", icon: "🗂️" },
  json: { label: "JSON", icon: "{ }" },
};

function StatusBadge({ status }: { status: string }) {
  const s = STATUS_LABELS[status] || { label: status, color: "#6b7280" };
  return (
    <span className="status-badge" style={{ backgroundColor: s.color + "20", color: s.color, borderColor: s.color + "40" }}>
      <span className={`status-dot ${status === "done" ? "pulse-done" : status === "failed" ? "" : "spinner"}`} />
      {s.label}
    </span>
  );
}

function CategoryChip({ category }: { category: string }) {
  const c = CATEGORY_LABELS[category] || { label: category, icon: "📌", color: "#6b7280" };
  return (
    <span className="category-chip" style={{ background: c.color + "18", color: c.color, borderColor: c.color + "40" }}>
      <span className="chip-icon">{c.icon}</span>
      {c.label}
    </span>
  );
}

function ProgressBar({ stage, status }: { stage: string; status: string }) {
  const stages = ["queued", "ingestion", "generation", "formatting", "done"];
  const currentIndex = status === "done" ? 4 : status === "failed" ? stages.indexOf(stage) : stages.indexOf(stage);
  const progress = status === "done" ? 100 : status === "failed" ? ((currentIndex + 1) / stages.length) * 100 : ((currentIndex + 1) / stages.length) * 100;

  return (
    <div className="progress-wrap">
      <div className="progress-stages">
        {stages.map((s, i) => (
          <div key={s} className={`progress-step ${i <= currentIndex ? "active" : ""} ${status === "failed" && i === currentIndex ? "failed" : ""}`}>
            <div className="step-num">{i + 1}</div>
            <div className="step-label">
              {s === "queued" && "Queue"}
              {s === "ingestion" && "Ingest"}
              {s === "generation" && "Generate"}
              {s === "formatting" && "Format"}
              {s === "done" && "Done"}
            </div>
          </div>
        ))}
      </div>
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{
            width: `${Math.max(progress, 8)}%`,
            background: status === "failed" ? "linear-gradient(90deg,#ef4444,#f87171)" : "linear-gradient(90deg,#6366f1,#8b5cf6,#ec4899)",
          }}
        />
      </div>
    </div>
  );
}

function Notes({ notes }: { notes: any }) {
  const cat = notes.category as keyof typeof CATEGORY_LABELS;
  const catInfo = CATEGORY_LABELS[cat] || CATEGORY_LABELS.interview;

  return (
    <div className="notes-viewer">
      <div className="notes-header" style={{ borderLeftColor: catInfo.color }}>
        <div>
          <div className="notes-title-row">
            <span className="notes-icon">{catInfo.icon}</span>
            <h2>{notes.source_title || "Untitled Source"}</h2>
          </div>
          <div className="notes-meta">
            <CategoryChip category={cat} />
            <span className="notes-date">Generated {new Date(notes.generated_at).toLocaleString()}</span>
          </div>
        </div>
      </div>

      <div className="notes-topics">
        {notes.topics?.map((topic: any, idx: number) => (
          <article key={topic.title + idx} className="topic-card">
            <div className="topic-header">
              <span className="topic-num">{String(idx + 1).padStart(2, "0")}</span>
              <h3>{topic.title}</h3>
            </div>

            {topic.content.qa_pairs && (
              <div className="qa-section">
                {topic.content.qa_pairs.map((x: any, i: number) => (
                  <details key={i} open={i < 2} className="qa-item">
                    <summary>
                      <span className={`diff-tag diff-${x.difficulty}`}>{x.difficulty?.toUpperCase()}</span>
                      <strong className="qa-q">Q: {x.q}</strong>
                    </summary>
                    <div className="qa-a"><b>A:</b> {x.a}</div>
                  </details>
                ))}
                {topic.content.talking_points?.length > 0 && (
                  <div className="talking-points">
                    <h4>💬 Talking Points</h4>
                    <ul>{topic.content.talking_points.map((p: string, i: number) => <li key={i}>{p}</li>)}</ul>
                  </div>
                )}
                {topic.content.gotchas?.length > 0 && (
                  <div className="gotchas">
                    <h4>⚠️ Gotchas</h4>
                    <ul>{topic.content.gotchas.map((g: string, i: number) => <li key={i}>{g}</li>)}</ul>
                  </div>
                )}
              </div>
            )}

            {topic.content.definitions && (
              <div className="exam-section">
                {topic.content.summary && (
                  <div className="exam-summary">
                    <h4>📋 Summary</h4>
                    <p>{topic.content.summary}</p>
                  </div>
                )}
                {topic.content.definitions.length > 0 && (
                  <div className="definitions">
                    <h4>📖 Key Definitions</h4>
                    <div className="def-grid">
                      {topic.content.definitions.map((x: any, i: number) => (
                        <div key={i} className="def-card">
                          <div className="def-term">{x.term}</div>
                          <div className="def-body">{x.definition}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {topic.content.self_test?.length > 0 && (
                  <div className="self-test">
                    <h4>✍️ Self-Test Questions</h4>
                    {topic.content.self_test.map((x: any, i: number) => (
                      <details key={i} className="self-test-item">
                        <summary><strong>{i + 1}. {x.q}</strong></summary>
                        <div className="self-test-a">{x.a}</div>
                      </details>
                    ))}
                  </div>
                )}
              </div>
            )}

            {topic.content.explanation && (
              <div className="understanding-section">
                <div className="explanation-block">
                  <h4>🔍 Explanation</h4>
                  <p>{topic.content.explanation}</p>
                </div>
                {topic.content.analogies?.length > 0 && (
                  <div className="analogies">
                    <h4>💡 Analogies</h4>
                    <ul>{topic.content.analogies.map((a: string, i: number) => <li key={i}>{a}</li>)}</ul>
                  </div>
                )}
                {topic.content.prerequisites?.length > 0 && (
                  <div className="prereqs">
                    <h4>🎒 Prerequisites</h4>
                    <div className="prereq-tags">
                      {topic.content.prerequisites.map((p: string, i: number) => <span key={i} className="prereq-tag">{p}</span>)}
                    </div>
                  </div>
                )}
                {topic.content.concept_map && topic.content.concept_map.nodes?.length > 0 && (
                  <div className="concept-map">
                    <h4>🗺️ Concept Map</h4>
                    <div className="concept-nodes">
                      {topic.content.concept_map.nodes.map((n: string, i: number) => (
                        <span key={i} className="concept-node">{n}</span>
                      ))}
                    </div>
                    {topic.content.concept_map.edges?.length > 0 && (
                      <div className="concept-edges">
                        {topic.content.concept_map.edges.map((edge: string[], i: number) => (
                          <div key={i} className="concept-edge">
                            <span className="edge-from">{edge[0]}</span>
                            <span className="edge-arrow">→</span>
                            <span className="edge-to">{edge[1]}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}

function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selected, setSelected] = useState<Job | null>(null);
  const [notes, setNotes] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);
  const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">("checking");
  const [tab, setTab] = useState<"submit" | "history" | "result">("submit");
  const [regenCategory, setRegenCategory] = useState("interview");
  const [newFormats, setNewFormats] = useState<string[]>(["markdown"]);

  const refresh = () => {
    fetch(`${api}/jobs`)
      .then((r) => r.json())
      .then((data) => {
        setJobs(Array.isArray(data) ? data : []);
        if (selected) {
          const updated = (Array.isArray(data) ? data : []).find((j) => j.id === selected.id);
          if (updated) setSelected(updated);
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    fetch(`${api}/health`)
      .then(() => setApiStatus("online"))
      .catch(() => setApiStatus("offline"));
    refresh();
    const timer = setInterval(refresh, 2500);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (selected && selected.status === "done") {
      fetch(`${api}/jobs/${selected.id}/result`)
        .then((r) => (r.ok ? r.json() : null))
        .then((n) => n && setNotes(n))
        .catch(() => {});
    } else {
      setNotes(null);
    }
  }, [selected?.id, selected?.status]);

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const form = new FormData(e.currentTarget);
      const file = form.get("file") as File;
      let response: Response;
      if (file?.size) {
        response = await fetch(`${api}/jobs/upload`, { method: "POST", body: form });
      } else {
        response = await fetch(`${api}/jobs`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: form.get("url"),
            source_type: form.get("source_type"),
            category: form.get("category"),
            formats: form.getAll("formats") as string[],
          }),
        });
      }
      if (!response.ok) {
        const text = await response.text();
        alert(text);
      } else {
        e.currentTarget.reset();
        setTab("history");
      }
      refresh();
    } finally {
      setSubmitting(false);
    }
  };

  const choose = (job: Job) => {
    setSelected(job);
    setTab("result");
  };

  const regenerate = async () => {
    if (!selected) return;
    await fetch(`${api}/jobs/${selected.id}/regenerate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ category: regenCategory }),
    });
    refresh();
  };

  const addFormat = async () => {
    if (!selected) return;
    await fetch(`${api}/jobs/${selected.id}/format`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ formats: newFormats }),
    });
    refresh();
  };

  const doneCount = useMemo(() => jobs.filter((j) => j.status === "done").length, [jobs]);
  const activeCount = useMemo(() => jobs.filter((j) => !["done", "failed", "queued"].includes(j.status)).length, [jobs]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <div className="brand-logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-2.04Z" />
              <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-2.04Z" />
            </svg>
          </div>
          <div>
            <h1 className="brand-title">Cortex</h1>
            <p className="brand-subtitle">Multimodal notes generation for study & interview prep</p>
          </div>
        </div>
        <div className="header-actions">
          <div className={`api-status ${apiStatus}`}>
            <span className="api-dot" />
            {apiStatus === "online" ? "API Online" : apiStatus === "offline" ? "API Offline" : "Connecting..."}
          </div>
          <div className="stats">
            <div className="stat"><span className="stat-num">{jobs.length}</span><span className="stat-label">Total</span></div>
            <div className="stat active"><span className="stat-num">{activeCount}</span><span className="stat-label">Active</span></div>
            <div className="stat done"><span className="stat-num">{doneCount}</span><span className="stat-label">Done</span></div>
          </div>
        </div>
      </header>

      <nav className="tabs">
        <button className={`tab ${tab === "submit" ? "active" : ""}`} onClick={() => setTab("submit")}>
          <span>🚀</span> New Job
        </button>
        <button className={`tab ${tab === "history" ? "active" : ""}`} onClick={() => setTab("history")}>
          <span>📋</span> Job History {jobs.length > 0 && <span className="tab-count">{jobs.length}</span>}
        </button>
        <button className={`tab ${tab === "result" && selected ? "active" : ""}`} onClick={() => selected && setTab("result")} disabled={!selected}>
          <span>📊</span> {selected ? "Job Details" : "Select a Job"}
        </button>
      </nav>

      <main className="app-main">
        {tab === "submit" && (
          <section className="submit-panel card">
            <div className="card-header">
              <h2>Submit a New Job</h2>
              <p>Upload a file or paste a link, then pick your note category and output formats.</p>
            </div>
            <form onSubmit={submit} className="submit-form">
              <div className="form-section upload-section">
                <h3>1. Choose Source</h3>
                <div className="source-grid">
                  <label className="file-drop">
                    <input name="file" type="file" accept=".pdf,.mp3,.wav,.m4a,.mp4,.mov" />
                    <div className="drop-zone">
                      <div className="drop-icon">📁</div>
                      <div className="drop-text">
                        <strong>Drop a file here</strong> or click to browse
                      </div>
                      <div className="drop-hint">PDF · MP3 · WAV · M4A · MP4 · MOV</div>
                    </div>
                  </label>
                  <div className="or-divider"><span>OR</span></div>
                  <div className="link-inputs">
                    <input name="url" type="url" placeholder="https://youtube.com/watch?v=...  or  podcast URL" className="url-input" />
                    <select name="source_type" className="source-select">
                      <option value="video_link">🎬 Video Link (YouTube, etc.)</option>
                      <option value="audio_link">🎧 Audio Link (Podcast, etc.)</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="form-section">
                <h3>2. Note Category</h3>
                <div className="category-grid">
                  {Object.entries(CATEGORY_LABELS).map(([key, info]) => (
                    <label key={key} className="cat-option">
                      <input type="radio" name="category" value={key} defaultChecked={key === "understanding"} />
                      <div className="cat-card" style={{ borderColor: info.color + "50" }}>
                        <div className="cat-icon" style={{ background: info.color + "20", color: info.color }}>{info.icon}</div>
                        <div className="cat-name">{info.label}</div>
                        <div className="cat-desc">
                          {key === "interview" && "Q&A pairs, talking points, gotchas, difficulty tags"}
                          {key === "exam" && "Definitions, summaries, self-test questions"}
                          {key === "understanding" && "Explanations, analogies, prerequisites, concept map"}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-section">
                <h3>3. Output Formats</h3>
                <div className="formats-grid">
                  {Object.entries(FORMAT_LABELS).map(([key, info]) => (
                    <label key={key} className="format-option">
                      <input type="checkbox" name="formats" value={key} defaultChecked={key === "markdown"} />
                      <div className="format-card">
                        <div className="format-icon">{info.icon}</div>
                        <div className="format-name">{info.label}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-actions">
                <button type="submit" disabled={submitting} className="submit-btn">
                  {submitting ? (
                    <>
                      <span className="spinner-submit" /> Submitting...
                    </>
                  ) : (
                    <>
                      <span>✨</span> Generate Notes
                    </>
                  )}
                </button>
              </div>
            </form>
          </section>
        )}

        {tab === "history" && (
          <section className="history-panel card">
            <div className="card-header">
              <h2>Job History</h2>
              <p>All submitted jobs, newest first. Click any job to view results and download outputs.</p>
            </div>
            {jobs.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">📭</div>
                <h3>No jobs yet</h3>
                <p>Submit your first job using the "New Job" tab to get started.</p>
                <button className="empty-btn" onClick={() => setTab("submit")}>Create First Job →</button>
              </div>
            ) : (
              <div className="job-list">
                {jobs.map((job) => (
                  <button
                    key={job.id}
                    className={`job-card ${selected?.id === job.id ? "selected" : ""}`}
                    onClick={() => choose(job)}
                  >
                    <div className="job-head">
                      <CategoryChip category={job.category} />
                      <StatusBadge status={job.status} />
                    </div>
                    <div className="job-meta-row">
                      <span className="job-stage">Stage: {STAGE_LABELS[job.stage] || job.stage}</span>
                    </div>
                    <ProgressBar stage={job.stage} status={job.status} />
                    <div className="job-formats">
                      {job.formats.map((f) => (
                        <span key={f} className="fmt-tag">{FORMAT_LABELS[f]?.icon} {FORMAT_LABELS[f]?.label || f}</span>
                      ))}
                    </div>
                    {job.error && <div className="job-error">⚠️ {job.error}</div>}
                    <div className="job-id">ID: {job.id.slice(0, 8)}…</div>
                  </button>
                ))}
              </div>
            )}
          </section>
        )}

        {tab === "result" && (
          <section className="result-panel">
            {!selected ? (
              <div className="card empty-state">
                <div className="empty-icon">👈</div>
                <h3>Select a job from the history</h3>
                <p>Open the Job History tab and click a job to see its details, notes, and downloads.</p>
              </div>
            ) : (
              <>
                <div className="card job-detail">
                  <div className="card-header detail-header">
                    <div>
                      <h2>Job Details</h2>
                      <div className="detail-meta">
                        <CategoryChip category={selected.category} />
                        <StatusBadge status={selected.status} />
                        <span className="detail-id">ID: {selected.id}</span>
                      </div>
                    </div>
                  </div>
                  <ProgressBar stage={selected.stage} status={selected.status} />
                  <div className="detail-info-grid">
                    <div className="info-block">
                      <span className="info-label">Current Stage</span>
                      <span className="info-value">{STAGE_LABELS[selected.stage] || selected.stage}</span>
                    </div>
                    <div className="info-block">
                      <span className="info-label">Output Formats</span>
                      <div className="info-value">
                        {selected.formats.map((f) => (
                          <span key={f} className="fmt-tag">{FORMAT_LABELS[f]?.icon} {FORMAT_LABELS[f]?.label || f}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                  {selected.error && (
                    <div className="error-banner">
                      <strong>❌ Error:</strong> {selected.error}
                    </div>
                  )}
                  {selected.status === "done" && (
                    <div className="downloads-section">
                      <h3>⬇️ Download Outputs</h3>
                      <div className="downloads-grid">
                        {selected.formats.map((f) => (
                          <a
                            key={f}
                            className="download-card"
                            href={`${api}/jobs/${selected.id}/download?format=${f}`}
                            target="_blank"
                            rel="noreferrer"
                          >
                            <div className="dl-icon">{FORMAT_LABELS[f]?.icon || "📄"}</div>
                            <div className="dl-name">{FORMAT_LABELS[f]?.label || f}</div>
                            <div className="dl-action">Download →</div>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                  {selected.status === "done" && (
                    <div className="actions-section">
                      <div className="action-group">
                        <h3>🔄 Regenerate Notes (different category)</h3>
                        <div className="action-row">
                          <select value={regenCategory} onChange={(e) => setRegenCategory(e.target.value)}>
                            <option value="interview">Interview Prep</option>
                            <option value="exam">Exam Prep</option>
                            <option value="understanding">Deep Understanding</option>
                          </select>
                          <button className="action-btn" onClick={regenerate}>Regenerate</button>
                        </div>
                        <small>Reuses the stored transcript — ingestion is skipped.</small>
                      </div>
                      <div className="action-group">
                        <h3>➕ Render Additional Formats</h3>
                        <div className="action-row">
                          <div className="multi-check">
                            {Object.entries(FORMAT_LABELS).map(([key, info]) => (
                              <label key={key} className={`mc-option ${newFormats.includes(key) ? "on" : ""}`}>
                                <input
                                  type="checkbox"
                                  checked={newFormats.includes(key)}
                                  onChange={(e) => {
                                    if (e.target.checked) setNewFormats([...newFormats, key]);
                                    else setNewFormats(newFormats.filter((x) => x !== key));
                                  }}
                                />
                                <span>{info.icon} {info.label}</span>
                              </label>
                            ))}
                          </div>
                          <button className="action-btn" onClick={addFormat} disabled={newFormats.length === 0}>
                            Render Formats
                          </button>
                        </div>
                        <small>Reuses the stored canonical JSON — generation is skipped, no LLM call.</small>
                      </div>
                    </div>
                  )}
                </div>
                {notes && <Notes notes={notes} />}
              </>
            )}
          </section>
        )}
      </main>

      <footer className="app-footer">
        <p>Cortex · Pipeline: Ingestion → Generation → Formatting · {Object.keys(CATEGORY_LABELS).length} categories · {Object.keys(FORMAT_LABELS).length} formats</p>
      </footer>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
