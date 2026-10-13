const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

export class ApiError extends Error {
  status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    let message = `The API returned ${response.status}.`;
    try {
      const body = (await response.json()) as { detail?: unknown; message?: string };
      const detail = body.detail;
      if (typeof detail === "string") message = detail;
      else if (detail && typeof detail === "object" && "message" in detail && typeof detail.message === "string") {
        message = detail.message;
      } else if (body.message) message = body.message;
    } catch {
      // Keep the status based message when the server did not return JSON.
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export function apiBaseUrl(): string {
  return API_BASE_URL;
}
