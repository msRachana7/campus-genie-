/* Orchard Commons: warm editorial campus bulletin board with tactile cards, asymmetric discovery, and warm intelligence. */
import { useEffect, useMemo, useState } from "react";
import { authFetch as apiFetch, accessToken, AUTH_EVENT, clearSession, currentUser, saveSession, type CampusUser } from "../lib/campusAuth";
import CampusLogin from "../components/CampusLogin";
import ConnectedGenieView from "../components/GenieView";
import { useGenieChat } from "../hooks/useGenieChat";
import { useHomeDashboard } from "../hooks/useHomeDashboard";
import LiveHomeView from "../components/LiveHomeView";
import { RestoredCommunityView, RestoredPulseView, ConnectedArchiveView } from "../components/RestoredCampusViews";
import {
  Archive, ArrowLeft, ArrowUpRight, Bell, BookOpen, Bot, CalendarDays, ChevronRight,
  CircleHelp, Compass, Download, Flame, GraduationCap, Hash, Heart, History, LayoutGrid,
  Library, Mail, MessageCircle, MoreHorizontal, Paperclip, Phone, Pencil, Play, Plus, Search,
  Send, Share2, Sparkles, UserRound, UsersRound, Zap,
} from "lucide-react";
import { toast } from "sonner";

const tabs = [
  { id: "home", label: "Home", icon: LayoutGrid },
  { id: "resources", label: "Notes & PYQs", icon: Library },
  { id: "community", label: "Community", icon: UsersRound },
  { id: "genie", label: "Ask Genie", icon: Bot },
  { id: "pulse", label: "Campus Pulse", icon: Zap },
  { id: "history", label: "Time Capsule", icon: History },
];

const resources = [
  { type: "PYQ", year: "Year 2", subject: "Data Structures", title: "Data Structures — Semester 3 PYQs", meta: "2021–2024 · 6 papers", tone: "mango" },
  { type: "NOTES", year: "Year 3", subject: "Computer Networks", title: "CN Unit 3: Transport Layer", meta: "12 pages · uploaded by Meera", tone: "sage" },
  { type: "PYQ", year: "Year 1", subject: "Engineering Maths", title: "Differential Equations — quick revision", meta: "8 pages · 94 saves", tone: "lilac" },
];

const prompts = ["What's happening on campus this week?", "Find me a teammate for a hackathon", "Show me notes for Data Structures"];

// Backend returns year_of_study as an integer (1-4). UI shows "1st year", "2nd year", etc.
const yearLabels: Record<number, string> = {
  1: "1st year",
  2: "2nd year",
  3: "3rd year",
  4: "4th year",
};

const yearLabelToNumber = (label: string): number => {
  const found = Object.entries(yearLabels).find(([, v]) => v === label);
  return found ? Number(found[0]) : 1;
};

// Expanded skill and interest pools (25 each) for Edit Profile and the post composer.
const SKILL_OPTIONS = [
  "Python", "Java", "C++", "C", "JavaScript", "TypeScript", "HTML", "CSS", "SQL", "DSA",
  "React", "Node.js", "Django", "Flask", "Machine Learning", "Deep Learning", "Data Analysis",
  "Figma", "UI/UX Design", "Public Speaking", "Cloud Computing (AWS/Azure)", "DevOps",
  "Cybersecurity", "Git & GitHub", "Content Writing",
];

const INTEREST_OPTIONS = [
  "AI & Data", "Hackathons", "Design Systems", "Campus Events", "Web Development",
  "Mobile Development", "Robotics", "Competitive Programming", "Open Source", "Blockchain",
  "Cloud & DevOps", "Cybersecurity", "Product Management", "Entrepreneurship", "Research",
  "Music", "Photography", "Public Speaking & Debate", "Sports", "Volunteering",
  "Sustainability", "Gaming & Game Dev", "Finance & Investing", "Literature & Writing", "Travel",
];

