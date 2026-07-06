export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (res.status === 401) {
    if (typeof window !== "undefined") window.location.href = "/";
    throw new Error("Not authenticated");
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  me: () => request("/auth/me"),
  githubRepos: () => request("/repos/github"),
  connectedRepos: () => request("/repos"),
  connectRepo: (owner: string, name: string) =>
    request("/repos", { method: "POST", body: JSON.stringify({ owner, name }) }),
  repoEvents: (repoId: number) => request(`/repos/${repoId}/events`),
  listRules: (repoId: number) => request(`/repos/${repoId}/rules`),
  createRule: (repoId: number, rule: any) =>
    request(`/repos/${repoId}/rules`, { method: "POST", body: JSON.stringify(rule) }),
  deleteRule: (repoId: number, ruleId: number) =>
    request(`/repos/${repoId}/rules/${ruleId}`, { method: "DELETE" }),
};
