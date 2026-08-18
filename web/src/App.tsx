import { useEffect, useMemo, useState } from "react";
import {
  loadExampleProfile,
  parseJob,
  recruiters,
  tailor,
  uploadProfileYaml,
  type Contact,
  type Profile,
  type TailorResult,
} from "./api";

type Tab = "markdown" | "latex" | "message";

function downloadText(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [profileLabel, setProfileLabel] = useState("No profile loaded");
  const [jobPaste, setJobPaste] = useState("");
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [locale, setLocale] = useState("en");
  const [contactsPaste, setContactsPaste] = useState("");
  const [result, setResult] = useState<TailorResult | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [contactsNote, setContactsNote] = useState("");
  const [tab, setTab] = useState<Tab>("markdown");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    loadExampleProfile()
      .then((p) => {
        setProfile(p);
        const name = (p.identity as { name?: string } | undefined)?.name;
        setProfileLabel(name ? `Example profile: ${name}` : "Example profile loaded");
      })
      .catch(() => {
        setStatus("API offline — start with: career-fit serve");
      });
  }, []);

  const output = useMemo(() => {
    if (!result) return "";
    if (tab === "markdown") return result.markdown;
    if (tab === "latex") return result.latex;
    return result.company_message;
  }, [result, tab]);

  async function onUpload(file: File | null) {
    if (!file) return;
    setError("");
    try {
      const p = await uploadProfileYaml(file);
      setProfile(p);
      const name = (p.identity as { name?: string } | undefined)?.name;
      setProfileLabel(name ? `Loaded: ${name}` : `Loaded: ${file.name}`);
      setStatus("Profile uploaded");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

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
      setStatus(`Angle: ${data.angle}`);
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

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <h1>Career Fit</h1>
          <p>
            Upload your profile, paste a job, get a tailored resume and short
            outreach — then paste recruiter profiles to draft DMs/emails. You
            send manually.
          </p>
        </div>
        <div className="steps">
          <span className={`step-pill ${profile ? "active" : ""}`}>1 Profile</span>
          <span className={`step-pill ${title || jobPaste ? "active" : ""}`}>2 Job</span>
          <span className={`step-pill ${result ? "active" : ""}`}>3 Resume</span>
          <span className={`step-pill ${contacts.length ? "active" : ""}`}>4 Recruiters</span>
        </div>
      </header>

      <div className="notice">
        LinkedIn/Gupy/inHire: paste what you see. This app does not scrape
        LinkedIn. Automated scraping breaks ToS, accounts, and the product —
        the moat is tailored CV quality + credible messages.
      </div>

      <div className="grid two">
        <section className="panel">
          <h2>Inputs</h2>

          <div className="field">
            <label>Profile (YAML)</label>
            <p className="hint">{profileLabel}</p>
            <div className="row">
              <input
                type="file"
                accept=".yaml,.yml,.json"
                onChange={(e) => onUpload(e.target.files?.[0] ?? null)}
              />
              <button
                type="button"
                className="btn secondary"
                onClick={() =>
                  loadExampleProfile().then((p) => {
                    setProfile(p);
                    setProfileLabel("Example profile reloaded");
                  })
                }
              >
                Use example
              </button>
            </div>
          </div>

          <div className="field">
            <label>Job paste (LinkedIn / Gupy / inHire / anywhere)</label>
            <p className="hint">
              Copy the posting text. Click Extract to fill title/company, then
              edit.
            </p>
            <textarea
              className="tall"
              value={jobPaste}
              onChange={(e) => setJobPaste(e.target.value)}
              placeholder="Paste the full job description here…"
            />
            <div className="row">
              <button type="button" className="btn secondary" disabled={busy || !jobPaste.trim()} onClick={onParseJob}>
                Extract fields
              </button>
            </div>
          </div>

          <div className="field">
            <label>Title</label>
            <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="field">
            <label>Company</label>
            <input type="text" value={company} onChange={(e) => setCompany(e.target.value)} />
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
            {result && (
              <span className="angle">angle · {result.angle}</span>
            )}
          </div>

          <div className="field" style={{ marginTop: "1.25rem" }}>
            <label>Recruiters / decision-makers (paste)</label>
            <p className="hint">
              From LinkedIn company people search: paste name, title, About
              (blank line between people). Or CSV with columns name,title,about,email,linkedin.
            </p>
            <textarea
              className="tall"
              value={contactsPaste}
              onChange={(e) => setContactsPaste(e.target.value)}
              placeholder={`Jane Doe\nTechnical Recruiter | Acme\nAbout: hiring for platform teams… jane@acme.com\n\nJohn Smith\nEngineering Manager · Acme`}
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
        </section>

        <section className="panel">
          <h2>Outputs</h2>
          {!result && (
            <p className="hint">Generate a resume to see Markdown, LaTeX, and a company message.</p>
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
                    {c.rationale ? ` · ${c.rationale}` : ""}
                  </p>
                  <pre className="output">{c.draft_message}</pre>
                  <div className="row" style={{ marginTop: "0.5rem" }}>
                    <button
                      type="button"
                      className="btn secondary"
                      onClick={() => navigator.clipboard.writeText(c.draft_message)}
                    >
                      Copy message
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

      <p className="footer-note">
        Run API: <code>career-fit serve</code> · Run UI:{" "}
        <code>cd web && npm run dev</code> · See{" "}
        <code>docs/ARCHITECTURE.md</code> for why scraping isn’t in the core.
      </p>
    </div>
  );
}
