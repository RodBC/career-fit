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
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
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

export function parseResume(text: string) {
  return api<{
    summary: string;
    skills: string[];
    experience: unknown[];
    projects: unknown[];
    education: unknown[];
    warnings: string[];
  }>("/api/parse-resume", {
    method: "POST",
    body: JSON.stringify({ text }),
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

const STORAGE_KEY = "career-fit.profile.v1";

export function loadStoredProfile(): Profile | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as Profile;
  } catch {
    return null;
  }
}

export function storeProfile(profile: Profile | null) {
  if (!profile) {
    localStorage.removeItem(STORAGE_KEY);
    return;
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
}
