export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const SLACK_CLIENT_ID = process.env.NEXT_PUBLIC_SLACK_CLIENT_ID || "";

export function getSlackInstallUrl() {
  if (!SLACK_CLIENT_ID) {
    return "https://slack.com/create";
  }

  const scope = [
    "channels:join",
    "incoming-webhook",
    "chat:write",
    "channels:read",
    "groups:read",
    "im:read",
    "mpim:read",
  ].join(",");

  const params = new URLSearchParams({
    client_id: SLACK_CLIENT_ID,
    scope,
    user_scope: "",
  });

  return `https://slack.com/oauth/v2/authorize?${params.toString()}`;
}

async function request(path: string, options: RequestInit = {}) {
  const authToken =
    typeof window !== "undefined" ? window.localStorage.getItem("session_token") : null;
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      ...(options.headers || {}),
    },
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
  slackConnection: () => request("/auth/slack"),
  updateSlackConnection: (payload: any) =>
    request("/auth/slack", { method: "PUT", body: JSON.stringify(payload) }),
  slackLoginUrl: () => `${API_URL}/auth/slack/login`,
  slackSignupUrl: () => getSlackInstallUrl(),
  slackChannels: () => request("/auth/slack/channels"),
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
