const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail : "Request failed";
    throw new Error(detail);
  }
  return data;
}

export const api = {
  submitMessage: (payload) => request("/messages", {
    method: "POST",
    body: JSON.stringify(payload),
  }),
  getMessages: (params = {}) => {
    const query = new URLSearchParams(params);
    return request(`/messages?${query.toString()}`);
  },
  getStats: () => request("/dashboard/stats"),
  updateReview: (id, payload) => request(`/messages/${id}/review`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  }),
};
