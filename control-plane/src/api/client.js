const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function apiRequest(path, { token, ...options } = {}) {
  const headers = new Headers(options.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (options.body != null && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new Error("Cannot connect to the server.");
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const detail = errorData?.detail;

    const message =
      typeof detail === "string"
        ? detail
        : detail != null
          ? JSON.stringify(detail)
          : `Request failed (HTTP ${response.status})`;

    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}
