import { useEffect, useState } from "react";
import { fetchToday, type Profile, type TodayCard } from "./api";
import {
  dismissToday,
  loadApplications,
  loadDismissedToday,
  loadOutreach,
  loadUsage,
  type Application,
  type OutreachRecord,
  type Stage,
  updateApplication,
  updateOutreach,
} from "./store";

const STAGE_LABEL: Record<Stage, string> = {
  saved: "Ready to send",
  applied: "Applied — waiting on them",
  waiting: "Waiting on a reply",
  interviewing: "Interviewing",
  offer: "Offer",
  rejected: "Closed — rejected",
};

type Props = {
  profile: Profile | null;
  profileLabel: string;
  limitsBlurb: string;
  proPrice: number;
  onCraft: (app?: Application) => void;
  onIntake: () => void;
  onPeopleFocus?: () => void;
  refreshKey: number;
};

export default function Home({
  profile,
  profileLabel,
  limitsBlurb,
  proPrice,
  onCraft,
  onIntake,
  refreshKey,
}: Props) {
  const [apps, setApps] = useState<Application[]>([]);
  const [people, setPeople] = useState<OutreachRecord[]>([]);
  const [cards, setCards] = useState<TodayCard[]>([]);
  const [savedFlash, setSavedFlash] = useState("");
  const usage = loadUsage();
  const name =
    (profile?.identity as { name?: string } | undefined)?.name || "there";

  function reload() {
    setApps(loadApplications());
    setPeople(loadOutreach());
  }

  useEffect(() => {
    reload();
    fetchToday({
      profile,
      applications: loadApplications(),
      outreach: loadOutreach(),
      dismissed_ids: loadDismissedToday(),
    })
      .then((r) => setCards(r.cards))
      .catch(() => setCards([]));
  }, [profile, refreshKey]);

  function onStage(id: string, stage: Stage) {
    setApps(updateApplication(id, { stage }));
    setSavedFlash("Pipeline updated");
    setTimeout(() => setSavedFlash(""), 1600);
  }

  async function onDismissCard(id: string) {
    dismissToday(id);
    const r = await fetchToday({
      profile,
      applications: loadApplications(),
      outreach: loadOutreach(),
      dismissed_ids: loadDismissedToday(),
    });
    setCards(r.cards);
  }

  function onCardAction(card: TodayCard) {
    if (card.action === "intake") onIntake();
    else if (card.action === "people") onCraft();
    else if (card.application_id) {
      const app = apps.find((a) => a.id === card.application_id);
      onCraft(app);
    } else onCraft();
  }

  return (
    <div className="home view-enter">
      <section className="home-hero">
        <p className="home-kicker">{profileLabel}</p>
        <h1 className="home-brand">Career Fit</h1>
        <p className="home-lead">
          Hi {name.split(" ")[0]} — keep advancing. Craft a pack, track who you
          reached, do the next sharp move.
        </p>
        <div className="row home-cta">
          <button type="button" className="btn" onClick={() => onCraft()}>
            {apps.length ? "Continue crafting" : "Add a role"}
          </button>
          <button type="button" className="btn secondary" onClick={onIntake}>
            Edit intake
          </button>
        </div>
        {savedFlash && <p className="status ok save-flash">{savedFlash}</p>}
      </section>

      <section className="home-block">
        <h2>Today</h2>
        <p className="hint">At most three moves. You send — we track.</p>
        {cards.length === 0 ? (
          <p className="empty-line">Nothing urgent. Craft a role or log outreach.</p>
        ) : (
          <ul className="today-list">
            {cards.map((c) => (
              <li key={c.id} className="today-item">
                <div>
                  <strong>{c.title}</strong>
                  <p className="hint">{c.why}</p>
                </div>
                <div className="row">
                  <button
                    type="button"
                    className="btn"
                    onClick={() => onCardAction(c)}
                  >
                    Do it
                  </button>
                  <button
                    type="button"
                    className="btn secondary"
                    onClick={() => onDismissCard(c.id)}
                  >
                    Snooze
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="home-block">
        <h2>Pipeline</h2>
        {apps.length === 0 ? (
          <p className="empty-line">
            No applications yet — generate a tailored pack and save it here.
          </p>
        ) : (
          <ul className="pipeline-list">
            {apps.map((a) => (
              <li key={a.id} className="pipeline-item">
                <button
                  type="button"
                  className="pipeline-main"
                  onClick={() => onCraft(a)}
                >
                  <span className="pipeline-title">
                    {a.title}
                    {a.company ? ` · ${a.company}` : ""}
                  </span>
                  <span className="stage-chip">{STAGE_LABEL[a.stage]}</span>
                </button>
                <div className="row">
                  <select
                    value={a.stage}
                    onChange={(e) => onStage(a.id, e.target.value as Stage)}
                    aria-label="Stage"
                  >
                    {(Object.keys(STAGE_LABEL) as Stage[]).map((s) => (
                      <option key={s} value={s}>
                        {STAGE_LABEL[s]}
                      </option>
                    ))}
                  </select>
                  {a.angle && <span className="angle">angle · {a.angle}</span>}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="home-block">
        <h2>People</h2>
        {people.length === 0 ? (
          <p className="empty-line">
            Log recruiter drafts from Craft after you paste contacts.
          </p>
        ) : (
          <ul className="people-list">
            {people.slice(0, 8).map((p) => (
              <li key={p.id} className="people-item">
                <div>
                  <strong>{p.name}</strong>
                  <p className="meta">
                    {p.title || "Contact"}
                    {p.company ? ` · ${p.company}` : ""}
                    {p.sent ? " · sent" : " · draft"}
                    {p.reply ? " · replied" : ""}
                  </p>
                </div>
                <div className="row">
                  {!p.sent && (
                    <button
                      type="button"
                      className="btn secondary"
                      onClick={() => {
                        setPeople(updateOutreach(p.id, { sent: true }));
                      }}
                    >
                      Mark sent
                    </button>
                  )}
                  {p.sent && !p.reply && (
                    <button
                      type="button"
                      className="btn secondary"
                      onClick={() => {
                        setPeople(updateOutreach(p.id, { reply: true }));
                      }}
                    >
                      Got reply
                    </button>
                  )}
                  <button
                    type="button"
                    className="btn ghost"
                    onClick={() => navigator.clipboard.writeText(p.draft_message)}
                  >
                    Copy draft
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <aside className="pro-panel">
        <p>
          Free this month: {usage.tailor_count} tailor
          {usage.tailor_count === 1 ? "" : "s"} used · pipeline {apps.length}{" "}
          roles.
        </p>
        <p className="hint">{limitsBlurb || `Pro ($${proPrice}/mo) unlocks unlimited craft + full memory.`}</p>
        {usage.pro_requested && (
          <p className="status ok">Pro interest noted — billing comes after the loop feels sticky.</p>
        )}
      </aside>
    </div>
  );
}
