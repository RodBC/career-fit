import { useEffect, useState } from "react";
import {
  fetchLimits,
  loadExampleProfile,
  loadStoredProfile,
  type Profile,
} from "./api";
import Craft from "./Craft";
import Home from "./Home";
import Intake from "./Intake";
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
  const [refreshKey, setRefreshKey] = useState(0);
  const [apiNote, setApiNote] = useState("");
  const [proBlurb, setProBlurb] = useState("");
  const [proPrice, setProPrice] = useState(29);

  useEffect(() => {
    fetchLimits()
      .then((l) => {
        setProBlurb(l.pro_blurb);
        setProPrice(l.pro_price_usd);
      })
      .catch(() => undefined);

    const stored = loadStoredProfile();
    if (stored && profileName(stored)) {
      setProfile(stored);
      setProfileLabel(`Saved intake: ${profileName(stored)}`);
      setView("home");
      return;
    }
    loadExampleProfile()
      .then(() => setApiNote("API online — complete intake to begin"))
      .catch(() => setApiNote("API offline — start with: career-fit serve"));
  }, []);

  function applyProfile(p: Profile, label: string) {
    setProfile(p);
    setProfileLabel(label);
    setView("home");
    setRefreshKey((k) => k + 1);
  }

  function goCraft(app?: Application) {
    setSeedApp(app || null);
    setView("craft");
  }

  return (
    <div className="app">
      <header className="shell-top">
        <button
          type="button"
          className="brand-link"
          onClick={() => (profile ? setView("home") : setView("intake"))}
        >
          <span className="brand-mark">Career Fit</span>
        </button>
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
            onClick={() => setView("intake")}
          >
            Intake
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
          onCancel={profile ? () => setView("home") : undefined}
        />
      )}

      {view === "home" && profile && (
        <Home
          profile={profile}
          profileLabel={profileLabel}
          limitsBlurb={proBlurb}
          proPrice={proPrice}
          onCraft={goCraft}
          onIntake={() => setView("intake")}
          refreshKey={refreshKey}
        />
      )}

      {view === "craft" && profile && (
        <Craft
          profile={profile}
          profileLabel={profileLabel}
          seedApp={seedApp}
          onProfile={(p, label) => {
            setProfile(p);
            setProfileLabel(label);
          }}
          onIntake={() => setView("intake")}
          onHome={() => {
            setRefreshKey((k) => k + 1);
            setView("home");
          }}
          onSaved={() => setRefreshKey((k) => k + 1)}
        />
      )}

      <p className="footer-note">
        You send messages manually. We draft and track. See{" "}
        <code>docs/AI_BUILD_MAP.md</code> · Pro working price ${proPrice}/mo
        (soft gate).
      </p>
    </div>
  );
}
