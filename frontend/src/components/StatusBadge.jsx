/**
 * Small pill that reflects the current RAG status.
 * Purely presentational — maps a status string to a label + tone.
 */

const STATUS_MAP = {
  idle: { label: "Ready to upload", tone: "neutral" },
  uploading: { label: "Processing PDF…", tone: "busy" },
  ready: { label: "Document ready", tone: "ok" },
  querying: { label: "Thinking…", tone: "busy" },
  error: { label: "Something went wrong", tone: "error" },
};

export default function StatusBadge({ status }) {
  const { label, tone } = STATUS_MAP[status] ?? STATUS_MAP.idle;
  const busy = tone === "busy";

  return (
    <span
      className={`status-badge status-badge--${tone}`}
      role="status"
      aria-live="polite"
    >
      <span
        className={`status-dot${busy ? " status-dot--pulse" : ""}`}
        aria-hidden="true"
      />
      {label}
    </span>
  );
}
