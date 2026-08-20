export type Profile = Record<string, unknown>;

export type TailorResult = {
  angle: string;
  locale: string;
  markdown: string;
  latex: string;
  company_message: string;
  summary: string;
  proof: string;
  project_name: string;
};

export type Contact = {
  name: string;
  title: string;
  company: string;
  linkedin_url: string;
  email: string;
  phone: string;
  about: string;
  source: string;
  score: number;
  rationale: string;
  draft_message: string;
};

export type IntakePayload = {
  identity: {
    name: string;
    email: string;
    city?: string;
    phone?: string;
    linkedin?: string;
    languages?: string;
  };
  career_tutoring: {
    enjoyed_most?: string;
    positive_differentials?: string;
    improvement_areas?: string;
    technical_knowledge?: string;
    networking_notes?: string;
    hates_doing?: string;
    challenges_overcome?: string;
  };
  targets: {
    roles_wanted?: string;
    locales?: string[];
    remote?: boolean;
  };
  resume_text?: string;
  base_profile?: Profile | null;
};

export type IntakeResult = {
  ok: boolean;
  profile: Profile;
  warnings: string[];
  parsed_roles: number;
  parsed_projects: number;
};

export type TrackerLimits = {
  free_tailor_per_month: number;
  free_application_cap: number;
  pro_price_usd: number;
  pro_blurb: string;
  stages: { id: string; label: string }[];
};

export type TodayCard = {
  id: string;
  title: string;
  why: string;
  action: string;
  application_id?: string | null;
  outreach_id?: string | null;
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    let detail = text || res.statusText;
    try {
      const j = JSON.parse(text) as { detail?: string };
      if (j?.detail) detail = typeof j.detail === "string" ? j.detail : text;
    } catch {
      /* plain text */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export function fetchSessionStatus() {
  return api<{
    ok: boolean;
    chrome_ok: boolean; // alias of camoufox_ok (back-compat)
    camoufox_ok?: boolean;
    logged_in_hint: boolean;
    ready: boolean;
    hint: string;
    engine?: string;
    user_data_dir?: string;
  }>("/api/session-status");
}

/** Opens Camoufox for LinkedIn login; may take several minutes. */
export function openLinkedInSession() {
  return api<{
    ok: boolean;
    logged_in: boolean;
    hint: string;
    after?: {
      chrome_ok: boolean;
      camoufox_ok?: boolean;
      logged_in_hint: boolean;
      ready: boolean;
      hint: string;
    };
  }>("/api/linkedin-session", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function loadExampleProfile() {
  return api<Profile>("/api/example-profile");
}

export function parseJob(raw: string, source = "paste") {
  return api<{
    title: string;
    company: string;
    description: string;
    locale_hint: string | null;
  }>("/api/parse-job", {
    method: "POST",
    body: JSON.stringify({ raw, source }),
  });
}

export type RoleInsights = {
  angle: string;
  angle_score: number;
  angle_rationale: string;
  top_angles: { angle: string; score: number }[];
  bullets: string[];
  gaps: string[];
  intake_nudge: string;
};

export type MapJobResult = {
  ok: boolean;
  job: {
    title: string;
    company: string;
    description: string;
    source: string;
    locale_hint: string | null;
  };
  insights: RoleInsights;
  meta: { source: string; url: string; mock: boolean };
};

export function mapJob(body: {
  url: string;
  profile?: Profile | null;
  mock?: boolean | null;
  locale?: string;
}) {
  return api<MapJobResult>("/api/map-job", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export type SuggestedRole = {
  id: string;
  title: string;
  kind: string;
  why: string;
  linkedin_url: string;
};

export type MapProfileResult = {
  ok: boolean;
  snapshot: {
    name?: string;
    headline?: string;
    location?: string;
    about?: string;
    experience_text?: string;
    linkedin_url?: string;
  };
  profile: Profile;
  suggested_roles?: SuggestedRole[];
  meta: { source: string; url: string; mock: boolean };
};

export function mapProfile(body: {
  url: string;
  mock?: boolean | null;
  stub?: boolean;
}) {
  return api<MapProfileResult>("/api/map-profile", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export type JobOpening = {
  id: string;
  title: string;
  company: string;
  blurb: string;
  description: string;
  linkedin_url: string;
  sample: boolean;
};

export function suggestOpenings(body: {
  role_titles?: string[];
  keywords?: string;
  location?: string;
  limit?: number;
}) {
  return api<{ ok: boolean; openings: JobOpening[]; note: string }>(
    "/api/suggest-openings",
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

export function suggestRoles(body: {
  profile: Profile | null;
  headline?: string;
  location?: string;
  limit?: number;
}) {
  return api<{ ok: boolean; roles: SuggestedRole[] }>("/api/suggest-roles", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export type SamplePackResult = {
  ok: boolean;
  job: MapJobResult["job"];
  insights: RoleInsights;
  pack: TailorResult;
  linkedin_search_url: string;
  meta: { source: string; mock: boolean; role_title: string };
};

export function samplePack(body: {
  profile: Profile | null;
  role_title: string;
  locale?: string;
}) {
  return api<SamplePackResult>("/api/sample-pack", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function jobInsights(body: {
  raw?: string;
  title?: string;
  company?: string;
  profile?: Profile | null;
  locale?: string;
  source?: string;
}) {
  return api<{ ok: boolean; job: MapJobResult["job"]; insights: RoleInsights }>(
    "/api/job-insights",
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

export function tailor(body: {
  profile: Profile | null;
  job: {
    title: string;
    company: string;
    description: string;
    locale?: string;
    raw_paste?: string;
  };
  angle?: string;
}) {
  return api<TailorResult>("/api/tailor", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function recruiters(body: {
  profile: Profile | null;
  job: {
    title: string;
    company: string;
    description: string;
    locale?: string;
  };
  contacts_text: string;
  angle?: string;
  locale?: string;
}) {
  return api<{ contacts: Contact[]; note: string; angle: string }>(
    "/api/recruiters",
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

export function submitIntake(body: IntakePayload) {
  return api<IntakeResult>("/api/intake", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function uploadProfileYaml(file: File): Promise<Profile> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch("/api/upload-profile", { method: "POST", body: fd });
  if (!res.ok) throw new Error(await res.text());
  const data = (await res.json()) as { profile: Profile };
  return data.profile;
}

export function fetchLimits() {
  return api<TrackerLimits>("/api/tracker/limits");
}

export function saveApplicationRemote(body: {
  title: string;
  company: string;
  angle: string;
  locale: string;
  job_description: string;
  markdown: string;
  latex: string;
  company_message: string;
  summary: string;
  proof: string;
}) {
  return api<{
    ok: boolean;
    application: import("./store").Application;
    artifact: import("./store").Artifact;
  }>("/api/tracker/save-application", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function logOutreachRemote(body: {
  contact: Contact;
  application_id?: string | null;
  applications: import("./store").Application[];
  sent?: boolean;
}) {
  return api<{ ok: boolean; outreach: import("./store").OutreachRecord }>(
    "/api/tracker/log-outreach",
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

export function fetchToday(body: {
  profile: Profile | null;
  applications: import("./store").Application[];
  outreach: import("./store").OutreachRecord[];
  dismissed_ids: string[];
}) {
  return api<{ cards: TodayCard[]; max: number }>("/api/tracker/today", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// Re-exports for callers that used api.ts storage helpers
export {
  clearLocalWorkspace,
  loadStoredProfile,
  storeProfile,
} from "./store";
