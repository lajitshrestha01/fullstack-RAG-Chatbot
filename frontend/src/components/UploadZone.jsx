import { useCallback, useRef, useState } from "react";

const MAX_BYTES = 10 * 1024 * 1024; // mirrors backend MAX_UPLOAD_SIZE (10MB)

/**
 * Drag-and-drop / click-to-browse zone for a single PDF.
 * Does light client-side validation, then hands the File to `onUpload`.
 *
 * props: onUpload(file), status, error
 */
export default function UploadZone({ onUpload, status, error }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState(null);

  const busy = status === "uploading";

  const validateAndUpload = useCallback(
    (file) => {
      if (!file) return;
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setLocalError("Only PDF files are accepted.");
        return;
      }
      if (file.size > MAX_BYTES) {
        setLocalError("File exceeds the 10 MB limit.");
        return;
      }
      setLocalError(null);
      onUpload(file);
    },
    [onUpload]
  );

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragging(false);
      if (busy) return;
      validateAndUpload(e.dataTransfer.files?.[0]);
    },
    [busy, validateAndUpload]
  );

  const handleDragOver = useCallback(
    (e) => {
      e.preventDefault();
      if (!busy) setDragging(true);
    },
    [busy]
  );

  const shownError = localError || error;

  return (
    <div className="upload">
      <button
        type="button"
        className={`dropzone${dragging ? " dropzone--active" : ""}${
          busy ? " dropzone--busy" : ""
        }`}
        onClick={() => !busy && inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={() => setDragging(false)}
        disabled={busy}
        aria-label="Upload a PDF document"
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="dropzone__input"
          onChange={(e) => validateAndUpload(e.target.files?.[0])}
          disabled={busy}
        />

        {busy ? (
          <>
            <span className="spinner" aria-hidden="true" />
            <p className="dropzone__title">Processing your PDF…</p>
            <p className="dropzone__hint">
              Extracting pages, chunking and embedding. This can take a moment.
            </p>
          </>
        ) : (
          <>
            <span className="dropzone__icon" aria-hidden="true">
              ⬆
            </span>
            <p className="dropzone__title">
              Drop a PDF here, or <span className="link">browse</span>
            </p>
            <p className="dropzone__hint">Up to 50 pages · max 10 MB</p>
          </>
        )}
      </button>

      {shownError && (
        <p className="upload__error" role="alert">
          {shownError}
        </p>
      )}
    </div>
  );
}
