import { useEffect, useMemo, useState } from "react";
import {
  jobInsights,
  loadExampleProfile,
  logOutreachRemote,
  mapJob,
  parseJob,
  recruiters,
  saveApplicationRemote,
  tailor,
  type Contact,
  type Profile,
  type RoleInsights,
  type TailorResult,
} from "./api";
import type { SeedJob } from "./Intake";
import {
  loadApplications,
  storeProfile,
  upsertApplicationBundle,
  upsertOutreach,
  type Application,
} from "./store";

type Tab = "markdown" | "latex" | "message";

type Props = {
  profile: Profile | null;
  profileLabel: string;
  seedApp?: Application | null;
  seedJob?: SeedJob | null;
  onProfile: (p: Profile, label: string) => void;
  onIntake: () => void;
  onSaved: () => void;
  onHome: () => void;
};

function downloadText(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function Craft({
  profile,
  profileLabel,
  seedApp,
  seedJob,
  onProfile,
  onIntake,
  onSaved,
  onHome,
}: Props) {
  const [jobUrl, setJobUrl] = useState(seedJob?.url || "");
  const [jobPaste, setJobPaste] = useState(
    seedJob?.description || seedApp?.job_description || "",
  );
  const [showPaste, setShowPaste] = useState(
    Boolean(seedJob?.description || seedApp?.job_description),
  );
  const [showRecruiters, setShowRecruiters] = useState(false);
  const [title, setTitle] = useState(seedJob?.title || seedApp?.title || "");
  const [company, setCompany] = useState(
    seedJob?.company || seedApp?.company || "",
  );
  const [locale, setLocale] = useState(seedApp?.locale || "en");
  const [insights, setInsights] = useState<RoleInsights | null>(
    seedJob?.insights || null,
  );
  const [mapMeta, setMapMeta] = useState("");
  const [contactsPaste, setContactsPaste] = useState("");
  const [result, setResult] = useState<TailorResult | null>(
    seedJob?.pack || null,
  );
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [contactsNote, setContactsNote] = useState("");
  const [tab, setTab] = useState<Tab>("markdown");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState(
    seedJob?.pack
      ? `Tailored · ${seedJob.title} at ${seedJob.company}`
      : seedJob
        ? `Job ready · ${seedJob.title} — generate when you want`
        : "",
  );
  const [savePulse, setSavePulse] = useState(false);

  useEffect(() => {
    if (!seedApp) return;
    setJobPaste(seedApp.job_description || "");
    setTitle(seedApp.title || "");
    setCompany(seedApp.company || "");
    setLocale(seedApp.locale || "en");
    setShowPaste(!!seedApp.job_description);
    setStatus(`Opened ${seedApp.company || seedApp.title} from pipeline`);
  }, [seedApp]);

  useEffect(() => {
    if (!seedJob) return;
    setTitle(seedJob.title);
    setCompany(seedJob.company);
    setJobPaste(seedJob.description);
    setJobUrl(seedJob.url || "");
    setShowPaste(true);
    if (seedJob.insights) setInsights(seedJob.insights);
    if (seedJob.pack) {
      setResult(seedJob.pack);
      setTab("message");
      setStatus(
        seedJob.saved
          ? `Saved · company message ready for ${seedJob.company}`
          : `Tailored · ${seedJob.title}`,
      );
    } else {
      setStatus(`Job ready · ${seedJob.title} — generate when you want`);
    }
  }, [seedJob]);

  const output = useMemo(() => {
    if (!result) return "";
    if (tab === "markdown") return result.markdown;
    if (tab === "latex") return result.latex;
    return result.company_message;
  }, [result, tab]);

  function applyMappedJob(
    job: {
      title: string;
      company: string;
      description: string;
      locale_hint: string | null;
    },
    nextInsights: RoleInsights,
    metaNote: string,
  ) {
    setTitle(job.title);
    setCompany(job.company);
    setJobPaste(job.description);
    if (job.locale_hint) setLocale(job.locale_hint);
    setInsights(nextInsights);
    setMapMeta(metaNote);
    setResult(null);
    setStatus(`Mapped · angle ${nextInsights.angle}`);
  }

  async function onMapJob(useMock: boolean) {
    setError("");
    if (!jobUrl.trim() && !useMock) {
      setError("Paste a LinkedIn job URL, or use a sample JD.");
      return;
    }
    setBusy(true);
    try {
      const data = await mapJob({
        url:
          jobUrl.trim() ||
          "https://www.linkedin.com/jobs/view/career-fit-mock",
        profile,
        mock: useMock ? true : null,
        locale,
      });
      applyMappedJob(
        data.job,
        data.insights,
        data.meta.mock
          ? "Sample JD (session skipped)"
          : `Session · ${data.meta.source}`,
      );
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      setShowPaste(true);
      setStatus("Session map failed — paste JD below.");
    } finally {
      setBusy(false);
    }
  }

  async function onParseJob() {
    setError("");
    setBusy(true);
    try {
      const parsed = await parseJob(jobPaste, "paste");
      const data = await jobInsights({
        raw: parsed.description,
        title: parsed.title,
        company: parsed.company,
        profile,
        locale: parsed.locale_hint || locale,
        source: "paste",
      });
      applyMappedJob(
        {
          title: data.job.title,
          company: data.job.company,
          description: data.job.description,
          locale_hint: parsed.locale_hint,
        },
        data.insights,
        "Paste fallback",
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onGenerate() {
    setError("");
    if (!title.trim() && !jobPaste.trim()) {
      setError("Pick or paste a job first, then generate.");
      return;
    }
    setBusy(true);
    try {
      const data = await tailor({
        profile,
        job: {
          title,
          company,
          description: jobPaste,
          locale,
          raw_paste: jobPaste,
        },
        angle: insights?.angle,
      });
      setResult(data);
      setTab("markdown");
      setStatus(`Angle: ${data.angle}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onSavePipeline() {
    if (!result && !title) return;
    setError("");
    setBusy(true);
    try {
      const bundle = await saveApplicationRemote({
        title,
        company,
        angle: result?.angle || insights?.angle || "",
        locale: result?.locale || locale,
        job_description: jobPaste,
        markdown: result?.markdown || "",
        latex: result?.latex || "",
        company_message: result?.company_message || "",
        summary: result?.summary || "",
        proof: result?.proof || "",
      });
      upsertApplicationBundle(bundle.application, bundle.artifact);
      setSavePulse(true);
      setStatus(
        `Saved · ${bundle.application.company || bundle.application.title}`,
      );
      setTimeout(() => setSavePulse(false), 900);
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onRecruiters() {
    setError("");
    setBusy(true);
    try {
      const data = await recruiters({
        profile,
        job: { title, company, description: jobPaste, locale },
        contacts_text: contactsPaste,
        angle: result?.angle || insights?.angle,
        locale,
      });
      setContacts(data.contacts);
      setContactsNote(data.note);
      setStatus(`${data.contacts.length} contact draft(s)`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onLogContact(c: Contact) {
    setError("");
    try {
      const res = await logOutreachRemote({
        contact: c,
        applications: loadApplications(),
        sent: true,
      });
      upsertOutreach(res.outreach);
      setStatus(`Logged outreach to ${c.name}`);
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className={`craft view-enter ${savePulse ? "saved-pulse" : ""}`}>
      <div className="grid two">
        <section className="panel">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h2>Craft</h2>
            <button type="button" className="btn secondary" onClick={onHome}>
              Home
            </button>
          </div>

          <div className="field">
            <label>Profile</label>
            <p className="hint">{profileLabel}</p>
            <div className="row">
              <button type="button" className="btn secondary" onClick={onIntake}>
                Start / jobs
              </button>
              <button
                type="button"
                className="btn secondary"
                onClick={() =>
                  loadExampleProfile().then((p: Profile) => {
                    storeProfile(p);
                    onProfile(p, "Example profile loaded");
                  })
                }
              >
                Use example
              </button>
            </div>
          </div>

          <div className="field">
            <label>Job link</label>
            <p className="hint">
              Prefer picking a job on Start. Here you can map a jobs/view URL or
              paste a JD.
            </p>
            <input
              type="url"
              value={jobUrl}
              onChange={(e) => setJobUrl(e.target.value)}
              placeholder="https://www.linkedin.com/jobs/view/…"
            />
            <div className="row" style={{ marginTop: "0.55rem" }}>
              <button
                type="button"
                className="btn"
                disabled={
                  busy || !jobUrl.trim() || jobUrl.includes("/jobs/search")
                }
                onClick={() => onMapJob(false)}
              >
                {busy ? "Mapping…" : "Map role"}
              </button>
              <button
                type="button"
                className="btn secondary"
                disabled={busy}
                onClick={() => onMapJob(true)}
              >
                Sample JD
              </button>
              <button
                type="button"
                className="btn ghost"
                disabled={busy}
                onClick={() => setShowPaste((v) => !v)}
              >
                {showPaste ? "Hide paste" : "Paste JD"}
              </button>
            </div>
            {mapMeta && <p className="hint">{mapMeta}</p>}
          </div>

          {showPaste && (
            <div className="field">
              <label>Job description</label>
              <textarea
                className="tall"
                value={jobPaste}
                onChange={(e) => setJobPaste(e.target.value)}
                placeholder="Paste the full job description here…"
              />
              <div className="row">
                <button
                  type="button"
                  className="btn secondary"
                  disabled={busy || !jobPaste.trim()}
                  onClick={onParseJob}
                >
                  Extract + insights
                </button>
              </div>
            </div>
          )}

          {insights && (
            <div className="insights-panel">
              <h3>Role insights</h3>
              <p className="angle">
                angle · {insights.angle}
                <span className="hint">
                  {" "}
                  ({insights.angle_score.toFixed(2)}) — {insights.angle_rationale}
                </span>
              </p>
              <ul>
                {insights.bullets.map((b) => (
                  <li key={b}>{b}</li>
                ))}
              </ul>
              {insights.gaps.length > 0 && (
                <>
                  <p className="hint">Real facts only — gaps to fill later:</p>
                  <ul className="gaps">
                    {insights.gaps.map((g) => (
                      <li key={g}>{g}</li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}

          <div className="field">
            <label>Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div className="field">
            <label>Company</label>
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
            />
          </div>
          <div className="field">
            <label>Locale</label>
            <select value={locale} onChange={(e) => setLocale(e.target.value)}>
              <option value="en">English</option>
              <option value="pt">Português</option>
            </select>
          </div>

          <div className="row">
            <button
              type="button"
              className="btn"
              disabled={busy || !profile || (!title && !jobPaste)}
              onClick={onGenerate}
            >
              {busy ? "Working…" : "Generate tailored resume"}
            </button>
            {(result || insights) && (
              <span className="angle">
                angle · {result?.angle || insights?.angle}
              </span>
            )}
          </div>

          {(result || title) && !seedJob?.saved && (
            <div className="row" style={{ marginTop: "0.75rem" }}>
              <button
                type="button"
                className="btn"
                disabled={busy}
                onClick={onSavePipeline}
              >
                Save to pipeline
              </button>
              <span className="hint">Keeps this role in Home.</span>
            </div>
          )}

          {result && seedJob?.saved && (
            <div className="notice" style={{ marginTop: "0.75rem" }}>
              <p style={{ marginBottom: "0.65rem" }}>
                Pack saved. Copy the company message and send it yourself — then
                check Home for the next move.
              </p>
              <div className="row">
                <button
                  type="button"
                  className="btn"
                  onClick={() => {
                    setTab("message");
                    void navigator.clipboard.writeText(
                      result.company_message || "",
                    );
                    setStatus("Company message copied — send it to a human.");
                  }}
                >
                  Copy message
                </button>
                <button type="button" className="btn secondary" onClick={onHome}>
                  Home
                </button>
              </div>
            </div>
          )}

          {result && (
            <div className="field" style={{ marginTop: "1.25rem" }}>
              <button
                type="button"
                className="btn ghost"
                onClick={() => setShowRecruiters((v) => !v)}
              >
                {showRecruiters
                  ? "Hide recruiter drafts"
                  : "Optional: paste recruiters"}
              </button>
              {showRecruiters && (
                <>
                  <p className="hint">
                    Paste name, title, About. You send — we draft and track.
                  </p>
                  <textarea
                    className="tall"
                    value={contactsPaste}
                    onChange={(e) => setContactsPaste(e.target.value)}
                    placeholder={`Jane Doe\nTechnical Recruiter | Acme\nAbout: jane@acme.com`}
                  />
                  <button
                    type="button"
                    className="btn ghost"
                    disabled={
                      busy || !contactsPaste.trim() || (!title && !jobPaste)
                    }
                    onClick={onRecruiters}
                  >
                    Rank contacts + draft messages
                  </button>
                </>
              )}
            </div>
          )}

          {error && <p className="status error">{error}</p>}
          {status && !error && <p className="status ok">{status}</p>}
        </section>

        <section className="panel">
          <h2>Outputs</h2>
          {!result && (
            <p className="hint">
              After you pick a job on Start (or map one here), generate Markdown /
              LaTeX / company message.
            </p>
          )}
          {result && (
            <>
              <div className="tabs">
                {(
                  [
                    ["message", "Company msg"],
                    ["markdown", "Resume MD"],
                    ["latex", "Resume LaTeX"],
                  ] as const
                ).map(([id, label]) => (
                  <button
                    key={id}
                    type="button"
                    className={`tab ${tab === id ? "on" : ""}`}
                    onClick={() => setTab(id)}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <div className="row" style={{ marginBottom: "0.65rem" }}>
                <button
                  type="button"
                  className="btn"
                  onClick={() => {
                    void navigator.clipboard.writeText(output);
                    setStatus(
                      tab === "message"
                        ? "Company message copied — send it yourself."
                        : "Copied.",
                    );
                  }}
                >
                  {tab === "message" ? "Copy message" : "Copy"}
                </button>
                <button
                  type="button"
                  className="btn secondary"
                  onClick={() =>
                    downloadText(
                      tab === "latex"
                        ? `${company || "resume"}.tex`
                        : tab === "message"
                          ? `${company || "message"}-outreach.txt`
                          : `${company || "resume"}.md`,
                      output,
                    )
                  }
                >
                  Download
                </button>
                {seedJob?.saved && (
                  <button
                    type="button"
                    className="btn secondary"
                    onClick={onHome}
                  >
                    Home
                  </button>
                )}
              </div>
              <pre className="output">{output}</pre>
            </>
          )}

          {contacts.length > 0 && (
            <div style={{ marginTop: "1.25rem" }}>
              <h2>Recruiter drafts</h2>
              {contactsNote && <p className="hint">{contactsNote}</p>}
              {contacts.map((c) => (
                <article className="contact" key={`${c.name}-${c.title}`}>
                  <header>
                    <h3>{c.name}</h3>
                    <span className="score">{Math.round(c.score * 100)}% fit</span>
                  </header>
                  <p className="meta">
                    {c.title || "No title"}
                    {c.email ? ` · ${c.email}` : " · DM (no email found)"}
                  </p>
                  <pre className="output">{c.draft_message}</pre>
                  <div className="row" style={{ marginTop: "0.5rem" }}>
                    <button
                      type="button"
                      className="btn secondary"
                      onClick={() =>
                        navigator.clipboard.writeText(c.draft_message)
                      }
                    >
                      Copy message
                    </button>
                    <button
                      type="button"
                      className="btn"
                      onClick={() => onLogContact(c)}
                    >
                      Log as sent
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
