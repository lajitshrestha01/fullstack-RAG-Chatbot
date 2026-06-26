import { useState } from "react";

/**
 * A single retrieved chunk shown as a citation under an assistant answer.
 * Collapsed by default; click to expand the full chunk text.
 *
 * source = { content, page, chunk_index, relevance_score }
 */
export default function SourceCard({ source }) {
  const [open, setOpen] = useState(false);

  const relevancePct = Math.round((source.relevance_score ?? 0) * 100);

  return (
    <div className={`source-card${open ? " source-card--open" : ""}`}>
      <button
        type="button"
        className="source-card__head"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="source-card__page">Page {source.page}</span>
        <span className="source-card__chunk">chunk #{source.chunk_index}</span>
        <span className="source-card__score" title="Relevance to your question">
          {relevancePct}% match
        </span>
        <span className="source-card__chevron" aria-hidden="true">
          {open ? "▾" : "▸"}
        </span>
      </button>

      {open && <p className="source-card__body">{source.content}</p>}
    </div>
  );
}
