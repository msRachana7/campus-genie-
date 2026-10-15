export type CampusUser = {
  user_id: string;
  student_id: string;
  usn: string;
  email: string;
};

const TOKEN_KEY = "campus_genie_access_token";
export const AUTH_EVENT = "campus-genie-auth-change";

export function accessToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function currentUser(): CampusUser | null {
  try {
    return JSON.parse(sessionStorage.getItem("campus_genie_user") ?? "null");
  } catch {
    return null;
  }
}

export function saveSession(token: string, user: CampusUser) {
  sessionStorage.setItem(TOKEN_KEY, token);
  sessionStorage.setItem("campus_genie_user", JSON.stringify(user));
  localStorage.setItem("user", JSON.stringify(user));
  localStorage.removeItem("access_token");
  window.dispatchEvent(new Event(AUTH_EVENT));
}

export function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem("campus_genie_user");
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
  window.dispatchEvent(new Event(AUTH_EVENT));
}

export async function authFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const base = (
    import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/$/, "");
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const token = accessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 45000);
  let response: Response;
  try {
    response = await fetch(`${base}${path}`, {
      ...options,
      headers,
      signal: options.signal ?? controller.signal,
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("The server took too long. Please try again.");
    }
    throw new Error(
      "Cannot reach the backend. Check that FastAPI is running on the configured backend URL.",
    );
  } finally {
    window.clearTimeout(timer);
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && path !== "/api/auth/login") clearSession();
    const detail =
      typeof data?.detail === "string"
        ? data.detail
        : Array.isArray(data?.detail)
          ? data.detail.map((item: { msg: string }) => item.msg).join(" ")
          : `Request failed (${response.status}).`;
    throw new Error(detail);
  }
  return data as T;
}