export default function Home() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [checkingSession, setCheckingSession] = useState(true);
  const home = useHomeDashboard(isLoggedIn);
  const [showProfile, setShowProfile] = useState(false);
  const [profile, setProfile] = useState<any>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState("");
  const [showProfileEdit, setShowProfileEdit] = useState(false);
  const [showComposer, setShowComposer] = useState(false);
  const [showResourceUpload, setShowResourceUpload] = useState(false);
  const [activeTab, setActiveTab] = useState("home");
  const [communityFilter, setCommunityFilter] = useState("For you");

  const getStudentId = () => {
    const user = currentUser();
    // student_id is the student's college email, set at login/registration.
    return user?.student_id || user?.email || "";
  };

  const loadProfile = async () => {
    const studentId = getStudentId();
    const requestToken = accessToken();

    if (!studentId) {
      console.error("No logged-in user found");
      setProfileError("You're not logged in.");
      return;
    }

    try {
      setProfileLoading(true);
      setProfileError("");

      const response = await apiFetch(
        "/api/profile/me"
      );

      if (accessToken() === requestToken) setProfile(response);
    } catch (error) {
      if (accessToken() !== requestToken) return;
      console.error("PROFILE ERROR:", error);
      setProfileError(
        error instanceof Error
          ? error.message
          : "Couldn't load your profile right now."
      );
    } finally {
      if (accessToken() === requestToken) setProfileLoading(false);
    }
  };

const navigateToTab = (id: string) => {
  setActiveTab(id);
  setShowProfile(false);
  setShowProfileEdit(false);
  setShowComposer(false);
  setShowResourceUpload(false);
};
const { chat, query, setQuery, sendQuestion, isLoading, error: chatError, resetChat } = useGenieChat();
const active = useMemo(() => tabs.find((tab) => tab.id === activeTab) ?? tabs[0], [activeTab]);

useEffect(() => {
  let cancelled = false;
  const action = new URLSearchParams(window.location.hash.slice(1)).get("auth_action");
  if (action === "verify" || action === "reset" || !accessToken()) {
    setCheckingSession(false);
    return;
  }
  apiFetch<{ user: CampusUser }>("/api/auth/me")
    .then((data) => {
      if (!cancelled) {
        const token = accessToken();
        if (!token) return;
        saveSession(token, data.user);
        setIsLoggedIn(true);
      }
    })
    .catch(() => { if (!cancelled) clearSession(); })
    .finally(() => { if (!cancelled) setCheckingSession(false); });
  return () => { cancelled = true; };
}, []);

useEffect(() => {
  const changed = () => {
    if (!accessToken()) {
      setIsLoggedIn(false);
      setProfile(null);
      setProfileLoading(false);
      setProfileError("");
      setShowProfile(false);
      setShowProfileEdit(false);
      setShowComposer(false);
      setShowResourceUpload(false);
      setActiveTab("home");
    }
  };
  window.addEventListener(AUTH_EVENT, changed);
  return () => window.removeEventListener(AUTH_EVENT, changed);
}, []);

useEffect(() => {
  if (isLoggedIn) void loadProfile();
}, [isLoggedIn]);

const ask = (text: string) => {
  navigateToTab("genie");
  void sendQuestion(text);
};

if (checkingSession) return <main className="login-screen"><p role="status">Checking your session...</p></main>;
if (!isLoggedIn) return <CampusLogin onLogin={() => setIsLoggedIn(true)} />;

