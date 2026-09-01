import { useEffect, useState } from "react";
import { ArrowUpRight, BookOpen, CalendarDays, History, Plus, Sparkles, UsersRound, Zap } from "lucide-react";
import { authFetch, accessToken } from "../lib/campusAuth";
import type { HomePost, HomeState } from "../hooks/useHomeDashboard";
import { HomeStatus, LivePostCard } from "./LiveHomeView";

const FILTERS = ["For you", "Technical events", "Club recruitment", "Hackathons", "Research", "Opportunities"];

export function matchesCategory(post: HomePost, filter: string) {
  const source = `${post.content_source || ""} ${post.type || ""}`.toLowerCase();
  const words = `${post.title} ${post.body} ${post.tags.join(" ")} ${post.skills_required.join(" ")}`.toLowerCase();
  const event = /\b(event|events|technical_event|club_event|workshop|hackathon)\b/.test(source);
  if (filter === "Technical events") return event && /\b(technical|tech|ai|data|coding|code|programming|hackathon|robotics|engineering|machine learning|cybersecurity|python|software|cloud)\b/.test(`${source} ${words}`);
  if (filter === "Club recruitment") return /\b(club_recruitment|recruitment)\b/.test(source)
    || (/\b(club_post|club_posts|clubs)\b/.test(source) && /\b(recruit|recruiting|recruitment|volunteer|volunteers|join|members|open call|applications)\b/.test(words));
  if (filter === "Hackathons") return /\bhackathons?\b/.test(`${source} ${words}`);
  if (filter === "Research") return /\b(research|research_post|research_posts)\b/.test(source);
  if (filter === "Opportunities") return /\b(opportunity|opportunities|internship|scholarship)\b/.test(source);
  return true;
}

export function RestoredCommunityView({ home, filter, setFilter, onCreatePost }: {
  home: HomeState; filter: string; setFilter: (filter: string) => void; onCreatePost: () => void;
}) {
  const [query, setQuery] = useState("");
  const all = home.data?.posts || [];
  const posts = all.filter(post => matchesCategory(post, filter)
    && `${post.title} ${post.body} ${post.tags.join(" ")}`.toLowerCase().includes(query.toLowerCase()));
  const available = home.data?.content_status === "ok";
  return <div className="page-content community-page">
    <div className="community-hero"><div className="community-hero-copy">
      <div className="eyebrow"><span className="eyebrow-pin">✦</span> THE QUAD, ONLINE</div>
      <h1>Find your<br /><em>people.</em></h1><p>Big ideas, last-minute teams, club chaos, and the small moments that make campus feel like yours.</p>
      <button className="primary-button" onClick={onCreatePost}><Plus size={15} /> Drop something into the quad</button>
    </div><div className="community-orbit"><div className="orbit-ring ring-one" /><div className="orbit-ring ring-two" />
      <div className="orbit-center"><UsersRound size={23} /><b>{home.data?.pulse?.active_count ?? "—"}</b><small>active campus posts</small></div>
      <span className="orbit-bubble bubble-one">find a teammate</span><span className="orbit-bubble bubble-two">explore clubs</span><span className="orbit-bubble bubble-three">build together</span>
    </div></div>
    <div className="campus-marquee"><div className="campus-marquee-track"><div className="marquee-set">
      <span>✦ TECHNICAL EVENTS</span><i>·</i><span>CLUB RECRUITMENT</span><i>·</i><span>HACKATHON TEAMS</span><i>·</i><span>RESEARCH COLLABORATION</span>
    </div></div></div>
    <div className="community-layout"><div><div className="community-filters">
      {FILTERS.map(item => <button key={item} className={filter === item ? "active" : ""} onClick={() => setFilter(item)}>{item}</button>)}
      <button className="community-create-link" onClick={onCreatePost}><Plus size={14} /> Create a post</button>
    </div><label>Search these posts<div className="composer-input"><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Python, research, clubs…" /></div></label>
      <HomeStatus home={home} />
      {posts.map(post => <LivePostCard key={post.id} post={post} home={home} />)}
      {available && !posts.length && <div className="empty-state"><b>No current posts in this category.</b><span>Try another filter or check again after the campus data refreshes.</span></div>}
      {home.data?.feed_limited && <p>Filters search the first 100 loaded posts. Ask Genie to explore more.</p>}
    </div></div>
  </div>;
}

