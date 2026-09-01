import { useCallback, useEffect, useRef, useState } from "react";
import { accessToken, authFetch } from "../lib/campusAuth";
import { toast } from "sonner";

export type HomePost = {
  id: string; initials: string; name: string; meta: string; color: string;
  title: string; body: string; tags: string[]; skills_required: string[];
  deadline: string | null; interested: boolean; matches_you: boolean;
};
export type HomeDashboard = {
  generated_at: string; first_name: string; date_label: string; greeting: string;
  content_status: "ok" | "unavailable"; content_fetched_at: string | null;
  interest_status: "ok" | "unavailable"; partial: boolean; feed_limited: boolean;
  weather: { temperature_c: number | null; condition: string; location: string; is_day: boolean; status: string };
  pulse: null | { headline: string; detail: string; active_count: number; ai_event_count: number;
    previous_ai_event_count: number; event_days: number[]; ai_days: number[]; has_event_dates: boolean;
    week_start: string; week_end: string };
  shortcuts: { resource_count: number | null; matching_posts: number | null };
  posts: HomePost[];
  up_next: null | { id: string; title: string; kind: "event" | "deadline"; date: string; day: string; month: string; time: string; location: string };
  archive: null | { title: string; year: number };
};

export function indiaClock(now: Date) {
  const options = { timeZone: "Asia/Kolkata" };
  const hour = Number(new Intl.DateTimeFormat("en-GB", { ...options, hour: "numeric", hourCycle: "h23" }).format(now));
  const period = hour >= 5 && hour < 12 ? "morning" : hour < 17 && hour >= 12 ? "afternoon" : hour >= 17 && hour < 21 ? "evening" : "night";
  return {
    date: new Intl.DateTimeFormat("en-IN", { ...options, weekday: "long", day: "numeric", month: "long" }).format(now),
    period,
    weekday: new Intl.DateTimeFormat("en-IN", { ...options, weekday: "long" }).format(now),
  };
}

export function useHomeDashboard(enabled: boolean) {
  const [data, setData] = useState<HomeDashboard | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [revision, setRevision] = useState(0);
  const [now, setNow] = useState(new Date());
  const [saving, setSaving] = useState<Set<string>>(new Set());
  const pending = useRef(new Set<string>());
  const interestEdits = useRef(new Map<string, boolean>());
  const refresh = useCallback(() => setRevision(n => n + 1), []);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 30_000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!enabled) {
      setData(null); setError(""); setLoading(false); setSaving(new Set());
      pending.current.clear(); interestEdits.current.clear();
      return;
    }
    let disposed = false, busy = false;
    const token = accessToken();
    const load = async () => {
      if (busy || disposed || document.visibilityState === "hidden") return;
      busy = true;
      setLoading(true);
      try {
        const result = await authFetch<HomeDashboard>("/api/home");
        if (!disposed && accessToken() === token) {
          // A refresh started before a save must not undo the completed save.
          result.posts = result.posts.map(post => interestEdits.current.has(post.id)
            ? { ...post, interested: interestEdits.current.get(post.id)! } : post);
          setData(result); setError(""); setNow(new Date());
        }
      } catch (cause) {
        if (!disposed && accessToken() === token) setError(cause instanceof Error ? cause.message : "Home could not be loaded.");
      } finally {
        busy = false;
        if (!disposed && accessToken() === token) setLoading(false);
      }
    };
    void load();
    const interval = window.setInterval(() => void load(), 300_000);
    const focus = () => void load();
    window.addEventListener("focus", focus);
    window.addEventListener("online", focus);
    document.addEventListener("visibilitychange", focus);
    return () => {
      disposed = true;
      window.clearInterval(interval);
      window.removeEventListener("focus", focus);
      window.removeEventListener("online", focus);
      document.removeEventListener("visibilitychange", focus);
    };
  }, [enabled, revision]);

  const toggleInterest = async (post: HomePost) => {
    if (pending.current.has(post.id)) return;
    const token = accessToken();
    pending.current.add(post.id); setSaving(new Set(pending.current));
    try {
      const result = await authFetch<{ interested: boolean }>(`/api/home/interests/${encodeURIComponent(post.id)}`, {
        method: post.interested ? "DELETE" : "PUT",
      });
      if (accessToken() !== token) return;
      interestEdits.current.set(post.id, result.interested);
      setData(current => current && ({ ...current, posts: current.posts.map(item => item.id === post.id ? { ...item, interested: result.interested } : item) }));
    } catch (cause) {
      if (accessToken() === token) toast.error(cause instanceof Error ? cause.message : "Could not save your interest.");
    } finally {
      if (accessToken() === token) {
        pending.current.delete(post.id); setSaving(new Set(pending.current));
      }
    }
  };
  return { data, error, loading, refresh, clock: indiaClock(now), saving, toggleInterest };
}

export type HomeState = ReturnType<typeof useHomeDashboard>;
