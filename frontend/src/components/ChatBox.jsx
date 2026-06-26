import { useEffect, useRef, useState } from "react";
import SourceCard from "./SourceCard";

/**
 * The conversation surface: scrollable message list + question input.
 *
 * props: messages, onSend(question), status, error
 */
export default function ChatBox({ messages, onSend, status, error }) {
  const [draft, setDraft] = useState("");
  const endRef = useRef(null);

  const querying = status === "querying";

  // Keep the latest message (or typing indicator) in view.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, querying]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const question = draft.trim();
    if (!question || querying) return;
    onSend(question);
    setDraft("");
  };

  return (
    <div className="chat">
      <div className="chat__scroll">
        {messages.length === 0 && !querying && (
          <div className="chat__empty">
            <p className="chat__empty-title">Ask anything about your document</p>
            <p className="chat__empty-hint">
              Answers are grounded in the PDF and cite the exact page they came
              from.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`bubble bubble--${msg.role}`}>
            <div className="bubble__content">{msg.content}</div>

            {msg.role === "assistant" && msg.sources?.length > 0 && (
              <div className="bubble__sources">
                <p className="bubble__sources-label">Sources</p>
                {msg.sources.map((source, si) => (
                  <SourceCard key={si} source={source} />
                ))}
              </div>
            )}
          </div>
        ))}

        {querying && (
          <div className="bubble bubble--assistant">
            <div className="typing" aria-label="Assistant is typing">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}

        {status === "error" && error && (
          <p className="chat__error" role="alert">
            {error}
          </p>
        )}

        <div ref={endRef} />
      </div>

      <form className="composer" onSubmit={handleSubmit}>
        <input
          type="text"
          className="composer__input"
          placeholder="Ask a question about the document…"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          disabled={querying}
          aria-label="Your question"
        />
        <button
          type="submit"
          className="composer__send"
          disabled={querying || !draft.trim()}
        >
          {querying ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
