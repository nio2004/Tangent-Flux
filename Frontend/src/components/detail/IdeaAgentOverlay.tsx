import { Bot, CheckCircle2, GitBranch, Image, Layers3, Link, MessageSquarePlus, Search, Sparkles, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { createChatSession, fetchChatSession, fetchChatSessions, fetchProjectMemory, generateIdeaCardDetail, generateIdeaCards, selectIdeaCard } from "../../api/chat.ts";
import type { ChatMessage, ChatSession, Idea, IdeaAgentCard, ProjectMemory } from "../../types/idea.ts";
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
  const [lastPrompt, setLastPrompt] = useState("Generate the strongest build ideas from this memory, using current web context where it matters.");
  const [cards, setCards] = useState<IdeaAgentCard[]>([]);
  const [selectedCard, setSelectedCard] = useState<IdeaAgentCard | null>(null);
  const [projectMemory, setProjectMemory] = useState<ProjectMemory | null>(null);
  const [groundingCount, setGroundingCount] = useState(0);
  const [generatingCards, setGeneratingCards] = useState(false);
  const [detailingCardId, setDetailingCardId] = useState<string | null>(null);
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
  }, [messages]);

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
      setInput("");
      setCards([]);
      setSelectedCard(null);
      setGroundingCount(0);
      setAppliedCardId(null);
      setDetailingCardId(null);
      window.localStorage.setItem(sessionStorageKey, session.id);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Could not create chat session.");
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateCards() {
    const content = input.trim();
    if (!content || generatingCards || !canChat) {
      return;
    }
    setGeneratingCards(true);
    setAppliedCardId(null);
    setError(null);
    setLastPrompt(content);
    try {
      const response = await generateIdeaCards(idea.id, content);
      setCards(response.cards);
      setSelectedCard(null);
      setGroundingCount(response.grounding.length);
    } catch (cardError) {
      setError(cardError instanceof Error ? cardError.message : "Idea cards could not be generated.");
    } finally {
      setGeneratingCards(false);
    }
  }

  async function loadProjectMemory() {
    try {
      const payload = await fetchProjectMemory(idea.id);
      setProjectMemory(payload.projectMemory);
    } catch {
      setProjectMemory(null);
    }
  }

  async function handleOpenCard(card: IdeaAgentCard) {
    setSelectedCard(card);
    const hasDetails = Boolean(card.whyNow && card.fitReason && card.firstTasks.length);
    if (hasDetails || detailingCardId) {
      return;
    }
    setDetailingCardId(card.id);
    setError(null);
    try {
      const response = await generateIdeaCardDetail(idea.id, lastPrompt, card);
      setCards((current) => current.map((item) => (item.id === card.id ? response.card : item)));
      setSelectedCard(response.card);
      setGroundingCount(response.grounding.length);
    } catch (cardError) {
      setError(cardError instanceof Error ? cardError.message : "Card details could not be generated.");
    } finally {
      setDetailingCardId(null);
    }
  }

  async function handleApplyCard(card: IdeaAgentCard) {
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
              {cards.length > 0 ? (
                <section className="agent-idea-lab" aria-label="Idea generation cards">
                  <div className="agent-lab-heading">
                    <div>
                      <p className="eyebrow">Generated Ideas</p>
                      <h3>Ranked idea cards</h3>
                    </div>
                    <span>{groundingCount ? `${groundingCount} grounded sources` : "memory + web ready"}</span>
                  </div>
                  <div className="agent-card-workspace">
                    <div className="agent-card-list">
                      {cards.map((card) => (
                        <button
                          key={card.id}
                          type="button"
                          className={selectedCard?.id === card.id ? "is-active" : ""}
                          onClick={() => handleOpenCard(card)}
                        >
                          <span>
                            <Sparkles size={14} aria-hidden="true" />
                            {Math.round(card.score * 100)}%
                          </span>
                          <strong>{card.title}</strong>
                          <small>{card.mainTopic}</small>
                          <p>{card.summary}</p>
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
                          <Button
                            variant="hot"
                            onClick={() => handleApplyCard(selectedCard)}
                            disabled={applyingCardId === selectedCard.id || detailingCardId === selectedCard.id || !selectedCard.firstTasks.length}
                          >
                            <Layers3 size={16} aria-hidden="true" />
                            <span>
                              {detailingCardId === selectedCard.id
                                ? "Loading"
                                : appliedCardId === selectedCard.id
                                ? "Added"
                                : applyingCardId === selectedCard.id
                                  ? "Adding"
                                  : "Add TODOs"}
                            </span>
                          </Button>
                        </div>
                        <p>{selectedCard.summary}</p>
                        {detailingCardId === selectedCard.id ? (
                          <div className="agent-detail-loading" aria-live="polite">
                            <span className="agent-spinner" aria-hidden="true" />
                            <p>Generating deep-dive details...</p>
                          </div>
                        ) : (
                          <>
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
                          </>
                        )}
                      </article>
                    )}
                  </div>
                </section>
              ) : (
                <div className="agent-empty">
                  <Bot size={26} aria-hidden="true" />
                  <p>Describe the build ideas you want. The agent will return compact ranked cards first.</p>
                </div>
              )}
              <div className="agent-message-list is-hidden">
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
                <div ref={messageEndRef} />
              </div>
              <div className="agent-composer">
                <textarea
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      handleGenerateCards();
                    }
                  }}
                  rows={3}
                  placeholder="Generate build ideas from this memory..."
                />
                <Button variant="hot" onClick={handleGenerateCards} disabled={generatingCards || !input.trim()}>
                  <Search size={16} aria-hidden="true" />
                  <span>{generatingCards ? "Generating" : "Generate"}</span>
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