export function RestoredPulseView({ home, onCommunity }: { home: HomeState; onCommunity: (filter: string) => void }) {
  const pulse = home.data?.pulse;
  const values = pulse?.event_days || [];
  const max = Math.max(1, ...values);
  const updated = home.data?.content_fetched_at
    ? new Date(home.data.content_fetched_at).toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit" }) + " IST"
    : "awaiting campus data";
  return <div className="page-content pulse-page">
    <div className="pulse-mode-banner"><div className="pulse-mode-icon"><Zap size={18} /></div><div><span className="section-kicker">THE CAMPUS, IN MOTION</span><b>Campus Pulse</b></div><span className="pulse-mode-status">This week’s campus listings</span></div>
    <HomeStatus home={home} />
    <section className="pulse-stage"><div className="pulse-stage-copy"><div className="live-label">CAMPUS SIGNALS · THIS WEEK</div><h1>Feel the<br /><em>campus energy.</em></h1>
      <p>{pulse?.detail || "Explore technical events, club recruitment, and opportunities from your campus."}</p>
      <div className="pulse-stat-row"><div><b>{pulse?.active_count ?? "—"}</b><span>active campus posts</span></div><div><b>{pulse?.has_event_dates ? pulse.ai_event_count : "—"}</b><span>AI events this week</span></div><div><b>{home.data?.shortcuts.matching_posts ?? "—"}</b><span>posts matching you</span></div></div>
    </div><div className="signal-field"><div className="field-grid" /><div className="field-core"><span className="core-glow" /><b>{pulse?.active_count ?? "—"}</b><small>active posts</small></div>
      <button className="signal-node node-ai" onClick={() => onCommunity("Technical events")}><Sparkles size={13} /><span>Technical events</span><b>explore</b></button>
      <button className="signal-node node-club" onClick={() => onCommunity("Club recruitment")}><UsersRound size={13} /><span>Club recruitment</span><b>explore</b></button>
      <div className="signal-node node-build"><Zap size={13} /><span>Build together</span></div><div className="signal-node node-fest"><CalendarDays size={13} /><span>Campus events</span></div><div className="signal-path path-one" /><div className="signal-path path-two" />
    </div><div className="pulse-stage-footer"><span>Data fetched: {updated}</span><span>Tap a signal to explore</span></div></section>
    <div className="pulse-section-intro"><div><span className="section-kicker">THE CAMPUS, IN MOTION</span><h2>What’s making waves</h2></div></div>
    <div className="pulse-story-grid">
      <button className="pulse-story story-orange" style={{ textAlign: "left", border: 0, font: "inherit", color: "inherit", cursor: "pointer" }} onClick={() => onCommunity("Technical events")}>
        <span className="story-number">01</span><div className="story-icon"><Sparkles size={19} /></div><span className="section-kicker">CURIOUS MINDS</span><h3>Find your next technical event.</h3><p>Explore technical workshops, hackathons, coding events, and AI sessions.</p><b>Explore technical events <ArrowUpRight size={15} /></b>
      </button>
      <button className="pulse-story story-lilac" style={{ textAlign: "left", border: 0, font: "inherit", color: "inherit", cursor: "pointer" }} onClick={() => onCommunity("Club recruitment")}>
        <span className="story-number">02</span><div className="story-icon"><UsersRound size={19} /></div><span className="section-kicker">THE SOCIAL CURRENT</span><h3>People are looking for people.</h3><p>Find clubs recruiting members, volunteers, and student teams.</p><b>Explore club recruitment <ArrowUpRight size={15} /></b>
      </button>
    </div>
    {pulse?.has_event_dates && <div className="pulse-bottom-grid"><div className="pulse-rhythm"><div className="section-kicker">SCHEDULED EVENTS · MONDAY TO SUNDAY</div><h3>Campus has a rhythm.</h3><div className="rhythm-bars" role="img" aria-label={`Scheduled events Monday to Sunday: ${values.join(", ")}`}>
      {values.map((value, i) => <i key={i} title={`${["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i]}: ${value}`} style={{ height: `${value / max * 100}%` }}><span /></i>)}
    </div><div className="chart-labels"><span>MON</span><span>SUN</span></div></div></div>}
  </div>;
}