return (
  <div className="app-shell">
    <aside className="side-rail">
      <div
        className="brand-lockup"
        onClick={() => navigateToTab("home")}
        role="button"
        tabIndex={0}
      >
        <div className="brand-mark">
          <Sparkles size={17} strokeWidth={2.6} />
        </div>

        <div>
          <div className="brand-name">campus genie</div>
          <div className="brand-sub">BMSCE · 2026</div>
        </div>
      </div>

      <div className="rail-label">YOUR CAMPUS</div>

      <nav className="rail-nav" aria-label="Main navigation">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={
              activeTab === id ? "rail-item is-active" : "rail-item"
            }
            onClick={() => navigateToTab(id)}
          >
            <Icon
              size={17}
              strokeWidth={activeTab === id ? 2.4 : 1.8}
            />
            <span>{label}</span>
            {id === "pulse" && <i className="live-dot" />}
          </button>
        ))}
      </nav>

      <div className="rail-spacer" />
      <button type="button" className="rail-item" onClick={clearSession}>Sign out</button>

      <div className="mini-tip">
        <Sparkles size={14} />
        <span>
          <b>Genie tip</b>
          <br />
          Your saved notes are one good question away.
        </span>
      </div>
    </aside>

    <main className="main-canvas">
      <header className="topbar">
        <div className="mobile-brand">
          <div className="brand-mark">
            <Sparkles size={16} />
          </div>
          <b>campus genie</b>
        </div>

        <div className="crumb">
          <span>{home.clock.date}</span>
          <span className="crumb-dot">·</span>
          <b>{active.label}</b>
        </div>

        <div className="top-actions">
          <button
            className="icon-button"
            onClick={() => navigateToTab("resources")}
            aria-label="Search resources"
          >
            <Search size={18} />
          </button>

          <button
            className="icon-button"
            onClick={() =>
              navigateToTab("community")
            }
            aria-label="Show notifications"
          >
            <Bell size={18} />
          </button>

          <button
            className="top-avatar profile-trigger"
            onClick={() => {
              setShowProfile(true);
              loadProfile();
            }}
            aria-label="Open profile"
          >
            {(profile?.name || home.data?.first_name || "U").charAt(0).toUpperCase()}
          </button>
        </div>
      </header>

      <div className="mobile-tabs">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={activeTab === id ? "is-active" : ""}
            onClick={() => navigateToTab(id)}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      {showProfileEdit ? (
        <EditProfileView
          profile={profile}
          studentId={getStudentId()}
          onBack={() => {
            setShowProfileEdit(false);
            setShowProfile(true);
          }}
          onSaved={(updated) => {
            setProfile(updated);
            home.refresh();
            setShowProfileEdit(false);
            setShowProfile(true);
          }}
        />
      ) : showProfile ? (
        <ProfileView
          profile={profile}
          loading={profileLoading}
          error={profileError}
          onBack={() => setShowProfile(false)}
          onEdit={() => {
            setShowProfile(false);
            setShowProfileEdit(true);
          }}
        />
      ) : showComposer ? (
        <ComposerView onBack={() => setShowComposer(false)} />
      ) : showResourceUpload ? (
        <ResourceUploadView
          onBack={() => setShowResourceUpload(false)}
        />
      ) : (
        <>
          {activeTab === "home" && (
            <LiveHomeView home={home} name={profile?.name} setActiveTab={navigateToTab} ask={ask} />
          )}

          {activeTab === "resources" && (
            <ResourcesView
              setActiveTab={setActiveTab}
              onUploadResource={() => setShowResourceUpload(true)}
            />
          )}

          {activeTab === "community" && (
            <RestoredCommunityView home={home} filter={communityFilter} setFilter={setCommunityFilter} onCreatePost={() => setShowComposer(true)} />
          )}

          {activeTab === "genie" && (
            <ConnectedGenieView
              chat={chat}
              query={query}
              setQuery={setQuery}
              ask={ask}
              isLoading={isLoading}
              error={chatError}
              resetChat={resetChat}
            />
          )}

          {activeTab === "pulse" && (
            <RestoredPulseView home={home} onCommunity={(filter) => { setCommunityFilter(filter); navigateToTab("community"); }} />
          )}

          {activeTab === "history" && (
            <ConnectedArchiveView ask={ask} />
          )}
        </>
      )}
    </main>
  </div>
);
}


