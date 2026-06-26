import { useRAG } from "./hooks/useRAG";
import UploadZone from "./components/UploadZone";
import ChatBox from "./components/ChatBox";
import StatusBadge from "./components/StatusBadge";
import "./App.css";

function App() {
  const { status, uploadInfo, messages, error, upload, query, reset } = useRAG();

  // Once a document is processed we have upload info to show the chat against.
  const hasDocument = Boolean(uploadInfo);

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="brand__mark" aria-hidden="true">
            ◆
          </span>
          <span className="brand__name">DocChat</span>
        </div>

        <div className="app-header__right">
          <StatusBadge status={status} />
          {hasDocument && (
            <button type="button" className="ghost-btn" onClick={reset}>
              New document
            </button>
          )}
        </div>
      </header>

      <main className="app-main">
        {hasDocument ? (
          <>
            <div className="doc-bar">
              <span className="doc-bar__icon" aria-hidden="true">
                📄
              </span>
              <span className="doc-bar__name" title={uploadInfo.filename}>
                {uploadInfo.filename}
              </span>
              <span className="doc-bar__meta">
                {uploadInfo.pages} pages · {uploadInfo.chunks} chunks
              </span>
            </div>

            <ChatBox
              messages={messages}
              onSend={query}
              status={status}
              error={error}
            />
          </>
        ) : (
          <section className="hero">
            <h1 className="hero__title">Chat with your PDF</h1>
            <p className="hero__subtitle">
              Upload a document and ask questions. Every answer is grounded in
              the text and cites the page it came from.
            </p>
            <UploadZone onUpload={upload} status={status} error={error} />
          </section>
        )}
      </main>

      <footer className="app-footer">
        Answers are generated from your document only · sessions are in-memory
      </footer>
    </div>
  );
}

export default App;
