import { API_URL, getSlackInstallUrl } from "../lib/api";
import { BotLogo } from "./logo";

const GH_ICON = (
  <svg height="52" viewBox="0 0 16 16" width="52" fill="#f0f6fc" aria-hidden="true">
    <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
  </svg>
);

export default function Home() {
  return (
    <main style={{
      display: "flex", flexDirection: "column", alignItems: "center",
      justifyContent: "center", minHeight: "100vh", padding: 24,
      background: "#0d1117",
    }}>
      {/* Hero */}
      <div style={{ textAlign: "center", maxWidth: 600, marginBottom: 40 }}>
        <div style={{ marginBottom: 20 }}><BotLogo size={80} /></div>
        <h1 style={{ margin: "0 0 12px", fontSize: 36, fontWeight: 700, color: "#f0f6fc", lineHeight: 1.2 }}>
          GitHub Automation Bot
        </h1>
        <p style={{ margin: 0, fontSize: 16, color: "#8b949e", lineHeight: 1.7 }}>
          Connect your repos. Set rules. Let the bot handle the rest —
          auto-label issues, post comments, and fire Slack alerts the moment something matches.
        </p>
      </div>

      {/* Sign in card */}
      <div style={{
        background: "#161b22", border: "1px solid #30363d", borderRadius: 12,
        padding: "32px 40px", maxWidth: 420, width: "100%", textAlign: "center",
        boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
      }}>
        <h2 style={{ margin: "0 0 8px", fontSize: 20, fontWeight: 600, color: "#f0f6fc" }}>
          Welcome back
        </h2>
        <p style={{ margin: "0 0 24px", color: "#8b949e", fontSize: 13, lineHeight: 1.6 }}>
          Sign in with your GitHub account to access your dashboard.
        </p>
        <a
          href={`${API_URL}/auth/login`}
          style={{
            display: "inline-flex", alignItems: "center", gap: 10,
            background: "#238636", color: "#fff", padding: "10px 24px",
            borderRadius: 6, fontWeight: 600, fontSize: 15,
            border: "1px solid rgba(240,246,252,0.1)",
            textDecoration: "none", width: "100%",
            justifyContent: "center", boxSizing: "border-box",
          }}
        >
          <svg height="18" viewBox="0 0 16 16" width="18" fill="white">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
          </svg>
          Continue with GitHub
        </a>
      </div>

      <div style={{
        marginTop: 16,
        display: "flex",
        flexWrap: "wrap",
        gap: 12,
        justifyContent: "center",
      }}>
        <a
          href={getSlackInstallUrl()}
          target="_blank"
          rel="noreferrer"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 10,
            background: "#4a154b",
            color: "#fff",
            padding: "10px 18px",
            borderRadius: 6,
            fontWeight: 600,
            fontSize: 14,
            textDecoration: "none",
            border: "1px solid rgba(240,246,252,0.1)",
          }}
        >
          <img
            alt="Add to Slack"
            height={20}
            width={69}
            src="https://platform.slack-edge.com/img/add_to_slack.png"
            srcSet="https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x"
          />
          Add to Slack
        </a>
      </div>

      {/* Feature pills */}
      <div style={{ display: "flex", gap: 12, marginTop: 32, flexWrap: "wrap", justifyContent: "center" }}>
        {[
          {
            icon: (
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke="#d29922" strokeWidth="1.8" strokeLinejoin="round" fill="#d2992222"/>
              </svg>
            ),
            label: "Instant webhooks",
            desc: "Real-time event processing",
            accent: "#d29922",
          },
          {
            icon: (
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="3" width="18" height="18" rx="4" stroke="#58a6ff" strokeWidth="1.8" fill="#58a6ff22"/>
                <path d="M7 12l3 3 7-7" stroke="#58a6ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            ),
            label: "Auto-labeling",
            desc: "Label issues automatically",
            accent: "#58a6ff",
          },
          {
            icon: (
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" stroke="#3fb950" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" fill="#3fb95022"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0" stroke="#3fb950" strokeWidth="1.8" strokeLinecap="round"/>
              </svg>
            ),
            label: "Slack alerts",
            desc: "Notify your team instantly",
            accent: "#3fb950",
          },
          {
            icon: (
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <rect x="4" y="2" width="16" height="20" rx="3" stroke="#bc8cff" strokeWidth="1.8" fill="#bc8cff22"/>
                <path d="M8 7h8M8 11h8M8 15h5" stroke="#bc8cff" strokeWidth="1.8" strokeLinecap="round"/>
              </svg>
            ),
            label: "Event log",
            desc: "Full audit trail",
            accent: "#bc8cff",
          },
        ].map(({ icon, label, desc, accent }) => (
          <div key={label} style={{
            background: "#161b22", border: `1px solid ${accent}33`, borderRadius: 10,
            padding: "16px 20px", textAlign: "center", minWidth: 130,
            boxShadow: `0 0 12px ${accent}11`,
          }}>
            <div style={{ display: "flex", justifyContent: "center", marginBottom: 8 }}>{icon}</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#f0f6fc", marginBottom: 3 }}>{label}</div>
            <div style={{ fontSize: 11, color: "#8b949e" }}>{desc}</div>
          </div>
        ))}
      </div>
    </main>
  );
}
