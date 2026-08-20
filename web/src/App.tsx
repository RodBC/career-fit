import { useEffect, useState } from "react";
import {
  clearLocalWorkspace,
  fetchLimits,
  loadExampleProfile,
  loadStoredProfile,
  type Profile,
} from "./api";
import Craft from "./Craft";
import Home from "./Home";
import Intake, { type SeedJob } from "./Intake";
import type { Application } from "./store";

type View = "home" | "intake" | "craft";

function profileName(p: Profile | null): string {
  return (p?.identity as { name?: string } | undefined)?.name || "";
}

export default function App() {
  const [view, setView] = useState<View>("intake");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [profileLabel, setProfileLabel] = useState("No profile loaded");
  const [seedApp, setSeedApp] = useState<Application | null>(null);
  const [seedJob, setSeedJob] = useState<SeedJob | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [apiNote, setApiNote] = useState("");

  useEffect(() => {
    fetchLimits().catch(() => undefined);

    const params = new URLSearchParams(window.location.search);
    if (params.get("fresh") === "1") {
      clearLocalWorkspace();
      window.history.replaceState({}, "", window.location.pathname);
      setProfile(null);
      setProfileLabel("No profile loaded");
      setSeedJob(null);
      setView("intake");
      setApiNote("Fresh start — paste your LinkedIn URL");
      loadExampleProfile()
        .then(() => setApiNote("API online — paste your LinkedIn URL"))
        .catch(() => setApiNote("API offline — start with: career-fit serve"));
      return;
    }

    const stored = loadStoredProfile();
    if (stored && profileName(stored)) {
      setProfile(stored);
      setProfileLabel(`Saved · ${profileName(stored)}`);
      setView("home");
      return;
    }
    loadExampleProfile()
      .then(() => setApiNote("API online — paste your LinkedIn URL"))
      .catch(() => setApiNote("API offline — start with: career-fit serve"));
  }, []);

  function applyProfile(
    p: Profile,
    label: string,
    opts?: { jobSearchUrl?: string; seedJob?: SeedJob | null },
  ) {
    setProfile(p);
    setProfileLabel(label);
    setSeedJob(opts?.seedJob || null);
    setSeedApp(null);
    setView(opts?.seedJob?.saved && !opts?.seedJob?.pack ? "home" : "craft");
    setRefreshKey((k) => k + 1);
  }

  function goCraft(app?: Application) {
    setSeedApp(app || null);
    if (app) setSeedJob(null);
    setView("craft");
  }

  function goStart() {
    setSeedApp(null);
    setSeedJob(null);
    setView("intake");
  }

  function eraseAndRestart() {
    const confirmed = window.confirm(
      "Clear all locally saved Career Fit data?\n\nThis removes your profile, applications, generated CVs, outreach history, and usage counters. This cannot be undone.",
    );
    if (!confirmed) return;
    clearLocalWorkspace();
    setProfile(null);
    setProfileLabel("No profile loaded");
    setSeedApp(null);
    setSeedJob(null);
    setView("intake");
    setApiNote("Saved intake erased — paste your LinkedIn URL");
  }

  return (
    <div className="app">
      <header className="shell-top">
        <div className="shell-brand-actions">
          <button
            type="button"
            className="brand-link"
            onClick={() => (profile ? setView("home") : setView("intake"))}
          >
            <span className="brand-mark">Career Fit</span>
          </button>
          <button
            type="button"
            className="reset-workspace"
            onClick={eraseAndRestart}
            title="Delete the local profile, applications, generated CVs, outreach, and usage history"
          >
            Clear all data
          </button>
        </div>
        <nav className="shell-nav" aria-label="Primary">
          <button
            type="button"
            className={`nav-pill ${view === "home" ? "on" : ""}`}
            disabled={!profile}
            onClick={() => setView("home")}
          >
            Home
          </button>
          <button
            type="button"
            className={`nav-pill ${view === "intake" ? "on" : ""}`}
            onClick={goStart}
          >
            Start
          </button>
          <button
            type="button"
            className={`nav-pill ${view === "craft" ? "on" : ""}`}
            disabled={!profile}
            onClick={() => goCraft()}
          >
            Craft
          </button>
        </nav>
      </header>

      {apiNote && !profile && <div className="notice">{apiNote}</div>}

      {view === "intake" && (
        <Intake
          initial={profile}
          onComplete={applyProfile}
          onCleared={eraseAndRestart}
          onCancel={profile ? () => setView("home") : undefined}
        />
      )}

      {view === "home" && profile && (
        <Home
          profile={profile}
          profileLabel={profileLabel}
          onCraft={goCraft}
          onIntake={goStart}
          refreshKey={refreshKey}
        />
      )}

      {view === "craft" && profile && (
        <Craft
          profile={profile}
          profileLabel={profileLabel}
          seedApp={seedApp}
          seedJob={seedJob}
          onProfile={(p, label) => {
            setProfile(p);
            setProfileLabel(label);
          }}
          onIntake={goStart}
          onHome={() => {
            setRefreshKey((k) => k + 1);
            setView("home");
          }}
          onSaved={() => setRefreshKey((k) => k + 1)}
        />
      )}

      <p className="footer-note">
        You send messages manually. We draft and track. Workspace data stays in
        this browser.
      </p>
    </div>
  );
}
