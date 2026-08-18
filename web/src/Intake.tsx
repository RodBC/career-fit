import { useMemo, useState } from "react";
import {
  loadExampleProfile,
  storeProfile,
  submitIntake,
  uploadProfileYaml,
  type IntakePayload,
  type Profile,
} from "./api";

type Step = 0 | 1 | 2 | 3 | 4;

const STEPS = ["You", "How you work", "Targets", "Resume", "Review"] as const;

type Props = {
  onComplete: (profile: Profile, label: string) => void;
  onCancel?: () => void;
  initial?: Profile | null;
};

function asLines(value: unknown): string {
  if (Array.isArray(value)) return value.map(String).join("\n");
  if (typeof value === "string") return value;
  return "";
}

function fromProfile(p: Profile | null | undefined): IntakePayload {
  const identity = (p?.identity as Record<string, unknown> | undefined) || {};
  const tutoring = (p?.career_tutoring as Record<string, unknown> | undefined) || {};
  const targets = (p?.targets as Record<string, unknown> | undefined) || {};
  const langs = identity.languages;
  return {
    identity: {
      name: String(identity.name || ""),
      email: String(identity.email || ""),
      city: String(identity.city || ""),
      phone: String(identity.phone || ""),
      linkedin: String(identity.linkedin || ""),
      languages: Array.isArray(langs) ? langs.join(", ") : String(langs || ""),
    },
    career_tutoring: {
      enjoyed_most: asLines(tutoring.enjoyed_most),
      positive_differentials: asLines(tutoring.positive_differentials),
      improvement_areas: asLines(tutoring.improvement_areas),
      technical_knowledge: asLines(tutoring.technical_knowledge),
      networking_notes: asLines(tutoring.networking_notes),
      hates_doing: asLines(tutoring.hates_doing),
      challenges_overcome: asLines(tutoring.challenges_overcome),
    },
    targets: {
      roles_wanted: asLines(targets.roles_wanted),
      locales: Array.isArray(targets.locales)
        ? (targets.locales as string[])
        : ["en"],
      remote: Boolean(targets.remote ?? true),
    },
    resume_text: "",
    base_profile: p || null,
  };
}

