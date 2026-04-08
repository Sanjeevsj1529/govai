const tones = {
  completed: "status-badge status-badge--good",
  "in progress": "status-badge status-badge--warn",
  delayed: "status-badge status-badge--bad",
  idle: "status-badge status-badge--muted",
  busy: "status-badge status-badge--accent",
  overloaded: "status-badge status-badge--bad",
  online: "status-badge status-badge--good",
  offline: "status-badge status-badge--muted",
  running: "status-badge status-badge--good",
  paused: "status-badge status-badge--muted",
};

export default function StatusBadge({ status }) {
  const key = String(status || "").toLowerCase();
  return <span className={tones[key] || "status-badge"}>{status}</span>;
}
