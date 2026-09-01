import { useEffect, useState } from "react";
import { ArrowUpRight, BookOpen, CalendarDays, ChevronRight, CircleHelp, Plus, Share2, Sparkles, UsersRound, Zap } from "lucide-react";
import { toast } from "sonner";
import type { HomePost, HomeState } from "../hooks/useHomeDashboard";

type Props = { home: HomeState; setActiveTab: (tab: string) => void; ask: (question: string) => void; name?: string };
const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function WeekBars({ values }: { values: number[] }) {
  const max = Math.max(1, ...values);
  return <><div className="tiny-bars" role="img" aria-label={values.map((n, i) => `${DAYS[i]}: ${n} scheduled events`).join(", ")}>
    {values.map((value, i) => <i key={DAYS[i]} title={`${DAYS[i]}: ${value}`} style={{ height: `${value / max * 100}%` }} />)}
  </div><div style={{ display: "flex", justifyContent: "space-between", fontSize: 10 }} aria-hidden="true">{DAYS.map(day => <span key={day}>{day}</span>)}</div></>;
}

export function LivePostCard({ post, home }: { post: HomePost; home: HomeState }) {
  const selected = new URLSearchParams(window.location.search).get("post") === post.id;
  const tags = Array.from(new Set([...post.tags, ...post.skills_required]));
  const share = async () => {
    const url = new URL(window.location.href);
    url.searchParams.set("post", post.id); url.hash = "";
    try {
      if (navigator.share) await navigator.share({ title: post.title, text: post.body, url: url.href });
      else {
        if (!navigator.clipboard) throw new Error("Clipboard unavailable. Copy the page address to share it.");
        await navigator.clipboard.writeText(url.href); toast.success("Post link copied.");
      }
    } catch (cause) {
      if (!(cause instanceof Error && cause.name === "AbortError")) toast.error(cause instanceof Error ? cause.message : "Could not share this post.");
    }
  };
  useEffect(() => { if (selected) document.getElementById(`post-${post.id}`)?.scrollIntoView({ block: "center" }); }, [selected, post.id]);
  return <article className="post-card" id={`post-${post.id}`} style={selected ? { outline: "2px solid #e67e45" } : undefined}>
    <div className={`post-avatar ${post.color}`}>{post.initials}</div><div className="post-main">
      <div className="post-meta"><b>{post.name}</b><span>{post.meta}</span></div>
      <h3>{post.title}</h3><p style={{ whiteSpace: "pre-wrap" }}>{post.body}</p>
      <div className="tag-row">{tags.map(tag => <span key={tag} className={post.skills_required.includes(tag) ? "skill-tag" : ""}>#{tag}</span>)}</div>
      {post.deadline && <div className="post-deadline">Deadline · {new Date(`${post.deadline}T00:00:00+05:30`).toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata", day: "numeric", month: "short", year: "numeric" })}</div>}
      <div className="post-actions"><button className={`interested-action ${post.interested ? "is-interested" : ""}`} aria-pressed={post.interested}
        disabled={home.saving.has(post.id) || home.data?.interest_status !== "ok"} onClick={() => void home.toggleInterest(post)}>
        <Sparkles size={16} />{home.saving.has(post.id) ? "Saving…" : post.interested ? "Interested ✓" : "Interested?"}
      </button><button onClick={() => void share()}><Share2 size={15} /> Share</button></div>
    </div>
  </article>;
}

export function HomeStatus({ home }: { home: HomeState }) {
  const issue = home.error || (home.data?.content_status === "unavailable" ? "Campus posts are temporarily unavailable. Try refreshing in a moment." : "");
  return <>
    {issue && <p role="alert">{issue} <button className="text-button" disabled={home.loading} onClick={home.refresh}>Retry</button></p>}
    {home.data?.interest_status === "unavailable" && <p role="status">Interested selections are temporarily unavailable.</p>}
    {home.data?.partial && <p role="status">Showing counts from the 5,000 loaded records.</p>}
    {home.loading && !home.data && <p role="status">Loading your campus…</p>}
  </>;
}

export default function LiveHomeView({ home, setActiveTab, ask, name }: Props) {
  const { data, clock } = home;
  const [mascotMissing, setMascotMissing] = useState(false);
  const firstName = name?.trim().split(/\s+/)[0] || data?.first_name || "there";
  const pulse = data?.pulse;
  const count = data?.shortcuts.matching_posts;
  const next = data?.up_next;
  const available = data?.content_status === "ok";
  const selected = data?.posts.find(post => post.id === new URLSearchParams(window.location.search).get("post"));
  const feed = selected ? [selected, ...(data?.posts.filter(post => post.id !== selected.id) ?? []).slice(0, 1)] : data?.posts.slice(0, 2) ?? [];
  const headline = pulse?.headline || (available ? "Explore campus updates." : "Campus updates unavailable.");
  return <div className="page-content page-home">
    <section className="welcome-row">
      <div className="welcome-copy"><div className="eyebrow"><span className="eyebrow-pin">✦</span> {`${clock.weekday} ${clock.period}, ${firstName}`.toUpperCase()}</div>
        <h1>Hi {firstName}<span className="title-period">.</span><br /><em>Your campus has a lot<br className="desktop-only" /> going on.</em></h1>
        <p className="lede">Let’s make it findable. Ask about the fest, the syllabus, or the friend you haven’t met yet.</p>
        <div className="welcome-actions"><button className="primary-button" onClick={() => setActiveTab("genie")}><Sparkles size={16} /> Ask Genie <ArrowUpRight size={15} /></button>
        <button className="ghost-button" onClick={() => setActiveTab("community")}>See what’s moving <ChevronRight size={15} /></button></div>
      </div>
      <div className="genie-card"><div className="genie-halo" />{mascotMissing
        ? <Sparkles size={110} aria-label="Campus Genie" style={{ position: "relative", margin: "60px auto", color: "#e67e45" }} />
        : <img src="/manus-storage/campus-genie-orb_df60dbe3.png" alt="Campus Genie mascot" onError={() => setMascotMissing(true)} />}
        <div className="genie-note"><b>Ask your campus a question</b><small>{count == null ? "Explore with Genie" : `${count} matching posts${data?.partial ? " in loaded data" : " for you"}`}</small></div>
      </div>
      <div className="weather-card"><span className="weather-icon">{data?.weather.is_day === false ? "☾" : "☼"}</span><div>
        <b>{data?.weather.temperature_c == null ? "—" : `${data.weather.temperature_c}°`}</b>
        <span>{data?.weather.condition || "Loading weather"} · Basavanagudi</span>
        <a href="https://open-meteo.com/" target="_blank" rel="noreferrer" style={{ fontSize: 9 }}>Weather: Open-Meteo</a>
      </div></div>
    </section>
    <HomeStatus home={home} />
    <button className="pulse-spotlight" onClick={() => setActiveTab("pulse")}>
      <div className="spotlight-copy"><div className="spotlight-label"><span className="eyebrow-pin">✦</span> CAMPUS PULSE · THIS WEEK</div>
        <h2>{headline}</h2><p>{pulse?.detail || "Campus information will appear when the data connection is available."}</p>
        <span className="spotlight-cta">Explore the pulse <ArrowUpRight size={15} /></span></div>
      <div className="spotlight-orbit"><span className="orbit-pulse pulse-a" /><span className="orbit-pulse pulse-b" /><b>{pulse?.active_count ?? "—"}</b><small>active posts</small></div>
      <div className="spotlight-stamp">CAMPUS DATA<br /><b>SHARED POSTS</b></div>
    </button>
    <div className="section-heading"><div><span className="section-kicker">YOUR SHORTCUTS</span><h2>Pick up where you left off</h2></div><button className="text-button" onClick={() => setActiveTab("resources")}>Open library <ArrowUpRight size={14} /></button></div>
    <section className="shortcut-grid">
      <button className="shortcut-card shortcut-yellow" onClick={() => setActiveTab("resources")}><div className="card-icon"><BookOpen size={19} /></div><div><b>Notes & PYQs</b><span>{data?.shortcuts.resource_count == null ? "Browse shared notes & PYQs" : `${data.shortcuts.resource_count} shared resources`}</span></div><ChevronRight size={18} /></button>
      <button className="shortcut-card shortcut-lilac" onClick={() => setActiveTab("community")}><div className="card-icon"><UsersRound size={19} /></div><div><b>Find your people</b><span>{count == null ? "Explore campus posts" : `${count} posts match your skills or interests`}</span></div><ChevronRight size={18} /></button>
      <button className="shortcut-card shortcut-sage" onClick={() => setActiveTab("pulse")}><div className="card-icon"><Zap size={19} /></div><div><b>Campus Pulse</b><span>{pulse?.has_event_dates ? `${pulse.ai_event_count} AI events this week` : "Explore campus activity"}</span></div><ChevronRight size={18} /></button>
    </section>
    <div className="content-columns"><section className="feed-column">
      <div className="section-heading compact"><div><span className="section-kicker">FROM THE QUAD</span><h2>Worth knowing today</h2></div><button className="round-plus" aria-label="Open community" onClick={() => setActiveTab("community")}><Plus size={17} /></button></div>
      {feed.map(post => <LivePostCard key={post.id} post={post} home={home} />)}
      {available && feed.length === 0 && <div className="empty-state"><b>No active campus posts yet.</b><span>New shared posts will appear here after your data pipeline refreshes.</span></div>}
      <button className="load-more" onClick={() => setActiveTab("community")}>View the whole community <ArrowUpRight size={14} /></button>
    </section><aside className="insight-column">
      <div className="section-heading compact"><div><span className="section-kicker">A LITTLE SIGNAL</span><h2>Campus, right now</h2></div></div>
      <div className="pulse-card"><div className="pulse-card-top"><div className="signal-icon"><Zap size={17} /></div><span className="live-label">{available && !home.error ? "THIS WEEK" : "UNAVAILABLE"}</span></div>
        <h3>{headline}</h3><p>{pulse?.detail || "Try refreshing shortly."}</p>
        {pulse?.has_event_dates && <WeekBars values={pulse.event_days} />}
        <button onClick={() => setActiveTab("pulse")}>Explore the pulse <ArrowUpRight size={14} /></button></div>
      <div className="upcoming-card">{next ? <><div className="upcoming-date"><b>{next.day}</b><span>{next.month}</span></div><div><span className="section-kicker">{next.kind === "event" ? "UP NEXT" : "NEXT DEADLINE"}</span><b>{next.title}</b><small>{next.kind === "event" ? `${next.location} · ${next.time}` : `Deadline · ${next.date}`}</small></div><CalendarDays size={18} /></>
        : <div><span className="section-kicker">UP NEXT</span><b>{available ? "No upcoming dates listed" : "Upcoming dates unavailable"}</b></div>}</div>
      <button className="archive-teaser" onClick={() => ask(data?.archive ? `Tell me about this past campus post: ${data.archive.title} (${data.archive.year}). Use the available campus data.` : "What past campus events are available in the archive?")}>
        <div><span className="section-kicker">FROM THE ARCHIVE</span><b>{data?.archive?.title || "Explore past campus events"}</b><span>Ask Genie about the archive <ArrowUpRight size={13} /></span></div></button>
    </aside></div>
    <div className="privacy-note"><CircleHelp size={14} /> Pulse counts shared campus listings. Interested selections are private to your account.</div>
    <p style={{ fontSize: 11, opacity: .75 }}>{data?.content_fetched_at ? `Data fetched ${new Date(data.content_fetched_at).toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit" })} IST. ` : ""}Refreshes every 5 minutes while this page is open. <button className="text-button" disabled={home.loading} onClick={home.refresh}>{home.loading ? "Refreshing…" : "Refresh now"}</button></p>
  </div>;
}

export function LivePulseView({ home }: { home: HomeState }) {
  const pulse = home.data?.pulse;
  return <div className="page-content pulse-page"><HomeStatus home={home} />
    <div className="section-heading"><div><span className="section-kicker">CAMPUS PULSE · THIS WEEK</span><h1>{pulse?.headline || "Campus Pulse"}</h1><p>{pulse?.detail || "Connect your shared campus data to see this week’s activity."}</p></div></div>
    {pulse && <><div className="pulse-stat-row"><div><b>{pulse.active_count}</b><span>active campus posts</span></div><div><b>{pulse.has_event_dates ? pulse.ai_event_count : "—"}</b><span>AI events this week</span></div><div><b>{pulse.has_event_dates ? pulse.previous_ai_event_count : "—"}</b><span>AI events last week</span></div></div>
      {pulse.has_event_dates && <div className="pulse-card"><h3>Scheduled events this week</h3><p>{pulse.week_start} to {pulse.week_end}</p><WeekBars values={pulse.event_days} /></div>}</>}
    <p>Counts use public campus listings and scheduled event dates. They do not measure student moods, private conversations, or browsing activity.</p>
  </div>;
}

export function LiveCommunityView({ home }: { home: HomeState }) {
  const [query, setQuery] = useState("");
  const posts = (home.data?.posts || []).filter(post => `${post.title} ${post.body} ${post.tags.join(" ")} ${post.skills_required.join(" ")}`.toLowerCase().includes(query.toLowerCase()));
  return <div className="page-content community-page"><div className="section-heading"><div><span className="section-kicker">FROM THE QUAD</span><h1>Find your people.</h1><p>Active posts from your campus data, with your skills and interests matched first.</p></div></div>
    <HomeStatus home={home} /><label>Search these posts<div className="composer-input"><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Python, research, clubs…" /></div></label>
    {posts.map(post => <LivePostCard key={post.id} post={post} home={home} />)}
    {home.data?.content_status === "ok" && posts.length === 0 && <p>No matching active posts.</p>}
    {home.data?.feed_limited && <p>Showing the first 100 active posts, with your matches first. Ask Genie to explore more.</p>}
  </div>;
}