export default function Intake({ onComplete, onCancel, initial }: Props) {
  const [step, setStep] = useState<Step>(0);
  const [form, setForm] = useState<IntakePayload>(() => fromProfile(initial));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [warnings, setWarnings] = useState<string[]>([]);
  const [previewNote, setPreviewNote] = useState("");

  const canNext = useMemo(() => {
    if (step === 0) {
      return Boolean(form.identity.name.trim() && form.identity.email.trim());
    }
    return true;
  }, [step, form.identity.name, form.identity.email]);

  function patchIdentity(partial: Partial<IntakePayload["identity"]>) {
    setForm((f) => ({ ...f, identity: { ...f.identity, ...partial } }));
  }
  function patchTutoring(partial: Partial<IntakePayload["career_tutoring"]>) {
    setForm((f) => ({
      ...f,
      career_tutoring: { ...f.career_tutoring, ...partial },
    }));
  }
  function patchTargets(partial: Partial<IntakePayload["targets"]>) {
    setForm((f) => ({ ...f, targets: { ...f.targets, ...partial } }));
  }

  async function onResumeFile(file: File | null) {
    if (!file) return;
    setError("");
    const name = file.name.toLowerCase();
    try {
      if (name.endsWith(".yaml") || name.endsWith(".yml") || name.endsWith(".json")) {
        const profile = await uploadProfileYaml(file);
        storeProfile(profile);
        onComplete(profile, `Loaded YAML: ${file.name}`);
        return;
      }
      if (name.endsWith(".pdf")) {
        setError(
          "PDF parse is not enabled yet — paste text, or upload .md / .txt / .tex / .yaml.",
        );
        return;
      }
      const text = await file.text();
      setForm((f) => ({ ...f, resume_text: text }));
      setPreviewNote(`Loaded resume file: ${file.name}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function finish() {
    setError("");
    setBusy(true);
    try {
      const result = await submitIntake({
        ...form,
        base_profile: form.base_profile,
      });
      storeProfile(result.profile);
      setWarnings(result.warnings || []);
      const name =
        (result.profile.identity as { name?: string } | undefined)?.name ||
        form.identity.name;
      onComplete(
        result.profile,
        `Intake saved: ${name}` +
          (result.parsed_roles
            ? ` · ${result.parsed_roles} role(s)`
            : " · no roles parsed yet"),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function useExample() {
    setBusy(true);
    setError("");
    try {
      const p = await loadExampleProfile();
      storeProfile(p);
      onComplete(p, "Example profile loaded");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel intake">
      <div className="intake-head">
        <div>
          <h2>Guided intake</h2>
          <p className="hint">
            Dump who you are and your current resume. We structure it once —
            then tailor jobs without inventing facts.
          </p>
        </div>
        <div className="intake-steps" aria-label="Intake steps">
          {STEPS.map((label, i) => (
            <button
              key={label}
              type="button"
              className={`intake-step ${step === i ? "on" : ""} ${step > i ? "done" : ""}`}
              onClick={() => setStep(i as Step)}
            >
              {i + 1}. {label}
            </button>
          ))}
        </div>
      </div>

      {step === 0 && (
        <div className="intake-body">
          <div className="field">
            <label htmlFor="name">Name *</label>
            <input
              id="name"
              type="text"
              value={form.identity.name}
              onChange={(e) => patchIdentity({ name: e.target.value })}
              placeholder="Alex Rivera"
              autoComplete="name"
            />
          </div>
          <div className="field">
            <label htmlFor="email">Email *</label>
            <input
              id="email"
              type="text"
              value={form.identity.email}
              onChange={(e) => patchIdentity({ email: e.target.value })}
              placeholder="you@example.com"
              autoComplete="email"
            />
          </div>
          <div className="grid two-tight">
            <div className="field">
              <label htmlFor="city">City</label>
              <input
                id="city"
                type="text"
                value={form.identity.city || ""}
                onChange={(e) => patchIdentity({ city: e.target.value })}
              />
            </div>
            <div className="field">
              <label htmlFor="phone">Phone</label>
              <input
                id="phone"
                type="text"
                value={form.identity.phone || ""}
                onChange={(e) => patchIdentity({ phone: e.target.value })}
              />
            </div>
          </div>
          <div className="field">
            <label htmlFor="linkedin">LinkedIn (public URL or handle)</label>
            <input
              id="linkedin"
              type="text"
              value={form.identity.linkedin || ""}
              onChange={(e) => patchIdentity({ linkedin: e.target.value })}
              placeholder="linkedin.com/in/you"
            />
          </div>
          <div className="field">
            <label htmlFor="languages">Languages</label>
            <p className="hint">Comma-separated</p>
            <input
              id="languages"
              type="text"
              value={form.identity.languages || ""}
              onChange={(e) => patchIdentity({ languages: e.target.value })}
              placeholder="English (fluent), Portuguese (fluent)"
            />
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="intake-body">
          <p className="hint" style={{ marginBottom: "0.75rem" }}>
            One idea per line. This feeds fit briefs and starter summaries — not
            invented CV bullets.
          </p>
          {(
            [
              ["enjoyed_most", "What you enjoy most"],
              ["positive_differentials", "Positive differentials"],
              ["technical_knowledge", "Technical knowledge"],
              ["challenges_overcome", "Challenges overcome"],
              ["hates_doing", "What you hate doing"],
              ["improvement_areas", "Improvement areas"],
              ["networking_notes", "Networking notes"],
            ] as const
          ).map(([key, label]) => (
            <div className="field" key={key}>
              <label htmlFor={key}>{label}</label>
              <textarea
                id={key}
                value={form.career_tutoring[key] || ""}
                onChange={(e) => patchTutoring({ [key]: e.target.value })}
                placeholder="One line per item…"
              />
            </div>
          ))}
        </div>
      )}

      {step === 2 && (
        <div className="intake-body">
          <div className="field">
            <label htmlFor="roles">Roles you want</label>
            <p className="hint">One per line</p>
            <textarea
              id="roles"
              value={form.targets.roles_wanted || ""}
              onChange={(e) => patchTargets({ roles_wanted: e.target.value })}
              placeholder={"GTM Engineer\nBackend / API Engineer"}
            />
          </div>
          <div className="field">
            <label>Locales</label>
            <div className="row">
              {(["en", "pt"] as const).map((loc) => {
                const on = (form.targets.locales || []).includes(loc);
                return (
                  <label key={loc} className="check">
                    <input
                      type="checkbox"
                      checked={on}
                      onChange={() => {
                        const cur = new Set(form.targets.locales || []);
                        if (on) cur.delete(loc);
                        else cur.add(loc);
                        const next = [...cur];
                        patchTargets({ locales: next.length ? next : ["en"] });
                      }}
                    />
                    {loc === "en" ? "English" : "Português"}
                  </label>
                );
              })}
              <label className="check">
                <input
                  type="checkbox"
                  checked={Boolean(form.targets.remote)}
                  onChange={(e) => patchTargets({ remote: e.target.checked })}
                />
                Open to remote
              </label>
            </div>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="intake-body">
          <div className="field">
            <label htmlFor="resume">Resume paste</label>
            <p className="hint">
              Prefer sections titled Experience / Projects / Skills / Education
              with <code>- bullet</code> lines. We parse rules-first — we do not
              invent employers. PDF not supported yet.
            </p>
            <textarea
              id="resume"
              className="tall"
              value={form.resume_text || ""}
              onChange={(e) =>
                setForm((f) => ({ ...f, resume_text: e.target.value }))
              }
              placeholder={`Experience\nSoftware Engineer at Acme — 2022 - Present\n- Shipped API integrations used by partners.\n\nProjects\nPipeline dashboard\n- Built daily health checks for failed jobs.\n\nSkills\nPython, FastAPI, SQL, React`}
            />
          </div>
          <div className="field">
            <label>Or upload text / YAML</label>
            <input
              type="file"
              accept=".md,.txt,.tex,.yaml,.yml,.json,.pdf"
              onChange={(e) => onResumeFile(e.target.files?.[0] ?? null)}
            />
            {previewNote && <p className="status ok">{previewNote}</p>}
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="intake-body">
          <ul className="review-list">
            <li>
              <strong>{form.identity.name || "—"}</strong> ·{" "}
              {form.identity.email || "no email"}
            </li>
            <li>
              Targets:{" "}
              {(form.targets.roles_wanted || "")
                .split("\n")
                .filter(Boolean)
                .slice(0, 3)
                .join(" · ") || "not set"}
            </li>
            <li>
              Resume paste:{" "}
              {form.resume_text?.trim()
                ? `${form.resume_text.trim().split(/\s+/).length} words`
                : "none (you can still tailor with tutoring + later YAML)"}
            </li>
          </ul>
          {warnings.length > 0 && (
            <div className="notice">
              {warnings.map((w) => (
                <div key={w}>{w}</div>
              ))}
            </div>
          )}
          <p className="hint">
            Saving builds a profile with the same facts on every angle until you
            tag per-angle bullets. Advanced users can still upload a full YAML
            anytime.
          </p>
        </div>
      )}

      {error && <p className="status error">{error}</p>}

      <div className="row intake-actions">
        {onCancel && (
          <button type="button" className="btn secondary" onClick={onCancel}>
            Back to workspace
          </button>
        )}
        <button
          type="button"
          className="btn secondary"
          disabled={busy}
          onClick={useExample}
        >
          Use example profile
        </button>
        {step > 0 && (
          <button
            type="button"
            className="btn secondary"
            onClick={() => setStep((s) => (s - 1) as Step)}
          >
            Back
          </button>
        )}
        {step < 4 ? (
          <button
            type="button"
            className="btn"
            disabled={!canNext}
            onClick={() => setStep((s) => (s + 1) as Step)}
          >
            Continue
          </button>
        ) : (
          <button
            type="button"
            className="btn"
            disabled={busy || !canNext}
            onClick={finish}
          >
            {busy ? "Saving…" : "Save intake & start tailoring"}
          </button>
        )}
      </div>
    </section>
  );
}
