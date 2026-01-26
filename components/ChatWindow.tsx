import React, { useEffect, useRef, useState } from "react";
import { Message, SourceRef } from "../types";
import { sendChat } from "../services/chatApi";

interface ChatWindowProps {
  isOpen: boolean;
  onClose: () => void;
}

function makeSessionId(): string {
  const anyCrypto = (window as any).crypto;
  if (anyCrypto?.randomUUID) return anyCrypto.randomUUID();
  return `guest_${Math.random().toString(16).slice(2)}_${Date.now()}`;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      text:
        "Welcome to the official Federal Urdu University Academic Assistant.\n\nAsk me about admissions, fees, programs, results, convocation, and campus information.",
      timestamp: new Date(),
    },
  ]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState<string>(() => makeSessionId());
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, isLoading]);

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();

    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      text: trimmed,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await sendChat(trimmed, sessionId);

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        text: res.answer,
        timestamp: new Date(),
        sources: res.sources,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err: any) {
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        text:
          "Sorry — I could not reach the server right now. Please try again in a moment.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderSources = (sources?: SourceRef[]) => {
    if (!sources?.length) return null;

    return (
      <div className="mt-3 pt-3 border-t border-slate-100 text-[12px] text-slate-500">
        <div className="font-semibold text-slate-600 mb-1">Sources</div>
        <ul className="space-y-1">
          {sources.slice(0, 4).map((s, idx) => (
            <li key={`${s.label}-${idx}`} className="leading-snug">
              {s.url ? (
                <a
                  href={s.url}
                  target="_blank"
                  rel="noreferrer"
                  className="underline hover:text-slate-700"
                >
                  {s.label}
                </a>
              ) : (
                <span>{s.label}</span>
              )}
            </li>
          ))}
        </ul>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-6 right-6 w-[420px] h-[650px] bg-white rounded-[2.5rem] shadow-[0_20px_60px_-15px_rgba(0,0,0,0.3)] border border-slate-100 flex flex-col overflow-hidden z-[100] animate-in slide-in-from-bottom-10 fade-in duration-300">
      <div className="bg-[#1e3a8a] pt-8 pb-6 px-8 text-white relative">
        <div className="absolute top-4 right-4 flex items-center gap-2">
          <button
            onClick={onClose}
            className="hover:bg-white/10 p-2 rounded-full transition-colors w-10 h-10 flex items-center justify-center"
          >
            <i className="fas fa-times text-sm"></i>
          </button>
        </div>

        <div className="flex items-center gap-4">
          <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center shadow-lg transform -rotate-3 group">
            <i className="fas fa-graduation-cap text-[#1e3a8a] text-2xl"></i>
          </div>

          <div>
            <h2 className="text-xl font-bold tracking-tight">
              FUUAST Academic Assistant
            </h2>
            <p className="text-blue-100 text-sm font-medium mt-1 flex items-center gap-2">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
              Online • Verified University Info
            </p>
          </div>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-6 py-6 space-y-4 bg-gradient-to-b from-slate-50 to-white chat-scroll"
      >
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] p-4 rounded-2xl text-[15px] leading-relaxed shadow-sm transition-all hover:shadow-md ${
                m.role === "user"
                  ? "bg-[#1e3a8a] text-white rounded-br-none"
                  : "bg-white border border-slate-100 text-slate-800 rounded-bl-none"
              }`}
            >
              <p className="whitespace-pre-wrap font-medium">{m.text}</p>

              {m.role === "assistant" && renderSources(m.sources)}

              <div
                className={`mt-3 pt-2 border-t flex justify-between items-center opacity-50 text-[9px] font-bold uppercase tracking-wider ${
                  m.role === "user"
                    ? "border-white/10 text-blue-100"
                    : "border-slate-100 text-slate-400"
                }`}
              >
                <span>
                  {m.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
                {m.role === "assistant" && <span>Institutional Data</span>}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-100 p-4 rounded-2xl shadow-sm">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 bg-blue-600/30 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-blue-600/60 rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="p-6 bg-white border-t border-slate-100">
        <form onSubmit={handleSend} className="relative group">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about admissions, fees, programs..."
            className="w-full pl-6 pr-14 py-4 bg-slate-100 rounded-2xl text-[13px] font-medium text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 bg-[#1e3a8a] hover:bg-blue-800 disabled:opacity-60 rounded-xl flex items-center justify-center transition-all shadow-sm hover:shadow-md"
          >
            <i className="fas fa-paper-plane text-white text-sm"></i>
          </button>
        </form>

        <p className="text-[11px] text-slate-400 mt-3 text-center">
          Answers are based on verified university sources only.
        </p>
      </div>
    </div>
  );
};

export default ChatWindow;