type Story = { title: string; description: string };
type Archive = { year: string; campus_life: Story; hackathons: Story; archive_question: string };

export function ConnectedArchiveView({ ask }: { ask: (question: string) => void }) {
  const [years, setYears] = useState<string[]>([]);
  const [year, setYear] = useState("");
  const [entry, setEntry] = useState<Archive | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let cancelled = false;
    const token = accessToken();
    setLoading(true); setError(""); setEntry(null);
    authFetch<{ available_years: string[] }>("/api/archive").then(result => {
      if (cancelled || accessToken() !== token) return;
      if (!Array.isArray(result.available_years)) throw new Error("The archive response is incomplete.");
      const available = result.available_years.map(String).sort((a, b) => Number(b) - Number(a));
      setYears(available);
      setYear(current => available.includes(current) ? current : available[0] || "");
      if (!available.length) setLoading(false);
    }).catch(cause => {
      if (!cancelled && accessToken() === token) { setError(cause instanceof Error ? cause.message : "Archive unavailable."); setLoading(false); }
    });
    return () => { cancelled = true; };
  }, [retry]);
  useEffect(() => {
    if (!year) return;
    let cancelled = false;
    const token = accessToken();
    setEntry(null); setLoading(true); setError("");
    authFetch<Archive>(`/api/archive/${encodeURIComponent(year)}`).then(result => {
      if (cancelled || accessToken() !== token) return;
      if (String(result.year) !== year || !result.campus_life || !result.hackathons) throw new Error("The archive response is incomplete.");
      setEntry(result);
    }).catch(cause => {
      if (!cancelled && accessToken() === token) setError(cause instanceof Error ? cause.message : "Archive unavailable.");
    }).finally(() => { if (!cancelled && accessToken() === token) setLoading(false); });
    return () => { cancelled = true; };
  }, [year, retry]);
  return <div className="page-content history-page">
    <div className="history-hero"><div className="history-copy"><span className="section-kicker">TIME CAPSULE · BMSCE ARCHIVES</span><h1>Campus has a<br /><em>long memory.</em></h1><p>Explore campus memories, student communities, and the ideas that brought people together.</p><button className="primary-button" onClick={() => ask(`What past campus events can you tell me about${year ? ` from ${year}` : ""}?`)}><History size={15} /> Explore with Genie <ArrowUpRight size={15} /></button></div><div className="history-stamp">EST.<br /><b>1946</b><span>BENGALURU</span></div></div>
    <div className="history-controls"><div><span className="section-kicker">BROWSE THE YEARS</span><h2>Choose a thread to follow</h2></div><div className="year-pills">{years.map(item => <button key={item} className={year === item ? "active" : ""} onClick={() => { if (item !== year) { setEntry(null); setYear(item); } }}>{item}</button>)}</div></div>
    {error && <div className="empty-state" role="alert"><b>Could not load the archive.</b><span>{error}</span><button className="ghost-button" onClick={() => setRetry(value => value + 1)}>Retry</button></div>}
    {loading && <p role="status">Loading {year} archive…</p>}
    {!loading && !error && !years.length && <p>No archive years are available yet.</p>}
    {entry && !loading && !error && <div className="history-grid">
      <div className="history-story story-large"><div className="story-image image-campus" style={{ display: "grid", placeItems: "center" }} aria-hidden="true"><BookOpen size={64} /></div><div className="story-copy"><span className="section-kicker">CAMPUS LIFE · {entry.year}</span><h3>{entry.campus_life.title}</h3><p>{entry.campus_life.description}</p></div></div>
      <div className="history-story"><div className="story-image image-hack" style={{ display: "grid", placeItems: "center" }} aria-hidden="true"><Sparkles size={64} /></div><div className="story-copy"><span className="section-kicker">HACKATHONS · {entry.year}</span><h3>{entry.hackathons.title}</h3><p>{entry.hackathons.description}</p></div></div>
      <div className="history-story note-story"><div className="note-pin">✦</div><span className="section-kicker">ASK THE ARCHIVE</span><h3>“{entry.archive_question}”</h3><button onClick={() => ask(`${entry.archive_question} Focus on ${entry.year} and use available campus sources.`)}>Ask Genie <ArrowUpRight size={14} /></button></div>
    </div>}
    <div className="source-note">Curated campus memories from your archive collection.</div>
  </div>;
}