function ProfileView({
  profile,
  loading,
  error,
  onBack,
  onEdit,
}: {
  profile: any;
  loading: boolean;
  error: string;
  onBack: () => void;
  onEdit: () => void;
}) {
  if (loading) {
    return (
      <div className="profile-page">
        <button className="profile-back" onClick={onBack}><ArrowLeft size={16} /> Back to campus</button>
        <p style={{ padding: "2rem 0" }}>Loading your profile…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="profile-page">
        <button className="profile-back" onClick={onBack}><ArrowLeft size={16} /> Back to campus</button>
        <p style={{ padding: "2rem 0", color: "#b23b3b" }}>{error}</p>
      </div>
    );
  }

  const name = profile?.name || "Your name";
  const department = profile?.department || "Not set";
  const yearLabel = profile?.year_of_study ? (yearLabels[profile.year_of_study] || `Year ${ profile.year_of_study }`) : "Not set";
  const skills: string[] = profile?.skills || [];
  const interestsList: string[] = profile?.interests || [];
  const initial = name.charAt(0).toUpperCase();

  return <div className="profile-page"><button className="profile-back" onClick={onBack}><ArrowLeft size={16} /> Back to campus</button><section className="profile-hero"><div className="profile-hero-copy"><span className="section-kicker">YOUR CAMPUS IDENTITY</span><h1>Make your<br /><em>space here.</em></h1><p>Your profile helps Genie connect you with the right people, resources, and moments around BMSCE.</p></div><div className="profile-big-avatar"><span>{initial}</span><i>✦</i></div></section><section className="profile-grid"><div className="profile-card profile-details"><div className="profile-card-title"><span className="section-kicker">ABOUT YOU</span><button onClick={onEdit}><Pencil size={14} /> Edit</button></div><div className="profile-name"><div className="profile-avatar profile-avatar-large">{initial}</div><div><h2>{name}</h2><span>{profile?.student_id || ""}</span></div></div><div className="detail-list"><div><Mail size={15} /><span>Email</span><b>{profile?.student_id || "Not set"}</b></div><div><GraduationCap size={15} /><span>Department</span><b>{department}</b></div><div><Library size={15} /><span>Year of study</span><b>{yearLabel}</b></div></div></div><div className="profile-card profile-interests"><span className="section-kicker">YOUR SIGNALS</span><h2>What makes you, you.</h2><p>These help Genie make better introductions and recommendations.</p><span className="profile-label">SKILLS</span><div className="profile-tags">{skills.length ? skills.map((s) => <span key={s}>{s}</span>) : <span>No skills added yet</span>}</div><span className="profile-label">INTERESTS</span><div className="profile-tags tags-mango">{interestsList.length ? interestsList.map((i) => <span key={i}>{i}</span>) : <span>No interests added yet</span>}</div></div><div className="profile-card profile-tip"><div className="signal-icon"><Sparkles size={17} /></div><div><span className="section-kicker">GENIE TIP</span><h3>The more you share, the better the connections.</h3><p>Your profile is only used to personalize your campus experience.</p></div></div></section></div>;
}

