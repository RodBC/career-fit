import type { Profile } from "./api";

export type Stage =
  | "saved"
  | "applied"
  | "waiting"
  | "interviewing"
  | "offer"
  | "rejected";

export type Application = {
  id: string;
  title: string;
  company: string;
  stage: Stage;
  angle: string;
  locale: string;
  job_description: string;
  next_action: string;
  created_at: string;
  updated_at: string;
  artifact_id: string | null;
};

export type Artifact = {
  id: string;
  application_id: string;
  markdown: string;
  latex: string;
  company_message: string;
  summary: string;
  proof: string;
  created_at: string;
};

export type OutreachRecord = {
  id: string;
  name: string;
  title: string;
  company: string;
  channel: "dm" | "email";
  draft_message: string;
  email: string;
  linkedin_url: string;
  application_id: string | null;
  sent: boolean;
  reply: boolean;
  created_at: string;
  updated_at: string;
};

export type Usage = {
  month: string; // YYYY-MM
  tailor_count: number;
  pro_requested: boolean;
};

const K = {
  profile: "career-fit.profile.v1",
  apps: "career-fit.applications.v1",
  artifacts: "career-fit.artifacts.v1",
  outreach: "career-fit.outreach.v1",
  usage: "career-fit.usage.v1",
  dismissed: "career-fit.today-dismissed.v1",
};

function read<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function write(key: string, value: unknown) {
  localStorage.setItem(key, JSON.stringify(value));
}

export function loadStoredProfile(): Profile | null {
  return read<Profile | null>(K.profile, null);
}

export function storeProfile(profile: Profile | null) {
  if (!profile) localStorage.removeItem(K.profile);
  else write(K.profile, profile);
}

export function loadApplications(): Application[] {
  return read(K.apps, []);
}

export function saveApplications(apps: Application[]) {
  write(K.apps, apps);
}

export function loadArtifacts(): Artifact[] {
  return read(K.artifacts, []);
}

export function saveArtifacts(arts: Artifact[]) {
  write(K.artifacts, arts);
}

export function upsertApplicationBundle(app: Application, art: Artifact) {
  const apps = loadApplications().filter((a) => a.id !== app.id);
  apps.unshift(app);
  saveApplications(apps);
  const arts = loadArtifacts().filter((a) => a.id !== art.id);
  arts.unshift(art);
  saveArtifacts(arts);
}

export function updateApplication(id: string, patch: Partial<Application>) {
  const apps = loadApplications().map((a) =>
    a.id === id
      ? { ...a, ...patch, updated_at: new Date().toISOString() }
      : a,
  );
  saveApplications(apps);
  return apps;
}

export function loadOutreach(): OutreachRecord[] {
  return read(K.outreach, []);
}

export function saveOutreach(rows: OutreachRecord[]) {
  write(K.outreach, rows);
}

export function upsertOutreach(row: OutreachRecord) {
  const rows = loadOutreach().filter((o) => o.id !== row.id);
  rows.unshift(row);
  saveOutreach(rows);
  return rows;
}

export function updateOutreach(id: string, patch: Partial<OutreachRecord>) {
  const rows = loadOutreach().map((o) =>
    o.id === id
      ? { ...o, ...patch, updated_at: new Date().toISOString() }
      : o,
  );
  saveOutreach(rows);
  return rows;
}

function monthKey() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function loadUsage(): Usage {
  const u = read<Usage>(K.usage, {
    month: monthKey(),
    tailor_count: 0,
    pro_requested: false,
  });
  if (u.month !== monthKey()) {
    const reset = { month: monthKey(), tailor_count: 0, pro_requested: u.pro_requested };
    write(K.usage, reset);
    return reset;
  }
  return u;
}

export function bumpTailorCount(): Usage {
  const u = loadUsage();
  const next = { ...u, tailor_count: u.tailor_count + 1 };
  write(K.usage, next);
  return next;
}

export function markProRequested(): Usage {
  const u = { ...loadUsage(), pro_requested: true };
  write(K.usage, u);
  return u;
}

export function loadDismissedToday(): string[] {
  return read(K.dismissed, []);
}

export function dismissToday(id: string) {
  const ids = [...new Set([...loadDismissedToday(), id])];
  write(K.dismissed, ids);
  return ids;
}

export function artifactForApp(
  appId: string,
  arts: Artifact[] = loadArtifacts(),
): Artifact | undefined {
  return arts.find((a) => a.application_id === appId);
}
