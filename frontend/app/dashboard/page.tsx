"use client";

import { useEffect, useState } from "react";
import { api, API_URL } from "../../lib/api";
import { BotLogo } from "../logo";

type GhRepo = { owner: string; name: string; full_name: string };
type Repo = { id: number; owner: string; name: string; connected_at: string };
type Rule = {
  id: number; name: string; event_type: string; match_field: string;
  match_type: string; match_value: string; add_label?: string;
  post_comment?: string; slack_notify: boolean; enabled: boolean;
};
type ActionLog = { action_type: string; status: string; detail?: string };
type EventRow = {
  id: number; event_type: string; action?: string; status: string;
  error?: string; received_at: string; actions: ActionLog[];
};

const GH_PATH = "M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z";

const GhIcon = ({ size = 20 }: { size?: number }) => (
  <svg height={size} viewBox="0 0 16 16" width={size} fill="currentColor" aria-hidden="true">
    <path d={GH_PATH} />
  </svg>
);

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, [string, string]> = {
    processed: ["#1a2f1a", "#3fb950"],
    failed: ["#2d1b1b", "#f85149"],
    skipped: ["#1c1f28", "#8b949e"],
  };
  const [bg, color] = map[status] ?? map.skipped;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5, background: bg, color, border: `1px solid ${color}33`, borderRadius: 12, padding: "2px 10px", fontSize: 12, fontWeight: 500 }}>
      <span style={{ width: 7, height: 7, borderRadius: "50%", background: color, display: "inline-block" }} />
      {status}
    </span>
  );
}

function EventTypeBadge({ type, action }: { type: string; action?: string }) {
  const colorMap: Record<string, string> = { issues: "#d29922", pull_request: "#58a6ff", push: "#bc8cff", ping: "#8b949e" };
  const color = colorMap[type] ?? "#8b949e";
  return (
    <span style={{ display: "inline-block", background: `${color}22`, color, border: `1px solid ${color}44`, borderRadius: 12, padding: "2px 10px", fontSize: 12, fontWeight: 500 }}>
      {action ? `${type} ${action}` : type}
    </span>
  );
}

function ActionChip({ action_type, status }: ActionLog) {
  const ok = status === "success";
  const icons: Record<string, string> = { github_label: "🏷️", slack_notify: "🔔", post_comment: "💬" };
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, background: ok ? "#1a2f1a" : "#2d1b1b", color: ok ? "#3fb950" : "#f85149", border: `1px solid ${ok ? "#3fb95033" : "#f8514933"}`, borderRadius: 4, padding: "2px 8px", fontSize: 12, marginRight: 4, marginBottom: 4 }}>
      {icons[action_type] ?? "⚡"} {action_type.replace("_", " ")} {ok ? "✓" : "✗"}
    </span>
  );
}

