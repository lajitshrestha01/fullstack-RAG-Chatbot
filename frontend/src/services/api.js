const BASE_URL = import.meta.env.VITE_API_URL 

/**
 * upload a pdf file to the backend
 * Returns session_id, filename, pages, chunks_stored
 **/

export async function uploadPDF(file) {
    const formData = new FormData();
    formData.append("file", file); 

    const response = await fetch(`${BASE_URL}/api/v1/upload`, {
        method: "POST", 
        body: formData,

    });
    if(!response.ok){
        const error = await response.json(); 
        throw new Error(error.detail || "Upload failed");
    }

    return response.json()

}

/**
 * Send a questionto the backend for a given session. 
 * Retuns answer, sources, session_id. 
 */

export async function queryDocument(sessionId, question){
    const response = await fetch(`${BASE_URL}/api/v1/query`,{
        method: "POST", 
        headers: {
            "Content-Type": "application/json", 
        },
        body: JSON.stringify({
            session_id: sessionId, 
            question: question,
        }), 
    });

    if(!response.ok){ 
        const error = await response.json();
        throw new Error(error.detail || "query failed");
    }

    return response.json()
}