function EditProfileView({
  profile,
  studentId,
  onBack,
  onSaved,
}: {
  profile: any;
  studentId: string;
  onBack: () => void;
  onSaved: (updatedProfile: any) => void;
}) {
  const [name, setName] = useState(profile?.name || "");
  const [department, setDepartment] = useState(profile?.department || "Computer Science & Engineering");
  const [yearLabel, setYearLabel] = useState(
    profile?.year_of_study ? (yearLabels[profile.year_of_study] || "1st year") : "1st year"
  );
  const [skills, setSkills] = useState<string[]>(profile?.skills || []);
  const [interests, setInterests] = useState<string[]>(profile?.interests || []);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState("");

  const toggleFromList = (list: string[], value: string) =>
    list.includes(value) ? list.filter((item) => item !== value) : [...list, value];

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!studentId) {
      setSaveError("You're not logged in.");
      return;
    }

    setIsSaving(true);
    setSaveError("");

    try {
      const data = await apiFetch<{ profile: Record<string, unknown> }>("/api/profile/me", {
        method: "PUT",
        body: JSON.stringify({
          name,
          department,
          year_of_study: yearLabelToNumber(yearLabel),
          skills,
          interests,
        }),
      });

      toast.success("Profile updated!");
      onSaved(data.profile);
    } catch (error) {
      console.error("PROFILE UPDATE ERROR:", error);
      setSaveError(
        error instanceof Error
          ? error.message
          : "Couldn't save your profile. Please try again."
      );
    } finally {
      setIsSaving(false);
    }
  };

  return <div className="page-content edit-profile-page">
    <button className="profile-back" onClick={onBack}><ArrowLeft size={16} /> Back to profile</button>
    <section className="edit-profile-card">
      <div className="section-kicker">EDIT YOUR CAMPUS IDENTITY</div>
      <h1>Keep your<br /><em>space current.</em></h1>
      <p>Update the details Genie uses to personalize your campus experience.</p>
      <form className="edit-profile-form" onSubmit={handleSubmit}>
        <div className="composer-field-grid">
          <label>Name<div className="composer-input"><input value={name} onChange={(e) => setName(e.target.value)} /></div></label>
          <label>College email<div className="composer-input"><input type="email" value={studentId} disabled title="Email is your login ID and can't be changed here" /></div></label>
        </div>
        <div className="composer-field-grid">
          <label>Department<div className="composer-input"><select value={department} onChange={(e) => setDepartment(e.target.value)}><option>Computer Science & Engineering</option><option>Electronics & Communication</option><option>Information Science</option><option>Mechanical Engineering</option></select><ChevronRight size={16} /></div></label>
          <label>Year of study<div className="composer-input"><select value={yearLabel} onChange={(e) => setYearLabel(e.target.value)}><option>1st year</option><option>2nd year</option><option>3rd year</option><option>4th year</option></select><ChevronRight size={16} /></div></label>
        </div>
        <label>
          Skills
          <div className="composer-input composer-multi-select">
            <select
              multiple
              size={8}
              aria-label="Select your skills"
              value={skills}
              onChange={(e) => setSkills(Array.from(e.target.selectedOptions, (o) => o.value))}
            >
              {SKILL_OPTIONS.map((skill) => <option key={skill} value={skill}>{skill}</option>)}
            </select>
          </div>
          <small className="field-hint">Ctrl/Cmd-click (or tap each) to select multiple skills.</small>
        </label>
        <label>
          Interests
          <div className="composer-input composer-multi-select">
            <select
              multiple
              size={8}
              aria-label="Select your interests"
              value={interests}
              onChange={(e) => setInterests(Array.from(e.target.selectedOptions, (o) => o.value))}
            >
              {INTEREST_OPTIONS.map((interest) => <option key={interest} value={interest}>{interest}</option>)}
            </select>
          </div>
          <small className="field-hint">Ctrl/Cmd-click (or tap each) to select multiple interests.</small>
        </label>
        {saveError && <p style={{ color: "#b23b3b" }}>{saveError}</p>}
        <div className="composer-actions"><button type="button" className="ghost-button" onClick={onBack}>Cancel</button><button type="submit" className="primary-button" disabled={isSaving}><Sparkles size={15} /> {isSaving ? "Saving..." : "OK"}</button></div>
      </form>
    </section>
  </div>;
}

function ResourcesView({ setActiveTab, onUploadResource }: { setActiveTab: (id: string) => void; onUploadResource: () => void }) { const [resourceQuery, setResourceQuery] = useState(""); const [isStudyStack, setIsStudyStack] = useState(false); const [yearFilter, setYearFilter] = useState("All years"); const [typeFilter, setTypeFilter] = useState("All types"); const filteredResources = resources.filter((resource) => { const searchable = `${ resource.subject } ${ resource.title } ${ resource.meta }`.toLowerCase(); const matchesQuery = searchable.includes(resourceQuery.toLowerCase().trim()); const matchesYear = yearFilter === "All years" || resource.year === yearFilter; const matchesType = typeFilter === "All types" || resource.type === typeFilter; return matchesQuery && matchesYear && matchesType; }); return <div className="page-content"><PageTitle kicker="KNOWLEDGE LIBRARY" title="Notes, PYQs, and the good stuff." description="A browsable shelf for the things that help you learn faster — and ask better questions." action="Upload a resource" onAction={onUploadResource} />{isStudyStack && <button className="profile-back resource-stack-back" onClick={() => { setIsStudyStack(false); setTypeFilter("All types"); }}><ArrowLeft size={16} /> Back to all Notes & PYQs</button>}<div className="resource-toolbar"><div className="search-field"><Search size={17} /><input value={resourceQuery} onChange={(e) => setResourceQuery(e.target.value)} placeholder="Search subjects, units, or keywords..." /></div><label className="filter-control"><span>Year of study</span><select value={yearFilter} onChange={(e) => setYearFilter(e.target.value)}><option>All years</option><option>Year 1</option><option>Year 2</option><option>Year 3</option><option>Year 4</option></select></label><label className="filter-control"><span>Type</span><select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}><option>All types</option><option>PYQ</option><option>NOTES</option></select></label></div><div className="resource-feature"><div><span className="section-kicker">GENIE'S PICK FOR YOU</span><h2>A study stack worth keeping close.</h2><p>Based on what you’ve saved and your Year of study roadmap.</p><button className="primary-button" onClick={() => { setTypeFilter("PYQ"); setIsStudyStack(true); toast("Study stack opened with PYQs."); }}><Play size={15} /> Open study stack</button></div><div className="resource-feature-art"><img src="/manus-storage/campus-genie-notes-visual_d047909b.png" alt="Open notebooks and study papers on a warm campus desk" /><span className="art-label">NOTES · PYQs · SHARED</span></div></div><div className="resource-grid">{filteredResources.map((resource) => <div className="resource-card" key={resource.title}><div className={`resource-badge ${resource.tone}`}>{resource.type}</div><span className="resource-subject">{resource.subject}</span><h3>{resource.title}</h3><span className="resource-meta">{resource.meta}</span><div className="resource-footer"><button onClick={() => toast(`${resource.title} saved to your shelf.`)}><Download size={15} /> Save</button><button className="ask-small" onClick={() => setActiveTab("genie")}><Sparkles size={14} /> Ask Genie</button></div></div>) }</div ></div > }

