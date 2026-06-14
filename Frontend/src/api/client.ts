const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8001/api";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers ?? {}),
      },
    });
  } catch (error) {
    throw new Error(`Backend is not reachable at ${API_BASE}. Start FastAPI on port 8001, then retry.`);
  }

  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      message = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail ?? payload);
    } catch {
      // Keep HTTP status message.
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export { API_BASE, request };
