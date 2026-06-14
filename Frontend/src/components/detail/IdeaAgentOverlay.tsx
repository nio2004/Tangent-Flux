import { Bot, CheckCircle2, GitBranch, Image, Layers3, Link, MessageSquarePlus, Search, Send, Sparkles, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { createChatSession, fetchChatSession, fetchChatSessions, fetchProjectMemory, generateIdeaCards, selectIdeaCard, sendIdeaAgentMessage } from "../../api/chat.ts";
import type { ChatMessage, ChatSession, Idea, IdeaAgentCard, ProjectMemory, ProjectMemoryEvent } from "../../types/idea.ts";
import { Button } from "../ui/button.tsx";

interface IdeaAgentOverlayProps {
  open: boolean;
  idea: Idea;
  onClose: () => void;
  onWorkspaceChange: () => Promise<void>;
}

export function IdeaAgentOverlay({ open, idea, onClose, onWorkspaceChange }: IdeaAgentOverlayProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [pendingUserMessage, setPendingUserMessage] = useState<string | null>(null);
  const [ideaPrompt, setIdeaPrompt] = useState("Generate the strongest build ideas from this memory, using current web context where it matters.");
  const [cards, setCards] = useState<IdeaAgentCard[]>([]);
  const [selectedCard, setSelectedCard] = useState<IdeaAgentCard | null>(null);
  const [projectMemory, setProjectMemory] = useState<ProjectMemory | null>(null);
  const [projectEvents, setProjectEvents] = useState<ProjectMemoryEvent[]>([]);
  const [groundingCount, setGroundingCount] = useState(0);
  const [generatingCards, setGeneratingCards] = useState(false);
  const [applyingCardId, setApplyingCardId] = useState<string | null>(null);
  const [appliedCardId, setAppliedCardId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messageEndRef = useRef<HTMLDivElement | null>(null);

  const canChat = idea.memoryState === "MEMORY_READY";
  const sortedSessions = useMemo(() => sessions.slice().sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)), [sessions]);
  const sessionStorageKey = `tangent-flux:last-agent-session:${idea.id}`;

  useEffect(() => {
    if (open) {
      loadSessions();
      loadProjectMemory();
    }
  }, [open, idea.id]);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [messages, pendingUserMessage, sending]);

  async function loadSessions() {
    setLoading(true);
    setError(null);
    try {
      const loaded = await fetchChatSessions(idea.id);
      setSessions(loaded);
      const storedSessionId = window.localStorage.getItem(sessionStorageKey);
      const sessionToOpen = loaded.find((session) => session.id === storedSessionId) ?? loaded[0];
      if (sessionToOpen) {
        await selectSession(sessionToOpen.id);
      } else {
        setActiveSession(null);
        setMessages([]);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Could not load agent sessions.");
    } finally {
      setLoading(false);
    }
  }

  async function selectSession(sessionId: string) {
    setLoading(true);
    setError(null);
    try {
      const detail = await fetchChatSession(idea.id, sessionId);
      setActiveSession(detail.session);
      setMessages(detail.messages);
      window.localStorage.setItem(sessionStorageKey, detail.session.id);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Could not load chat session.");
    } finally {
      setLoading(false);
    }
  }

  async function startNewSession() {
    setLoading(true);
    setError(null);
    try {
      const session = await createChatSession(idea.id, `${idea.title} agent`);
      setSessions((current) => [session, ...current]);
      setActiveSession(session);
      setMessages([]);
      window.localStorage.setItem(sessionStorageKey, session.id);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Could not create chat session.");
    } finally {
      setLoading(false);
    }
  }

  async function sendMessage() {
    const content = input.trim();
    if (!content || sending || !canChat) {
      return;
    }
    setSending(true);
    setPendingUserMessage(content);
    setError(null);
    setInput("");
    try {
      const response = await sendIdeaAgentMessage(idea.id, content, activeSession?.id, projectMemory?.id);
      setActiveSession(response.session);
      setSessions((current) => [response.session, ...current.filter((session) => session.id !== response.session.id)]);
      setMessages((current) => [...current, response.userMessage, response.assistantMessage]);
      window.localStorage.setItem(sessionStorageKey, response.session.id);
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : "Agent could not answer.");
      setInput(content);
    } finally {
      setSending(false);
      setPendingUserMessage(null);
    }
  }

  async function loadProjectMemory() {
    try {
      const payload = await fetchProjectMemory(idea.id);
      setProjectMemory(payload.projectMemory);
      setProjectEvents(payload.recentEvents);
    } catch {
      setProjectMemory(null);
      setProjectEvents([]);
    }
  }

  async function handleGenerateCards() {
    const prompt = ideaPrompt.trim();
    if (!prompt || generatingCards || !canChat) {
      return;
    }
    setGeneratingCards(true);
    setAppliedCardId(null);
    setError(null);
    try {
      const response = await generateIdeaCards(idea.id, prompt);
      setCards(response.cards);
      setSelectedCard(response.cards[0] ?? null);
      setGroundingCount(response.grounding.length);
    } catch (cardError) {
      setError(cardError instanceof Error ? cardError.message : "Idea cards could not be generated.");
    } finally {
      setGeneratingCards(false);
    }
  }

  async function handleSelectCard(card: IdeaAgentCard) {
    setApplyingCardId(card.id);
    setError(null);
    try {
      const response = await selectIdeaCard(idea.id, card);
      setProjectMemory(response.projectMemory);
      setAppliedCardId(card.id);
      await onWorkspaceChange();
      await loadProjectMemory();
    } catch (cardError) {
      setError(cardError instanceof Error ? cardError.message : "Card could not be added to Kanban.");
    } finally {
      setApplyingCardId(null);
    }
  }

  if (!open) {
    return null;
  }

  return (
    <div className="idea-agent-overlay" role="dialog" aria-modal="true" aria-label={`${idea.title} memory agent`}>
      <div className="idea-agent-shell">
        <aside className="agent-session-rail">
          <div className="agent-panel-heading">
            <div>
              <p className="eyebrow">Idea Agent</p>
              <h2>{idea.title}</h2>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close idea agent">
              <X size={18} aria-hidden="true" />
            </Button>
          </div>
          <Button variant="hot" onClick={startNewSession} disabled={loading}>
            <MessageSquarePlus size={16} aria-hidden="true" />
            <span>New session</span>
          </Button>
          <div className="agent-session-list">
            {sortedSessions.map((session) => (
              <button
                key={session.id}
                type="button"
                className={activeSession?.id === session.id ? "is-active" : ""}
                onClick={() => selectSession(session.id)}
              >
                <strong>{session.title}</strong>
                <span>{session.messageCount} messages</span>
              </button>
            ))}
            {!sortedSessions.length && <p>No sessions yet.</p>}
          </div>
        </aside>

        <main className="agent-chat-panel">
          {!canChat && (
            <div className="agent-empty">
              <Bot size={26} aria-hidden="true" />
              <p>Initialize local memory first so the agent can use graph nodes, evidence, links, and image descriptions.</p>
            </div>
          )}
          {canChat && (
            <>
              <div className="agent-context-strip">
                <span>{idea.memoryState}</span>
                <span>{activeSession ? activeSession.messageCount : 0} saved messages</span>
                <span>{projectMemory ? "Using local project memory first" : "Using parent idea memory"}</span>
              </div>
              {projectMemory && (
                <section className="agent-project-memory" aria-label="Project memory">
                  <div>
                    <p className="eyebrow">Project Memory</p>
                    <h3>{projectMemory.title}</h3>
                    <span>{projectMemory.mainTopic}</span>
                  </div>
                  <p>{projectMemory.textualSummary}</p>
                  {projectEvents.length > 0 && (
                    <ul>
                      {projectEvents.slice(0, 4).map((event) => (
                        <li key={event.id}>
                          <strong>{event.eventType.replace(/_/g, " ")}</strong>
                          <span>{event.content}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              )}
              <section className="agent-idea-lab" aria-label="Idea generation cards">
                <div className="agent-lab-heading">
                  <div>
                    <p className="eyebrow">Generate Ideas</p>
                    <h3>Ranked idea cards</h3>
                  </div>
                  <span>{groundingCount ? `${groundingCount} grounded sources` : "memory + web ready"}</span>
                </div>
                <div className="agent-card-prompt">
                  <textarea
                    value={ideaPrompt}
                    onChange={(event) => setIdeaPrompt(event.target.value)}
                    rows={2}
                    placeholder="Describe the ideas you want the agent to filter and rank..."
                  />
                  <Button variant="hot" onClick={handleGenerateCards} disabled={generatingCards || !ideaPrompt.trim()}>
                    <Search size={16} aria-hidden="true" />
                    <span>{generatingCards ? "Generating" : "Generate cards"}</span>
                  </Button>
                </div>
                {cards.length > 0 && (
                  <div className="agent-card-workspace">
                    <div className="agent-card-list">
                      {cards.map((card) => (
                        <button
                          key={card.id}
                          type="button"
                          className={selectedCard?.id === card.id ? "is-active" : ""}
                          onClick={() => setSelectedCard(card)}
                        >
                          <span>
                            <Sparkles size={14} aria-hidden="true" />
                            {Math.round(card.score * 100)}%
                          </span>
                          <strong>{card.title}</strong>
                          <small>{card.mainTopic}</small>
                        </button>
                      ))}
                    </div>
                    {selectedCard && (
                      <article className="agent-card-detail">
                        <div className="agent-card-detail-heading">
                          <div>
                            <p>{selectedCard.mainTopic}</p>
                            <h4>{selectedCard.title}</h4>
                          </div>
                          <Button variant="hot" onClick={() => handleSelectCard(selectedCard)} disabled={applyingCardId === selectedCard.id}>
                            <Layers3 size={16} aria-hidden="true" />
                            <span>
                              {appliedCardId === selectedCard.id
                                ? "Added"
                                : applyingCardId === selectedCard.id
                                  ? "Adding"
                                  : "Add TODOs"}
                            </span>
                          </Button>
                        </div>
                        <p>{selectedCard.summary}</p>
                        <div className="agent-card-grid">
                          <section>
                            <h5>Why now</h5>
                            <p>{selectedCard.whyNow}</p>
                          </section>
                          <section>
                            <h5>Fit</h5>
                            <p>{selectedCard.fitReason}</p>
                          </section>
                        </div>
                        <div className="agent-card-columns">
                          <section>
                            <h5>Evidence</h5>
                            <ul>{selectedCard.evidence.map((item) => <li key={item}>{item}</li>)}</ul>
                          </section>
                          <section>
                            <h5>Risks</h5>
                            <ul>{selectedCard.risks.map((item) => <li key={item}>{item}</li>)}</ul>
                          </section>
                          <section>
                            <h5>Kanban TODOs</h5>
                            <ul>
                              {selectedCard.firstTasks.map((task) => (
                                <li key={`${selectedCard.id}-${task.title}`}>
                                  <CheckCircle2 size={13} aria-hidden="true" />
                                  <span>{task.title}</span>
                                </li>
                              ))}
                            </ul>
                          </section>
                        </div>
                      </article>
                    )}
                  </div>
                )}
              </section>
              <div className="agent-message-list">
                {messages.map((message) => (
                  <article key={message.id} className={message.role === "user" ? "agent-message is-user" : "agent-message"}>
                    <div className="agent-message-content">{renderMessageContent(message.content)}</div>
                    {message.sources.length > 0 && (
                      <div className="agent-sources">
                        {message.sources.slice(0, 5).map((source) => (
                          <span className={`source-${source.kind}`} key={`${message.id}-${source.id}`} title={source.excerpt}>
                            {sourceIcon(source.kind)}
                            {source.kind}: {source.title}
                          </span>
                        ))}
                      </div>
                    )}
                  </article>
                ))}
                {pendingUserMessage && (
                  <article className="agent-message is-user is-pending">
                    <div className="agent-message-content"><p>{pendingUserMessage}</p></div>
                  </article>
                )}
                {sending && (
                  <article className="agent-message is-thinking" aria-live="polite">
                    <span className="agent-spinner" aria-hidden="true" />
                    <p>Thinking through this idea's memory...</p>
                  </article>
                )}
                <div ref={messageEndRef} />
                {!messages.length && !loading && !sending && !pendingUserMessage && (
                  <div className="agent-empty">
                    <Bot size={26} aria-hidden="true" />
                    <p>Ask about relationships between papers, links, graph nodes, and uploaded image descriptions.</p>
                  </div>
                )}
              </div>
              <div className="agent-composer">
                <textarea
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      sendMessage();
                    }
                  }}
                  rows={3}
                  placeholder="Ask this idea's agent..."
                />
                <Button variant="hot" onClick={sendMessage} disabled={sending || !input.trim()}>
                  <Send size={16} aria-hidden="true" />
                  <span>{sending ? "Thinking" : "Send"}</span>
                </Button>
              </div>
            </>
          )}
          {error && <p className="agent-error">{error}</p>}
        </main>
      </div>
    </div>
  );
}

function renderMessageContent(content: string) {
  const lines = content.split("\n").map((line) => line.trim()).filter(Boolean);
  const bulletLines = lines.filter((line) => line.startsWith("- "));
  if (bulletLines.length) {
    return (
      <ul>
        {bulletLines.map((line, index) => (
          <li key={`${line}-${index}`}>{line.replace(/^- /, "")}</li>
        ))}
      </ul>
    );
  }
  return <p>{content}</p>;
}

function sourceIcon(kind: string) {
  if (kind === "image") {
    return <Image size={13} aria-hidden="true" />;
  }
  if (kind === "graph") {
    return <GitBranch size={13} aria-hidden="true" />;
  }
  return <Link size={13} aria-hidden="true" />;
}
