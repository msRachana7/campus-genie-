import { useEffect, useRef } from "react";
import { ArrowUpRight, Send, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "../lib/genieApi";
import "./genie-chat.css";

type Props = {
  chat: ChatMessage[];
  query: string;
  setQuery: (value: string) => void;
  ask: (question: string) => void;
  isLoading: boolean;
  error: string;
  resetChat: () => void;
};

function safeLink(url: string) {
  try {
    const parsed = new URL(url);
    return ["https:", "http:"].includes(parsed.protocol) && !parsed.username && !parsed.password;
  } catch { return false; }
}

export default function GenieView({ chat, query, setQuery, ask, isLoading, error, resetChat }: Props) {
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }, [chat, isLoading, error]);
  return (
    <div className="page-content genie-page">
      <div className="page-title"><div>
        <span className="section-kicker">THE INTELLIGENCE LAYER</span>
        <h1>Ask your campus.</h1>
        <p>Genie connects the dots between resources, people, events, and the little bits of campus knowledge you don’t want to lose.</p>
      </div></div>
      <div className="chat-layout">
        <div className="chat-window">
          <div className="chat-header">
            <div className="chat-orb"><Sparkles size={18} /></div>
            <div><b>Campus Genie</b><span><i className="live-dot" /> {isLoading ? "searching your campus…" : "powered by your Databricks Supervisor"}</span></div>
            <button type="button" onClick={resetChat} aria-label="Start a new chat">New chat</button>
          </div>
          <div className="chat-messages" role="log" aria-label="Conversation" aria-live="polite">
            <div className="genie-message"><div className="message-avatar"><Sparkles size={13} /></div><div>
              <p>Hey! Ask me about BMSCE, club events, opportunities, or finding teammates.</p><span>Campus Genie</span>
            </div></div>
            {chat.map((message) => message.role === "user" ? (
              <div className="user-message" key={message.id}><p style={{ whiteSpace: "pre-wrap" }}>{message.content}</p></div>
            ) : (
              <div className="genie-message" key={message.id}>
                <div className="message-avatar"><Sparkles size={13} /></div>
                <div className="genie-answer">
                  <div className="genie-markdown">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml components={{
                      a: ({ href, children }) => href && safeLink(href)
                        ? <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
                        : <span>{children}</span>,
                      // Avoid external tracking images in generated responses.
                      img: () => null,
                    }}>{message.content}</ReactMarkdown>
                  </div>
                  {!!message.citations?.length && <div className="genie-sources"><b>Sources</b><ul>
                    {message.citations.filter((source) => safeLink(source.url)).map((source) => (
                      <li key={source.url}><a href={source.url} target="_blank" rel="noopener noreferrer">{source.title}</a></li>
                    ))}
                  </ul></div>}
                  <span>Campus Genie</span>
                </div>
              </div>
            ))}
            {isLoading && <div className="genie-message" role="status"><div className="message-avatar"><Sparkles size={13} /></div><div><p>Searching campus data and official website information…</p></div></div>}
            {error && <p className="genie-chat-error" role="alert">{error}</p>}
            <div ref={end} />
          </div>
          <div className="suggestion-row">
            {["What’s happening on campus this week?", "Find me a teammate for a hackathon", "What facilities are available at BMSCE?"].map((prompt) => (
              <button type="button" key={prompt} disabled={isLoading} onClick={() => ask(prompt)}>{prompt}</button>
            ))}
          </div>
          <form className="chat-input" onSubmit={(event) => { event.preventDefault(); ask(query); }}>
            <input aria-label="Ask Genie" value={query} onChange={(event) => setQuery(event.target.value)} maxLength={4000} disabled={isLoading} placeholder="Ask anything about your campus…" />
            <button className="send-button" type="submit" disabled={isLoading || !query.trim()} aria-label="Send"><Send size={16} /></button>
          </form>
        </div>
        <div className="genie-aside">
          <div className="question-card"><span>TRY A BETTER QUESTION</span><h3>“What should I learn before joining an AI hackathon?”</h3><button type="button" disabled={isLoading} onClick={() => ask("What should I learn before joining an AI hackathon?")}>Use this prompt <ArrowUpRight size={14} /></button></div>
          <div className="pillars"><span className="section-kicker">GENIE KNOWS</span>
            {[["Know", "Policies, campus info, facilities"], ["Discover", "Events, clubs, opportunities"], ["Connect", "Peers, teammates, mentors"], ["Grow", "Skills, paths, resources"]].map(([title, description]) => <div key={title}><span>{title}</span><p>{description}</p></div>)}
          </div>
        </div>
      </div>
    </div>
  );
}