function PageTitle({ kicker, title, description, action, onAction }: { kicker: string; title: string; description: string; action?: string; onAction?: () => void }) { return <div className="page-title"><div><span className="section-kicker">{kicker}</span><h1>{title}</h1><p>{description}</p></div>{action && <button className="primary-button" onClick={onAction}><Plus size={15} /> {action}</button>}</div> }


/* Orchard Commons composer: a tactile campus noticeboard form for turning a student idea into a structured post. */
function ComposerView({ onBack }: { onBack: () => void }) {
  return <div className="page-content composer-page">
    <button className="profile-back" onClick={onBack}><ArrowLeft size={16} /> Back to community</button>
    <section className="composer-hero">
      <div>
        <span className="section-kicker">PUT IT INTO THE QUAD</span>
        <h1>Make something<br /><em>findable.</em></h1>
        <p>Share a teammate call, a technical opportunity, a research idea, or a campus moment. Genie will help the right people notice it.</p>
      </div>
      <div className="composer-stamp"><Sparkles size={20} /><b>NEW<br />POST</b><span>PRIYA · BMSCE</span></div>
    </section>
    <div className="composer-layout">
      <form className="composer-form" onSubmit={(event) => { event.preventDefault(); toast("Your post is drafted and ready for the campus connection."); }}>
        <div className="composer-form-top"><div><span className="section-kicker">POST DETAILS</span><h2>What are you putting out there?</h2></div><span className="required-note">* required</span></div>
        <div className="composer-field-grid">
          <label>Post type *<div className="composer-input"><select required defaultValue=""><option value="" disabled>Choose a lane</option><option value="hackathon">Hackathon</option><option value="recruitment">Recruitment</option><option value="event">Technical event</option><option value="opportunity">Opportunity</option><option value="research">Research collaboration</option></select><ChevronRight size={16} /></div></label>
          <label>Deadline *<div className="composer-input"><input required type="date" /><CalendarDays size={16} /></div></label>
        </div>
        <label>Title *<div className="composer-input"><input required placeholder="Looking for a Python teammate for our climate project" /></div></label>
        <label>Tell the campus what’s happening *<div className="composer-input composer-textarea"><textarea required rows={5} placeholder="What are you building, researching, or organizing? Tell people why they should join."></textarea></div></label>
        <label>Skills required<div className="composer-input composer-multi-select"><select multiple size={8} aria-label="Select skills required">{SKILL_OPTIONS.map((skill) => <option key={skill}>{skill}</option>)}</select></div><small className="field-hint">Select every skill that would make this post a good fit.</small></label>
        <div className="composer-field-grid">
          <label>Team slots<div className="composer-input"><input type="number" min="1" max="20" defaultValue="2" /><UsersRound size={16} /></div></label>
          <label>Tags<div className="composer-input"><input placeholder="Hackathon, Python, teammates" /><Hash size={16} /></div></label>
        </div>
        <div className="composer-actions"><button type="button" className="ghost-button" onClick={onBack}>Cancel</button><button type="submit" className="primary-button"><Sparkles size={15} /> Publish to the quad <ArrowUpRight size={15} /></button></div>
      </form>
      <aside className="composer-aside"><div className="composer-preview"><span className="section-kicker">LIVE PREVIEW</span><div className="preview-pin">✦</div><h3>Your post will look like a campus card.</h3><p>It will show your title, story, skill tags, deadline, team slots, and a simple Interested action for students who want to join.</p><div className="preview-rule" /><span><BookOpen size={14} /> Structured for Genie</span></div><div className="composer-schema"><span className="section-kicker">GENIE WILL SAVE</span><div><b>author_id</b><span>from your campus identity</span></div><div><b>skills_required</b><span>your selected skill chips</span></div><div><b>deadline</b><span>the date you choose</span></div></div></aside>
    </div>
  </div>;
}


