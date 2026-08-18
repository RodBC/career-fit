import { useEffect, useMemo, useState } from "react";
import {
  fetchLimits,
  loadExampleProfile,
  logOutreachRemote,
  parseJob,
  recruiters,
  saveApplicationRemote,
  tailor,
  type Contact,
  type Profile,
  type TailorResult,
  type TrackerLimits,
} from "./api";
import {
  bumpTailorCount,
  loadApplications,
  loadUsage,
  markProRequested,
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
  onProfile,
  onIntake,
  onSaved,
  onHome,
}: Props) {
  const [jobPaste, setJobPaste] = useState(seedApp?.job_description || "");
  const [title, setTitle] = useState(seedApp?.title || "");
  const [company, setCompany] = useState(seedApp?.company || "");
  const [locale, setLocale] = useState(seedApp?.locale || "en");
  const [contactsPaste, setContactsPaste] = useState("");
  const [result, setResult] = useState<TailorResult | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [contactsNote, setContactsNote] = useState("");
  const [tab, setTab] = useState<Tab>("markdown");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [limits, setLimits] = useState<TrackerLimits | null>(null);
  const [savePulse, setSavePulse] = useState(false);
  const [usage, setUsage] = useState(loadUsage());

  useEffect(() => {
    fetchLimits()
      .then(setLimits)
      .catch(() =>
        setLimits({
          free_tailor_per_month: 3,
          free_application_cap: 5,
          pro_price_usd: 29,
          pro_blurb: "Pro unlocks unlimited craft + full pipeline.",
          stages: [],
        }),
      );
  }, []);

  useEffect(() => {
    if (!seedApp) return;
    setJobPaste(seedApp.job_description || "");
    setTitle(seedApp.title || "");
    setCompany(seedApp.company || "");
    setLocale(seedApp.locale || "en");
    setStatus(`Opened ${seedApp.company || seedApp.title} from pipeline`);
  }, [seedApp]);

  const output = useMemo(() => {
    if (!result) return "";
    if (tab === "markdown") return result.markdown;
    if (tab === "latex") return result.latex;
    return result.company_message;
  }, [result, tab]);

  const tailorBlocked =
    !!limits && usage.tailor_count >= limits.free_tailor_per_month;

  const appCapBlocked =
    !!limits && loadApplications().length >= limits.free_application_cap;

  async function onParseJob() {
    setError("");
    setBusy(true);
    try {
      const parsed = await parseJob(jobPaste, "paste");
      setTitle(parsed.title);
      setCompany(parsed.company);
      if (parsed.locale_hint) setLocale(parsed.locale_hint);
      setStatus("Job fields extracted — edit if needed, then Generate");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onGenerate() {
    setError("");
    if (tailorBlocked) {
      setError(
        `Free limit: ${limits?.free_tailor_per_month} tailored CVs / month. Request Pro to continue.`,
      );
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
      });
      setResult(data);
      setTab("markdown");
      setUsage(bumpTailorCount());
      setStatus(`Angle: ${data.angle}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onSavePipeline() {
    if (!result) return;
    setError("");
    if (appCapBlocked) {
      setError(
        `Free pipeline cap: ${limits?.free_application_cap} applications. Request Pro for full memory.`,
      );
      return;
    }
    setBusy(true);
    try {
      const bundle = await saveApplicationRemote({
        title,
        company,
        angle: result.angle,
        locale: result.locale,
        job_description: jobPaste,
        markdown: result.markdown,
        latex: result.latex,
        company_message: result.company_message,
        summary: result.summary,
        proof: result.proof,
      });
      upsertApplicationBundle(bundle.application, bundle.artifact);
      setSavePulse(true);
      setStatus(`Saved to pipeline · ${bundle.application.company || bundle.application.title}`);
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
        angle: result?.angle,
        locale,
      });
      setContacts(data.contacts);
      setContactsNote(data.note);
      setStatus(`${data.contacts.length} contact draft(s) · angle ${data.angle}`);
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

  function requestPro() {
    setUsage(markProRequested());
    setStatus(
      "Pro interest saved — thanks. Limits stay until billing ships; clear usage in localStorage to reset while dogfooding.",
    );
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
                Edit intake
              </button>
              <button
                type="button"
                className="btn secondary"
                onClick={() =>
                  loadExampleProfile().then((p) => {
                    storeProfile(p);
                    onProfile(p, "Example profile loaded");
                  })
                }
              >
                Use example
              </button>
            </div>
          </div>

          {(tailorBlocked || appCapBlocked) && (
            <div className="pro-panel warn">
              <p>
                {tailorBlocked
                  ? `Free tailor limit reached (${limits?.free_tailor_per_month}/mo).`
                  : `Free pipeline cap (${limits?.free_application_cap} roles).`}
              </p>
              <p className="hint">{limits?.pro_blurb}</p>
              <button type="button" className="btn" onClick={requestPro}>
                Request Pro (${limits?.pro_price_usd}/mo)
              </button>
            </div>
          )}

          <div className="field">
            <label>Job paste (LinkedIn / Gupy / inHire / anywhere)</label>
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
                Extract fields
              </button>
            </div>
          </div>

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
              disabled={busy || !profile || (!title && !jobPaste) || tailorBlocked}
              onClick={onGenerate}
            >
              {busy ? "Working…" : "Generate tailored resume"}
            </button>
            {result && <span className="angle">angle · {result.angle}</span>}
          </div>

          {result && (
            <div className="row" style={{ marginTop: "0.75rem" }}>
              <button
                type="button"
                className="btn"
                disabled={busy || appCapBlocked}
                onClick={onSavePipeline}
              >
                Save to pipeline
              </button>
              <span className="hint">Primary next step — don’t lose this pack.</span>
            </div>
          )}

          <div className="field" style={{ marginTop: "1.25rem" }}>
            <label>Recruiters / decision-makers (paste)</label>
            <p className="hint">
              Paste name, title, About. Then log who you actually message.
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
              disabled={busy || !contactsPaste.trim() || (!title && !jobPaste)}
              onClick={onRecruiters}
            >
              Rank contacts + draft messages
            </button>
          </div>

          {error && <p className="status error">{error}</p>}
          {status && !error && <p className="status ok">{status}</p>}
          <p className="hint">
            Free usage: {usage.tailor_count}/
            {limits?.free_tailor_per_month ?? 3} tailors this month
          </p>
        </section>

        <section className="panel">
          <h2>Outputs</h2>
          {!result && (
            <p className="hint">
              Generate a resume to see Markdown, LaTeX, and a company message.
            </p>
          )}
          {result && (
            <>
              <div className="tabs">
                {(
                  [
                    ["markdown", "Resume MD"],
                    ["latex", "Resume LaTeX"],
                    ["message", "Company msg"],
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
                <button
                  type="button"
                  className="btn secondary"
                  onClick={() => navigator.clipboard.writeText(output)}
                >
                  Copy
                </button>
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
                    {c.linkedin_url && (
                      <a href={c.linkedin_url} target="_blank" rel="noreferrer">
                        Open profile
                      </a>
                    )}
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