function RepoCard({ repo, conn, isSelected, isConnecting, onConnect, onSelect }: {
  repo: GhRepo; conn?: Repo; isSelected: boolean; isConnecting: boolean;
  onConnect: () => void; onSelect: () => void;
}) {
  const [hover, setHover] = useState(false);
  const connected = !!conn;

  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: isSelected ? "#1c2d3a" : hover ? "#1c2128" : "#161b22",
        border: `1px solid ${isSelected ? "#58a6ff55" : hover ? "#30363d" : "#21262d"}`,
        borderRadius: 8, padding: "12px 14px",
        display: "flex", flexDirection: "column", gap: 10,
        transition: "all 0.15s", cursor: connected ? "pointer" : "default",
      }}
      onClick={connected ? onSelect : undefined}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
          <div style={{ color: "#8b949e", flexShrink: 0 }}><GhIcon size={15} /></div>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 12, color: "#8b949e", lineHeight: 1 }}>{repo.owner}</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#f0f6fc", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {repo.name}
            </div>
          </div>
        </div>
        {connected && (
          <span style={{ flexShrink: 0, background: "#1a2f1a", color: "#3fb950", border: "1px solid #3fb95033", borderRadius: 10, padding: "1px 7px", fontSize: 10, fontWeight: 600 }}>
            ● live
          </span>
        )}
      </div>
      {!connected ? (
        <button
          onClick={(e) => { e.stopPropagation(); onConnect(); }}
          disabled={isConnecting}
          style={{
            background: isConnecting ? "#21262d" : hover ? "#1f6feb" : "#0d419d",
            border: "1px solid rgba(240,246,252,0.1)", color: "white",
            borderRadius: 6, padding: "5px 0", fontSize: 12, fontWeight: 600,
            width: "100%", transition: "background 0.15s",
            opacity: isConnecting ? 0.7 : 1,
          }}
        >
          {isConnecting ? "Connecting…" : "+ Connect webhook"}
        </button>
      ) : (
        <button
          onClick={(e) => { e.stopPropagation(); onSelect(); }}
          style={{
            background: isSelected ? "#58a6ff22" : "transparent",
            border: `1px solid ${isSelected ? "#58a6ff55" : "#30363d"}`,
            color: isSelected ? "#58a6ff" : "#8b949e",
            borderRadius: 6, padding: "5px 0", fontSize: 12,
            width: "100%", transition: "all 0.15s",
          }}
        >
          {isSelected ? "▶ Viewing" : "View dashboard →"}
        </button>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [user, setUser] = useState<any>(null);
  const [ghRepos, setGhRepos] = useState<GhRepo[]>([]);
  const [connected, setConnected] = useState<Repo[]>([]);
  const [selected, setSelected] = useState<Repo | null>(null);
  const [events, setEvents] = useState<EventRow[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState<"all" | "connected">("all");
  const [newRule, setNewRule] = useState({
    name: "", event_type: "issues", match_field: "title", match_type: "contains",
    match_value: "", add_label: "", post_comment: "", slack_notify: true, enabled: true,
  });

  useEffect(() => {
    (async () => {
      try {
        const me = await api.me();
        setUser(me);
        const [gh, conn] = await Promise.all([api.githubRepos(), api.connectedRepos()]);
        setGhRepos(gh);
        setConnected(conn);
        if (conn.length > 0) setSelected(conn[0]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!selected) return;
    const load = async () => {
      const [ev, rl] = await Promise.all([api.repoEvents(selected.id), api.listRules(selected.id)]);
      setEvents(ev);
      setRules(rl);
    };
    load();
    const iv = setInterval(load, 5000);
    return () => clearInterval(iv);
  }, [selected]);

  async function handleConnect(r: GhRepo) {
    setConnecting(r.full_name);
    try {
      const repo = await api.connectRepo(r.owner, r.name);
      setConnected((p) => [...p.filter((x) => x.id !== repo.id), repo]);
      setSelected(repo);
    } finally {
      setConnecting(null);
    }
  }

  async function handleCreateRule() {
    if (!selected || !newRule.match_value) return;
    const rule = await api.createRule(selected.id, newRule);
    setRules((p) => [...p, rule]);
    setNewRule({ ...newRule, name: "", match_value: "", add_label: "", post_comment: "" });
  }

  async function handleDeleteRule(id: number) {
    if (!selected) return;
    await api.deleteRule(selected.id, id);
    setRules((p) => p.filter((r) => r.id !== id));
  }

  const filtered = ghRepos
    .filter((r) => r.full_name.toLowerCase().includes(search.toLowerCase()))
    .filter((r) => activeTab === "all" || connected.find((c) => c.owner === r.owner && c.name === r.name));

  if (loading) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", gap: 10, color: "#8b949e" }}>
      <GhIcon size={18} /> Loading…
    </div>
  );

  return (
    <div style={{ minHeight: "100vh", background: "#0d1117" }}>
      {/* Navbar */}
      <header style={{ background: "#161b22", borderBottom: "1px solid #30363d", padding: "0 24px", height: 56, display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, color: "#f0f6fc", fontWeight: 600, fontSize: 15 }}>
          <BotLogo size={32} />
          <span style={{ color: "#8b949e" }}>GitHub</span>
          <span style={{ color: "#30363d" }}>/</span>
          <span>Automation Bot</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {user?.avatar_url && <img src={user.avatar_url} alt="" width={28} height={28} style={{ borderRadius: "50%", border: "2px solid #30363d" }} />}
          <span style={{ color: "#c9d1d9", fontWeight: 500, fontSize: 14 }}>{user?.username}</span>
          <a href={`${API_URL}/auth/logout`} style={{ background: "#21262d", border: "1px solid #30363d", borderRadius: 6, padding: "5px 14px", color: "#c9d1d9", fontSize: 13, textDecoration: "none" }}>Sign out</a>
        </div>
      </header>

      <div style={{ display: "flex", maxWidth: 1400, margin: "0 auto", padding: "0 24px 40px", gap: 24, alignItems: "flex-start" }}>
        {/* Left panel — repos */}
        <aside style={{ width: 300, flexShrink: 0, paddingTop: 24, position: "sticky", top: 72, maxHeight: "calc(100vh - 90px)", display: "flex", flexDirection: "column" }}>
          <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, display: "flex", flexDirection: "column", overflow: "hidden", flex: 1 }}>
            {/* Panel header */}
            <div style={{ padding: "14px 16px", borderBottom: "1px solid #21262d" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                <span style={{ fontWeight: 600, color: "#f0f6fc", fontSize: 14 }}>Repositories</span>
                <span style={{ background: "#21262d", border: "1px solid #30363d", borderRadius: 10, padding: "1px 8px", fontSize: 12, color: "#8b949e" }}>
                  {connected.length} / {ghRepos.length}
                </span>
              </div>
              <input placeholder="🔍  Filter repositories…" value={search} onChange={(e) => setSearch(e.target.value)}
                style={{ width: "100%", background: "#0d1117", boxSizing: "border-box" }} />
              {/* Tabs */}
              <div style={{ display: "flex", gap: 4, marginTop: 10 }}>
                {(["all", "connected"] as const).map((t) => (
                  <button key={t} onClick={() => setActiveTab(t)} style={{
                    flex: 1, background: activeTab === t ? "#21262d" : "transparent",
                    border: `1px solid ${activeTab === t ? "#58a6ff55" : "#30363d"}`,
                    color: activeTab === t ? "#58a6ff" : "#8b949e", fontSize: 12, padding: "4px 0",
                  }}>
                    {t === "all" ? `All (${ghRepos.length})` : `Connected (${connected.length})`}
                  </button>
                ))}
              </div>
            </div>
            {/* Repo grid */}
            <div style={{ overflowY: "auto", padding: 12, display: "flex", flexDirection: "column", gap: 8, flex: 1 }}>
              {filtered.length === 0 ? (
                <div style={{ color: "#8b949e", fontSize: 13, textAlign: "center", padding: "24px 0" }}>No repos found</div>
              ) : filtered.map((r) => {
                const conn = connected.find((c) => c.owner === r.owner && c.name === r.name);
                return (
                  <RepoCard
                    key={r.full_name} repo={r} conn={conn}
                    isSelected={!!(selected && conn && selected.id === conn.id)}
                    isConnecting={connecting === r.full_name}
                    onConnect={() => handleConnect(r)}
                    onSelect={() => conn && setSelected(conn)}
                  />
                );
              })}
            </div>
          </div>
        </aside>

        {/* Right panel — main */}
        <main style={{ flex: 1, minWidth: 0, paddingTop: 24 }}>
          {!selected ? (
            <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: "64px 32px", textAlign: "center" }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>🔗</div>
              <div style={{ fontWeight: 600, color: "#f0f6fc", fontSize: 18, marginBottom: 8 }}>No repository selected</div>
              <div style={{ fontSize: 14, color: "#8b949e" }}>Connect a repository from the panel on the left to start automating.</div>
            </div>
          ) : (
            <>
              {/* Repo header */}
              <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: "16px 20px", marginBottom: 16, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <GhIcon size={18} />
                  <span style={{ color: "#8b949e", fontSize: 16 }}>{selected.owner} </span>
                  <span style={{ color: "#8b949e" }}>/</span>
                  <span style={{ color: "#f0f6fc", fontWeight: 700, fontSize: 18 }}>{selected.name}</span>
                  <span style={{ background: "#1a2f1a", color: "#3fb950", border: "1px solid #3fb95033", borderRadius: 12, padding: "2px 10px", fontSize: 11, fontWeight: 600 }}>● webhook active</span>
                </div>
                <a href={`https://github.com/${selected.owner}/${selected.name}`} target="_blank" rel="noopener noreferrer"
                  style={{ color: "#58a6ff", fontSize: 13, display: "flex", alignItems: "center", gap: 5, textDecoration: "none" }}>
                  <GhIcon size={14} /> View on GitHub ↗
                </a>
              </div>

              {/* Stats */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 16 }}>
                {[
                  { label: "Rules", value: rules.length, color: "#58a6ff", icon: "⚙️" },
                  { label: "Total events", value: events.length, color: "#c9d1d9", icon: "📋" },
                  { label: "Processed", value: events.filter(e => e.status === "processed").length, color: "#3fb950", icon: "✅" },
                  { label: "Failed", value: events.filter(e => e.status === "failed").length, color: "#f85149", icon: "❌" },
                ].map(({ label, value, color, icon }) => (
                  <div key={label} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: "16px 20px" }}>
                    <div style={{ fontSize: 22, marginBottom: 6 }}>{icon}</div>
                    <div style={{ fontSize: 28, fontWeight: 700, color, lineHeight: 1 }}>{value}</div>
                    <div style={{ fontSize: 12, color: "#8b949e", marginTop: 4 }}>{label}</div>
                  </div>
                ))}
              </div>

              {/* Rules */}
              <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, marginBottom: 16, overflow: "hidden" }}>
                <div style={{ padding: "14px 20px", borderBottom: "1px solid #21262d", display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontWeight: 600, color: "#f0f6fc", fontSize: 14 }}>⚙️ Automation Rules</span>
                  <span style={{ background: "#21262d", border: "1px solid #30363d", borderRadius: 10, padding: "1px 7px", fontSize: 12, color: "#8b949e" }}>{rules.length}</span>
                </div>

                {rules.length === 0 ? (
                  <div style={{ padding: "28px 20px", color: "#8b949e", textAlign: "center", fontSize: 13 }}>
                    No rules yet — add your first rule below to start automating
                  </div>
                ) : rules.map((r) => (
                  <div key={r.id} style={{ padding: "12px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid #21262d", gap: 12 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", flex: 1 }}>
                      <EventTypeBadge type={r.event_type} />
                      <span style={{ color: "#8b949e", fontSize: 13 }}>if</span>
                      <code style={{ background: "#1c2128", border: "1px solid #30363d", borderRadius: 4, padding: "2px 8px", fontSize: 12, color: "#c9d1d9" }}>{r.match_field}</code>
                      <span style={{ color: "#8b949e", fontSize: 13 }}>contains</span>
                      <code style={{ background: "#1c2128", border: "1px solid #30363d", borderRadius: 4, padding: "2px 8px", fontSize: 12, color: "#79c0ff" }}>"{r.match_value}"</code>
                      <span style={{ color: "#30363d" }}>→</span>
                      {r.add_label && <span style={{ background: "#d2992222", border: "1px solid #d2992244", color: "#d29922", borderRadius: 12, padding: "2px 10px", fontSize: 12 }}>🏷️ {r.add_label}</span>}
                      {r.slack_notify && <span style={{ background: "#1a2f1a", border: "1px solid #3fb95033", color: "#3fb950", borderRadius: 12, padding: "2px 10px", fontSize: 12 }}>🔔 Slack</span>}
                    </div>
                    <button onClick={() => handleDeleteRule(r.id)} style={{ background: "transparent", border: "1px solid #f8514933", color: "#f85149", padding: "4px 12px", fontSize: 12, flexShrink: 0 }}>
                      Delete
                    </button>
                  </div>
                ))}

                {/* Add rule */}
                <div style={{ padding: "16px 20px", background: "#0d1117", borderTop: "1px solid #21262d" }}>
                  <div style={{ fontSize: 11, color: "#8b949e", marginBottom: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>New rule</div>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                    <select value={newRule.event_type} onChange={(e) => setNewRule({ ...newRule, event_type: e.target.value })} style={{ width: 130 }}>
                      <option value="issues">issues</option>
                      <option value="pull_request">pull_request</option>
                    </select>
                    <span style={{ color: "#8b949e", fontSize: 13 }}>if</span>
                    <select value={newRule.match_field} onChange={(e) => setNewRule({ ...newRule, match_field: e.target.value })} style={{ width: 100 }}>
                      <option value="title">title</option>
                      <option value="body">body</option>
                      <option value="author">author</option>
                    </select>
                    <span style={{ color: "#8b949e", fontSize: 13 }}>contains</span>
                    <input placeholder="e.g. bug" value={newRule.match_value} onChange={(e) => setNewRule({ ...newRule, match_value: e.target.value })} style={{ width: 120 }} />
                    <span style={{ color: "#8b949e", fontSize: 13 }}>→ label</span>
                    <input placeholder="e.g. bug" value={newRule.add_label} onChange={(e) => setNewRule({ ...newRule, add_label: e.target.value })} style={{ width: 100 }} />
                    <label style={{ display: "flex", alignItems: "center", gap: 6, color: "#c9d1d9", cursor: "pointer", fontSize: 13 }}>
                      <input type="checkbox" checked={newRule.slack_notify} onChange={(e) => setNewRule({ ...newRule, slack_notify: e.target.checked })} style={{ width: "auto", padding: 0 }} />
                      Slack
                    </label>
                    <button onClick={handleCreateRule} disabled={!newRule.match_value} style={{ background: newRule.match_value ? "#238636" : "#21262d", border: "1px solid rgba(240,246,252,0.1)", color: newRule.match_value ? "white" : "#8b949e", fontWeight: 600 }}>
                      Add rule
                    </button>
                  </div>
                </div>
              </div>

              {/* Event log */}
              <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, overflow: "hidden" }}>
                <div style={{ padding: "14px 20px", borderBottom: "1px solid #21262d", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontWeight: 600, color: "#f0f6fc", fontSize: 14 }}>📋 Event Log</span>
                    <span style={{ background: "#21262d", border: "1px solid #30363d", borderRadius: 10, padding: "1px 7px", fontSize: 12, color: "#8b949e" }}>{events.length}</span>
                  </div>
                  <span style={{ fontSize: 11, color: "#3fb950", display: "flex", alignItems: "center", gap: 5 }}>
                    <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#3fb950", display: "inline-block" }} />
                    Live · updates every 5s
                  </span>
                </div>
                {events.length === 0 ? (
                  <div style={{ padding: "40px 20px", color: "#8b949e", textAlign: "center", fontSize: 13 }}>
                    No events yet. Open an issue or PR on <strong style={{ color: "#c9d1d9" }}>{selected.name}</strong> to see events here.
                  </div>
                ) : (
                  <table>
                    <thead><tr>
                      <th style={{ paddingLeft: 20 }}>Received</th>
                      <th>Event</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr></thead>
                    <tbody>
                      {events.map((ev) => (
                        <tr key={ev.id}>
                          <td style={{ paddingLeft: 20, color: "#8b949e", whiteSpace: "nowrap", fontSize: 12 }}>{new Date(ev.received_at).toLocaleString()}</td>
                          <td><EventTypeBadge type={ev.event_type} action={ev.action} /></td>
                          <td><StatusBadge status={ev.status} /></td>
                          <td>{ev.actions.length === 0 ? <span style={{ color: "#8b949e", fontSize: 12 }}>—</span> : ev.actions.map((a, i) => <ActionChip key={i} {...a} />)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
