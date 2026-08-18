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

export async function uploadProfileYaml(file: File): Promise<Profile> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch("/api/upload-profile", { method: "POST", body: fd });
  if (!res.ok) throw new Error(await res.text());
  const data = (await res.json()) as { profile: Profile };
  return data.profile;
}