/* Orchard Commons resource intake: a simple shelf-label form for notes and previous-year papers. */
function ResourceUploadView({ onBack }: { onBack: () => void }) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [uploadStatus, setUploadStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const submitResource = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const file = selectedFile;
    const errors: Record<string, string> = {};
    const title = String(formData.get("title") ?? "").trim();
    const subject = String(formData.get("subject") ?? "").trim();
    const resourceType = String(formData.get("resource_type") ?? "");
    const semester = String(formData.get("semester") ?? "");

    if (!resourceType) errors.resource_type = "Choose a resource type.";
    if (!semester) errors.semester = "Choose your year of study.";
    if (!title) errors.title = "Resource title is required.";
    if (!subject) errors.subject = "Subject is required.";
    if (!file) errors.file = "Choose a PDF file to upload.";
    else if (file.size === 0) errors.file = "The selected file is empty.";
    else if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) errors.file = "Only PDF files are allowed.";

    setFieldErrors(errors);
    setUploadStatus(null);
    if (Object.keys(errors).length) return;
    if (!file) return;

    const payload = new FormData();
   const signedInUser = currentUser();


    if (!accessToken()) {
      setUploadStatus({
        type: "error",
        message: "Please sign in before uploading."
      });
      return;
    }

    if (!signedInUser?.email) {
      setUploadStatus({
        type: "error",
        message: "Your email was not found in the login session. Please sign out and log in again."
      });
      return;
    }

    payload.append("email", signedInUser.email);
    payload.append("title", title);
    payload.append("resource_type", resourceType);
    payload.append("subject", subject);
    payload.append("semester", String(Number(semester.replace(/\D/g, ""))));
    payload.append("description", String(formData.get("description") ?? "").trim());
    payload.append("tags", String(formData.get("tags") ?? "").trim());
    payload.append("file", file);

    setIsUploading(true);
    try {
      const backendUrl = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

      const response = await fetch(`${backendUrl}/api/resources/upload`, {
        method: "POST", body: payload,
        headers: { Authorization: `Bearer ${accessToken()}` },
      });
      const result = await response.json().catch(() => ({}));
      if (response.ok) {
        setUploadStatus({ type: "success", message: "Resource uploaded successfully!" });
        form.reset();
        setSelectedFile(null);
        setFieldErrors({});
      } else if (response.status === 409) {
        setUploadStatus({ type: "error", message: "This resource has already been uploaded." });
      } else if (response.status === 422) {
        const reason = result?.reason ?? result?.validation?.reason;
        setUploadStatus({
          type: "error",
          message:
            "This file doesn't seem to match the information you provided." +
            (reason ? ` ${reason}` : ""),
        });
      } else if (response.status === 404) {
          setUploadStatus({ type: "error", message: "Student account could not be found. Please try again." });
        } else if (response.status === 503) {
          setUploadStatus({ type: "error", message: "Resource validation is temporarily unavailable. Please try again in a moment." });
        } else {
          setUploadStatus({ type: "error", message: response.status >= 500 ? "Something went wrong while uploading the resource. Please try again." : "Unable to upload the resource. Please check the details and try again." });
        }
      } catch {
        setUploadStatus({ type: "error", message: "Unable to connect to the server. Please check your internet connection and try again." });
      } finally {
        setIsUploading(false);
      }
    };

    const fieldError = (field: string) => fieldErrors[field] && <span className="field-error">{fieldErrors[field]}</span>;

    return <div className="page-content resource-upload-page">
    <button className="profile-back" onClick={onBack}><ArrowLeft size={16} /> Back to resource shelf</button>
    <section className="resource-upload-hero">
      <div><span className="section-kicker">ADD TO THE SHARED SHELF</span><h1>Pass the good<br /><em>stuff on.</em></h1><p>Upload notes or PYQs so the next student can find the right page before the panic sets in.</p></div>
      <div className="upload-doodle"><div className="doodle-paper paper-back" /><div className="doodle-paper paper-front"><BookOpen size={25} /><span>SHARED<br />SHELF</span></div><Sparkles className="doodle-spark" size={17} /></div>
    </section>
    <div className="resource-upload-layout">
      <form className="resource-upload-form" onSubmit={submitResource}>
        <div className="composer-form-top"><div><span className="section-kicker">RESOURCE DETAILS</span><h2>Give it a useful label.</h2></div><span className="required-note">* required</span></div>
        <div className="composer-field-grid">
          <label>Resource type *<div className="composer-input"><select name="resource_type" defaultValue="" aria-invalid={Boolean(fieldErrors.resource_type)}><option value="" disabled>Choose a type</option><option>NOTES</option><option>PYQ</option></select><ChevronRight size={16} /></div>{fieldError("resource_type")}</label>
          <label>Year of study *<div className="composer-input"><select name="semester" defaultValue="" aria-invalid={Boolean(fieldErrors.semester)}><option value="" disabled>Choose a year</option><option>Year 1</option><option>Year 2</option><option>Year 3</option><option>Year 4</option></select><ChevronRight size={16} /></div>{fieldError("semester")}</label>
        </div>
        <label>Resource title *<div className="composer-input"><input name="title" placeholder="Data Structures — Semester 3 PYQs" aria-invalid={Boolean(fieldErrors.title)} /></div>{fieldError("title")}</label>
        <div className="composer-field-grid">
          <label>Subject *<div className="composer-input"><input name="subject" placeholder="Data Structures" aria-invalid={Boolean(fieldErrors.subject)} /></div>{fieldError("subject")}</label>
          <label>Pages or paper count<div className="composer-input"><input placeholder="12 pages · 6 papers" /></div></label>
        </div>
        <label>What’s inside?<div className="composer-input composer-textarea"><textarea name="description" rows={4} placeholder="Units covered, exam years, useful context, or a note for the person opening it."></textarea></div></label>
        <label>Choose the file *<div className={`resource-file-input ${fieldErrors.file ? "input-error" : ""}`}><Paperclip size={18} /><span>{selectedFile ? selectedFile.name : "Drop a PDF here or browse from your device"}</span><input type="file" accept=".pdf,application/pdf" onChange={(event) => { setSelectedFile(event.target.files?.[0] ?? null); setFieldErrors((current) => ({ ...current, file: "" })); setUploadStatus(null); }} aria-invalid={Boolean(fieldErrors.file)} /></div>{fieldError("file")}</label>
        <label>Tags<div className="composer-input"><input name="tags" placeholder="DSA, Unit 3, revision" /><Hash size={16} /></div></label>
        <div className="composer-actions"><button type="button" className="ghost-button" onClick={onBack}>Cancel</button><button type="submit" className="primary-button" disabled={isUploading}><BookOpen size={15} /> {isUploading ? "Validating & uploading..." : "Add to the shelf"} {!isUploading && <ArrowUpRight size={15} />}</button></div>{uploadStatus && <div className={`upload-status ${uploadStatus.type}`} role="status">{uploadStatus.message}</div>}
      </form>
      <aside className="resource-upload-aside"><div className="upload-note-card"><span className="section-kicker">A LITTLE CONTEXT HELPS</span><h3>Future-you will thank present-you.</h3><p>Good titles and subject labels make the shelf searchable for everyone. Genie can use these details to surface the right material in a question.</p><div className="upload-note-line"><Sparkles size={15} /><span>Keep it specific, keep it kind.</span></div></div><div className="upload-schema-card"><span className="section-kicker">GENIE WILL INDEX</span><div><b>type</b><span>NOTES or PYQ</span></div><div><b>year</b><span>your year of study</span></div><div><b>subject</b><span>the course shelf</span></div><div><b>title + tags</b><span>how students find it</span></div></div></aside>
    </div >
  </div >;
}
