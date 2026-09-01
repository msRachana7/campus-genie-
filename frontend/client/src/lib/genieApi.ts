export type Citation = { title: string; url: string };
export type HistoryMessage = { role: "user" | "assistant"; content: string };
export type ChatMessage = HistoryMessage & {
  id: string;
  citations?: Citation[];
};

const TOKEN_KEY = "campus_genie_access_token";
export const GENIE_AUTH_EVENT = "campus-genie-auth-change";

// This is your app's login JWT, NOT the Databricks token.
export function saveGenieAccessToken(token: string | null) {
  if (token) sessionStorage.setItem(TOKEN_KEY, token);
  else sessionStorage.removeItem(TOKEN_KEY);
  window.dispatchEvent(new Event(GENIE_AUTH_EVENT));
}

export function getGenieAccessToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export async function requestGenie(
  messages: HistoryMessage[],
  token: string,
  signal: AbortSignal,
): Promise<{ answer: string; citations: Citation[] }> {
  // Only a public backend URL is allowed in a VITE_ variable.
  const base = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
  const response = await fetch(`${base}/api/genie/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ messages }),
    signal,
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Your session expired. Please sign out and sign in again.");
    }
    throw new Error(
      typeof body?.detail === "string"
        ? body.detail
        : `Chat request failed (${response.status}).`,
    );
  }
  if (typeof body?.answer !== "string" || !body.answer.trim()) {
    throw new Error("Genie returned an empty answer. Please try again.");
  }
  return { answer: body.answer, citations: Array.isArray(body.citations) ? body.citations : [] };
}
