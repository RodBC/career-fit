import { useMemo, useState } from "react";
import {
  clearLocalWorkspace,
  jobInsights,
  loadExampleProfile,
  mapJob,
  mapProfile,
  saveApplicationRemote,
  storeProfile,
  submitIntake,
  suggestOpenings,
  suggestRoles,
  tailor,
  uploadProfileYaml,
  type IntakePayload,
  type JobOpening,
  type Profile,
  type RoleInsights,
  type SuggestedRole,
  type TailorResult,
} from "./api";
import { upsertApplicationBundle } from "./store";

type Step = "link" | "roles" | "jobs" | "deepen";

export type SeedJob = {
  title: string;
  company: string;
  description: string;
  url?: string;
  insights?: RoleInsights | null;
  pack?: TailorResult | null;
  saved?: boolean;
};

export type JourneyCompleteOpts = {
  jobSearchUrl?: string;
  seedJob?: SeedJob | null;
};

type Props = {
  onComplete: (profile: Profile, label: string, opts?: JourneyCompleteOpts) => void;
  onCancel?: () => void;
  onCleared?: () => void;
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

export default function Intake({
  onComplete,
  onCancel,
  onCleared,
  initial,
}: Props) {
  const [step, setStep] = useState<Step>("link");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [form, setForm] = useState<IntakePayload>(() => fromProfile(null));
  const [mappedProfile, setMappedProfile] = useState<Profile | null>(null);
  const [headline, setHeadline] = useState("");
  const [mapMeta, setMapMeta] = useState("");
  const [roleCards, setRoleCards] = useState<SuggestedRole[]>([]);
  const [votes, setVotes] = useState<Record<string, "yes" | "no">>({});
  const [customRole, setCustomRole] = useState("");
  const [openings, setOpenings] = useState<JobOpening[]>([]);
  const [openingsNote, setOpeningsNote] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [selected, setSelected] = useState<JobOpening | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const canFinish = useMemo(
    () => Boolean(form.identity.name.trim()),
    [form.identity.name],
  );

  const yesRoles = useMemo(
    () => roleCards.filter((r) => votes[r.id] === "yes"),
    [roleCards, votes],
  );

  function patchTutoring(partial: Partial<IntakePayload["career_tutoring"]>) {
    setForm((f) => ({
      ...f,
      career_tutoring: { ...f.career_tutoring, ...partial },
    }));
  }

  function patchIdentity(partial: Partial<IntakePayload["identity"]>) {
    setForm((f) => ({ ...f, identity: { ...f.identity, ...partial } }));
  }

  function startFresh() {
    clearLocalWorkspace();
    setStep("link");
    setLinkedinUrl("");
    setForm(fromProfile(null));
    setMappedProfile(null);
    setHeadline("");
    setMapMeta("");
    setRoleCards([]);
    setVotes({});
    setCustomRole("");
    setOpenings([]);
    setOpeningsNote("");
    setJobUrl("");
    setSelected(null);
    setError("");
    onCleared?.();
  }

  function applyMapped(
    data: Awaited<ReturnType<typeof mapProfile>>,
    metaLine: string,
  ) {
    setMappedProfile(data.profile);
    setForm(fromProfile(data.profile));
    setHeadline(String(data.snapshot.headline || data.snapshot.name || ""));
    setMapMeta(metaLine);
    setRoleCards(data.suggested_roles || []);
    setVotes({});
    setError("");
    setStep("roles");
  }

  async function persistProfile() {
    const wanted =
      yesRoles.length > 0
        ? yesRoles.map((r) => r.title).join("\n")
        : form.targets.roles_wanted || "";
    const payload: IntakePayload = {
      ...form,
      targets: { ...form.targets, roles_wanted: wanted },
      base_profile: mappedProfile,
    };
    const result = await submitIntake(payload);
    storeProfile(result.profile);
    return result.profile;
  }

  /** One field only: LinkedIn URL → stub identity (no login, no form dump). */
  async function onContinueWithUrl() {
    setError("");
    if (!linkedinUrl.trim()) {
      setError("Paste your LinkedIn profile URL — that’s the only thing we need here.");
      return;
    }
    setBusy(true);
    try {
      const data = await mapProfile({
        url: linkedinUrl.trim(),
        stub: true,
      });
      let roles = data.suggested_roles || [];
      if (roles.length === 0) {
        const more = await suggestRoles({
          profile: data.profile,
          headline: String(data.snapshot.headline || data.snapshot.name || ""),
          limit: 5,
        });
        roles = more.roles;
      }
      applyMapped(
        { ...data, suggested_roles: roles },
        "From your LinkedIn URL only — no login. We don’t invent employers. Next: pick roles, then pick a job.",
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  function addCustomRole() {
    const title = customRole.trim();
    if (!title) return;
    const id = `custom-${Date.now()}`;
    setRoleCards((cards) => [
      ...cards,
      {
        id,
        title,
        kind: "custom",
        why: "You added this target title.",
        linkedin_url: "",
      },
    ]);
    setVotes((v) => ({ ...v, [id]: "yes" }));
    setCustomRole("");
  }

  async function goToJobs() {
    setError("");
    setBusy(true);
    try {
      const profile = await persistProfile();
      setMappedProfile(profile);
      setForm(fromProfile(profile));
      const titles =
        yesRoles.length > 0
          ? yesRoles.map((r) => r.title)
          : roleCards.slice(0, 2).map((r) => r.title);
      const searchTitles =
        titles.length > 0 ? titles : ["Software Engineer"];
      setSelected(null);
      setJobUrl("");
      setStep("jobs");

      // Discovery cards from role search links (open in their browser — not invented JDs)
      const browse: JobOpening[] = (
        yesRoles.length > 0 ? yesRoles : roleCards.slice(0, 3)
      ).map((r) => ({
        id: `browse-${r.id}`,
        title: r.title,
        company: "LinkedIn search",
        blurb: "Browse live openings in your browser, then paste a jobs/view URL below.",
        description: "",
        linkedin_url:
          r.linkedin_url ||
          `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(r.title)}`,
        sample: false,
      }));

      try {
        const data = await suggestOpenings({
          role_titles: searchTitles,
          location: String(
            (profile.identity as { city?: string } | undefined)?.city || "",
          ),
          limit: 6,
        });
        setOpenings(data.openings);
        setOpeningsNote(
          data.note ||
            "Pick a job below — we already pulled the posting. Or paste any job URL.",
        );
      } catch {
        setOpenings(browse);
        setOpeningsNote(
          "Open a search below in your browser, copy one job link, paste it here — one URL, we scrape the rest.",
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function useJobUrl() {
    setError("");
    if (!jobUrl.trim()) {
      setError("Paste a job URL — one link, we scrape title, company, and JD.");
      return;
    }
    setBusy(true);
    try {
      const data = await mapJob({
        url: jobUrl.trim(),
        profile: mappedProfile,
        mock: null,
      });
      if (!data.job.company?.trim()) {
        setError(
          "That URL didn’t yield a company — try a public careers / jobs/view link.",
        );
        return;
      }
      const opening: JobOpening = {
        id: "mapped-url",
        title: data.job.title || "Role",
        company: data.job.company,
        blurb: data.job.description.slice(0, 180),
        description: data.job.description,
        linkedin_url: jobUrl.trim(),
        sample: Boolean(data.meta.mock),
      };
      setSelected(opening);
      setOpenings((o) => [opening, ...o.filter((x) => x.id !== "mapped-url")]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function chooseOpening(o: JobOpening) {
    // Stay inside Career Fit UI — never open LinkedIn in another tab
    if (!o.description?.trim()) {
      setError(
        "That card has no JD yet — paste its jobs/view URL below (one shot).",
      );
      if (o.linkedin_url) {
        setJobUrl(o.linkedin_url);
      }
      return;
    }
    setSelected(o);
    setError("");
  }

  async function finishWithJob(mode: "tailor" | "save" | "craft") {
    if (!selected || !selected.description?.trim()) {
      setError("Pick a scraped job or paste a job URL first.");
      return;
    }
    if (!selected.company.trim()) {
      setError("That posting has no company — try another URL.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      const profile = await persistProfile();
      const name =
        (profile.identity as { name?: string } | undefined)?.name ||
        form.identity.name;

      const insightsData = await jobInsights({
        raw: selected.description,
        title: selected.title,
        company: selected.company,
        profile,
        source: "paste",
      });

      let pack: TailorResult | null = null;
      let saved = false;

      if (mode === "tailor") {
        pack = await tailor({
          profile,
          job: {
            title: selected.title,
            company: selected.company,
            description: selected.description,
            locale: "en",
            raw_paste: selected.description,
          },
          angle: insightsData.insights.angle,
        });
        const bundle = await saveApplicationRemote({
          title: selected.title,
          company: selected.company,
          angle: pack.angle,
          locale: pack.locale,
          job_description: selected.description,
          markdown: pack.markdown,
          latex: pack.latex,
          company_message: pack.company_message,
          summary: pack.summary,
          proof: pack.proof,
        });
        upsertApplicationBundle(bundle.application, bundle.artifact);
        saved = true;
      } else if (mode === "save") {
        const bundle = await saveApplicationRemote({
          title: selected.title,
          company: selected.company,
          angle: insightsData.insights.angle,
          locale: "en",
          job_description: selected.description,
          markdown: "",
          latex: "",
          company_message: "",
          summary: "",
          proof: "",
        });
        upsertApplicationBundle(bundle.application, bundle.artifact);
        saved = true;
      }

      onComplete(profile, `Ready · ${name}`, {
        jobSearchUrl: selected.linkedin_url,
        seedJob: {
          title: selected.title,
          company: selected.company,
          description: selected.description,
          url: selected.linkedin_url,
          insights: insightsData.insights,
          pack,
          saved,
        },
      });
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

  async function onResumeFile(file: File | null) {
    if (!file) return;
    setError("");
    const name = file.name.toLowerCase();
    try {
      if (
        name.endsWith(".yaml") ||
        name.endsWith(".yml") ||
        name.endsWith(".json")
      ) {
        const profile = await uploadProfileYaml(file);
        storeProfile(profile);
        setMappedProfile(profile);
        setForm(fromProfile(profile));
        setMapMeta(`Loaded ${file.name}`);
        const data = await suggestRoles({ profile, limit: 5 });
        setRoleCards(data.roles);
        setVotes({});
        setStep("roles");
        return;
      }
      const text = await file.text();
      setForm((f) => ({ ...f, resume_text: text }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  const stepTitle =
    step === "link"
      ? "Your LinkedIn URL"
      : step === "roles"
        ? "What kinds of roles?"
        : step === "jobs"
          ? "Jobs for you"
          : "Optional depth";

  const stepHint =
    step === "link"
      ? "One link. No login. No long form — we never invent employers."
      : step === "roles"
        ? "Tap yes/no, or type a title. Then we show openings."
        : step === "jobs"
          ? "Pick a card, or paste one job URL — we scrape the rest."
          : "Skip anytime — only if you want more depth later.";

  return (
    <section className="panel intake">
      <div className="intake-head">
        <div>
          <h2>{stepTitle}</h2>
          <p className="hint">{stepHint}</p>
        </div>
        <div className="intake-steps" aria-label="Start steps">
          {(
            [
              ["link", "1. Link"],
              ["roles", "2. Roles"],
              ["jobs", "3. Job"],
              ["deepen", "4. Optional"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              className={`intake-step ${step === id ? "on" : ""} ${
                (step === "roles" && id === "link") ||
                (step === "jobs" && (id === "link" || id === "roles")) ||
                (step === "deepen" && id !== "deepen")
                  ? "done"
                  : ""
              }`}
              onClick={() => {
                if (id === "link") setStep("link");
                if (id === "roles" && mappedProfile) setStep("roles");
                if (id === "jobs" && mappedProfile) setStep("jobs");
                if (id === "deepen" && mappedProfile) setStep("deepen");
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {step === "link" && (
        <div className="intake-body journey-hero">
          {(initial || mappedProfile) && (
            <div className="notice">
              There’s a saved profile in this browser.{" "}
              <button type="button" className="btn" onClick={startFresh}>
                Erase & start fresh
              </button>
            </div>
          )}
          <div className="field">
            <label htmlFor="li">LinkedIn profile URL</label>
            <input
              id="li"
              type="url"
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
              placeholder="https://www.linkedin.com/in/you"
              autoFocus
            />
            <p className="hint">
              We only use the URL (name from the slug). No password, no browser
              login.
            </p>
          </div>
          <div className="row">
            <button
              type="button"
              className="btn"
              disabled={busy || !linkedinUrl.trim()}
              onClick={onContinueWithUrl}
            >
              {busy ? "Continuing…" : "Continue"}
            </button>
          </div>
        </div>
      )}

      {step === "roles" && (
        <div className="intake-body">
          {mapMeta && <p className="status ok">{mapMeta}</p>}
          {headline ? (
            <p className="journey-headline">
              <span className="hint">Starting from · </span>
              {headline}
            </p>
          ) : null}
          <div className="field">
            <label htmlFor="custom-role">Add a target title</label>
            <div className="row">
              <input
                id="custom-role"
                type="text"
                value={customRole}
                onChange={(e) => setCustomRole(e.target.value)}
                placeholder="e.g. Data Engineer…"
              />
              <button
                type="button"
                className="btn secondary"
                disabled={!customRole.trim()}
                onClick={addCustomRole}
              >
                Add
              </button>
            </div>
          </div>
          <div className="role-cards">
            {roleCards.map((r) => {
              const vote = votes[r.id];
              return (
                <article
                  key={r.id}
                  className={`role-card ${vote === "yes" ? "yes" : ""} ${vote === "no" ? "no" : ""}`}
                >
                  <header>
                    <h3>{r.title}</h3>
                    <span className="hint">{r.kind.replace(/_/g, " ")}</span>
                  </header>
                  <p className="meta">{r.why}</p>
                  <div className="row" style={{ marginTop: "0.65rem" }}>
                    <button
                      type="button"
                      className={`btn ${vote === "yes" ? "" : "secondary"}`}
                      onClick={() =>
                        setVotes((v) => ({ ...v, [r.id]: "yes" }))
                      }
                    >
                      Yes
                    </button>
                    <button
                      type="button"
                      className={`btn ${vote === "no" ? "" : "ghost"}`}
                      onClick={() => setVotes((v) => ({ ...v, [r.id]: "no" }))}
                    >
                      No
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      )}

      {step === "jobs" && (
        <div className="intake-body">
          {openingsNote && <p className="hint">{openingsNote}</p>}
          <div className="role-cards">
            {openings.map((o) => {
              const hasJd = Boolean(o.description?.trim());
              return (
                <article
                  key={o.id}
                  className={`role-card ${selected?.id === o.id ? "yes" : ""}`}
                >
                  <header>
                    <h3>{o.title}</h3>
                    <span className="hint">
                      {hasJd ? o.company : "Browse openings"}
                    </span>
                  </header>
                  <p className="meta">
                    {hasJd ? (
                      <>
                        <strong>{o.company}</strong> — {o.blurb}
                      </>
                    ) : (
                      o.blurb
                    )}
                  </p>
                  <div className="row" style={{ marginTop: "0.65rem" }}>
                    <button
                      type="button"
                      className={`btn ${selected?.id === o.id ? "" : "secondary"}`}
                      disabled={busy}
                      onClick={() => chooseOpening(o)}
                    >
                      {hasJd
                        ? selected?.id === o.id
                          ? "Selected"
                          : "Choose this"
                        : "Open search →"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
          <div className="field" style={{ marginTop: "1.25rem" }}>
            <label htmlFor="job-url">Or paste a job URL</label>
            <div className="row">
              <input
                id="job-url"
                type="url"
                value={jobUrl}
                onChange={(e) => setJobUrl(e.target.value)}
                placeholder="https://www.linkedin.com/jobs/view/… or search?currentJobId=…"
              />
              <button
                type="button"
                className="btn"
                disabled={busy || !jobUrl.trim()}
                onClick={useJobUrl}
              >
                {busy ? "Scraping…" : "Use URL"}
              </button>
            </div>
            <p className="hint">
              One link only (jobs/view or search with a selected job) — we scrape
              title, company, and description.
            </p>
          </div>
          {selected && selected.description?.trim() && (
            <div className="notice" style={{ marginTop: "1rem" }}>
              <p style={{ marginBottom: "0.65rem" }}>
                Tailor for <strong>{selected.title}</strong> at{" "}
                <strong>{selected.company}</strong>?
              </p>
              <div className="row">
                <button
                  type="button"
                  className="btn"
                  disabled={busy}
                  onClick={() => finishWithJob("tailor")}
                >
                  {busy ? "Crafting…" : "Yes — tailor & save"}
                </button>
                <button
                  type="button"
                  className="btn secondary"
                  disabled={busy}
                  onClick={() => finishWithJob("save")}
                >
                  Save only
                </button>
                <button
                  type="button"
                  className="btn ghost"
                  disabled={busy}
                  onClick={() => finishWithJob("craft")}
                >
                  Open in Craft
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {step === "deepen" && (
        <div className="intake-body">
          <p className="hint">
            Optional only — skip unless you want a richer graph later.
          </p>
          <div className="field">
            <label htmlFor="name">Name</label>
            <input
              id="name"
              type="text"
              value={form.identity.name}
              onChange={(e) => patchIdentity({ name: e.target.value })}
            />
          </div>
          {(
            [
              ["enjoyed_most", "What you enjoy most"],
              ["hates_doing", "What you hate doing"],
            ] as const
          ).map(([key, label]) => (
            <div className="field" key={key}>
              <label htmlFor={key}>{label}</label>
              <textarea
                id={key}
                value={form.career_tutoring[key] || ""}
                onChange={(e) => patchTutoring({ [key]: e.target.value })}
                rows={2}
              />
            </div>
          ))}
          <div className="field">
            <label>Résumé / YAML (optional)</label>
            <input
              type="file"
              accept=".md,.txt,.tex,.yaml,.yml,.json"
              onChange={(e) => onResumeFile(e.target.files?.[0] ?? null)}
            />
          </div>
        </div>
      )}

      {error && <p className="status error">{error}</p>}

      <div className="row intake-actions">
        {onCancel && step !== "link" && (
          <button type="button" className="btn secondary" onClick={onCancel}>
            Back to workspace
          </button>
        )}
        <button
          type="button"
          className="btn ghost"
          disabled={busy}
          onClick={useExample}
        >
          Use example
        </button>
        {step === "roles" && (
          <>
            <button
              type="button"
              className="btn ghost"
              onClick={() => setStep("deepen")}
            >
              Optional depth
            </button>
            <button
              type="button"
              className="btn"
              disabled={busy || !canFinish}
              onClick={goToJobs}
            >
              {busy ? "Saving…" : "Find jobs →"}
            </button>
          </>
        )}
        {step === "jobs" && (
          <button
            type="button"
            className="btn secondary"
            onClick={() => setStep("roles")}
          >
            Back to roles
          </button>
        )}
        {step === "deepen" && (
          <>
            <button
              type="button"
              className="btn secondary"
              onClick={() => setStep("roles")}
            >
              Back
            </button>
            <button
              type="button"
              className="btn"
              disabled={busy || !canFinish}
              onClick={goToJobs}
            >
              {busy ? "Saving…" : "Find jobs →"}
            </button>
          </>
        )}
      </div>
    </section>
  );
}
