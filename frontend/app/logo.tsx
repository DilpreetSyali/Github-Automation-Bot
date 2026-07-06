export function BotLogo({ size = 40 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="GitHub Automation Bot"
    >
      {/* Outer circle */}
      <circle cx="32" cy="32" r="30" fill="#161b22" stroke="#30363d" strokeWidth="2" />

      {/* Bot head */}
      <rect x="18" y="16" width="28" height="22" rx="6" fill="#21262d" stroke="#58a6ff" strokeWidth="1.5" />

      {/* Eyes */}
      <circle cx="25" cy="26" r="3.5" fill="#58a6ff" />
      <circle cx="39" cy="26" r="3.5" fill="#58a6ff" />
      <circle cx="26" cy="25" r="1.2" fill="#0d1117" />
      <circle cx="40" cy="25" r="1.2" fill="#0d1117" />

      {/* Antenna */}
      <line x1="32" y1="16" x2="32" y2="10" stroke="#58a6ff" strokeWidth="2" strokeLinecap="round" />
      <circle cx="32" cy="8" r="2.5" fill="#3fb950" />

      {/* Mouth — smile */}
      <path d="M25 32 Q32 37 39 32" stroke="#58a6ff" strokeWidth="1.5" strokeLinecap="round" fill="none" />

      {/* Body */}
      <rect x="24" y="38" width="16" height="10" rx="3" fill="#21262d" stroke="#30363d" strokeWidth="1.5" />

      {/* Lightning bolt */}
      <path d="M34 42 L30 47 L33 47 L30 52 L36 45 L33 45 Z" fill="#d29922" />

      {/* Arms */}
      <rect x="12" y="38" width="10" height="5" rx="2.5" fill="#21262d" stroke="#30363d" strokeWidth="1.5" />
      <rect x="42" y="38" width="10" height="5" rx="2.5" fill="#21262d" stroke="#30363d" strokeWidth="1.5" />
    </svg>
  );
}
