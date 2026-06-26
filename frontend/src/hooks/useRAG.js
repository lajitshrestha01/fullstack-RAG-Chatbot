import { useState, useCallback } from "react";
import { uploadPDF, queryDocument } from "../services/api";

/**
 * All RAG state and logic lives here.
 * Components stay dumb - they just call these functions and render state.
 */
export function useRAG() {
    const [status, setStatus] = useState("idle");
    // idle | uploading | ready | querying | error

    const [sessionId, setSessionId] = useState(null);
    const [uploadInfo, setUploadInfo] = useState(null);
    const [messages, setMessages] = useState([]);
    const [error, setError] = useState(null);

    const upload = useCallback(async (file) => {
        setStatus("uploading");
        setError(null);

        try {
            const result = await uploadPDF(file);
            setSessionId(result.session_id);
            setUploadInfo({
                filename: result.filename,
                pages: result.pages,
                chunks: result.chunks_stored,
            });
            setMessages([]);
            setStatus("ready");
        } catch (err) {
            setError(err.message);
            setStatus("error");
        }
    }, []);

    const query = useCallback(
        async (question) => {
            if (!sessionId) return;
            setStatus("querying");

            // Optimistically add user message immediately
            setMessages((prev) => [
                ...prev,
                { role: "user", content: question, sources: [] },
            ]);

            try {
                const result = await queryDocument(sessionId, question);
                setMessages((prev) => [
                    ...prev,
                    {
                        role: "assistant",
                        content: result.answer,
                        sources: result.sources,
                    },
                ]);
                setStatus("ready");
            } catch (err) {
                setError(err.message);
                setStatus("error");
            }
        },
        [sessionId]
    );

    const reset = useCallback(() => {
        setStatus("idle");
        setSessionId(null);
        setUploadInfo(null);
        setMessages([]);
        setError(null);
    }, []);

    return {
        status,
        sessionId,
        uploadInfo,
        messages,
        error,
        upload,
        query,
        reset,
    };
}