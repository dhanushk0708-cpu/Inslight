const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function readJson(response) {
  const data = await response.json();
  if (!response.ok) {
    const detail = data?.detail || data?.message || "Request failed";
    throw new Error(detail);
  }
  return data;
}

export const api = {
  baseUrl: API_BASE_URL,

  fetchHealth() {
    return fetch(`${API_BASE_URL}/api/health`).then(readJson);
  },

  query(question, conversationHistory) {
    return fetch(`${API_BASE_URL}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        conversation_history: conversationHistory,
      }),
    }).then(readJson);
  },

  deepDive() {
    return fetch(`${API_BASE_URL}/api/deep-dive`, {
      method: "POST",
    }).then(readJson);
  },

  whatIf(payload) {
    return fetch(`${API_BASE_URL}/api/what-if`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(readJson);
  },

  fetchAnomalies() {
    return fetch(`${API_BASE_URL}/api/anomalies`).then(readJson);
  },

  uploadCsv(file) {
    const formData = new FormData();
    formData.append("file", file);

    return fetch(`${API_BASE_URL}/api/upload`, {
      method: "POST",
      body: formData,
    }).then(readJson);
  },
};
