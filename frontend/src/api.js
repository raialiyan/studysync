
const API_URL = "http://127.0.0.1:8000";

export function getToken() {
  return sessionStorage.getItem("studysync_token");
}

export function saveToken(token) {
  sessionStorage.setItem("studysync_token", token);
}

export function logout() {
  sessionStorage.removeItem("studysync_token");
}

export async function apiRequest(path, options = {}) {
  const token = getToken();

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;

    try {
      const error = await response.json();
      if (typeof error.detail === "string") {
        message = error.detail;
      }
    } catch {
      // Keep the default error message
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}
