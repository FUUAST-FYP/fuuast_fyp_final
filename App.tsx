import React, { useEffect, useState } from "react";
import ChatWindow from "./components/ChatWindow";

const App: React.FC = () => {
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    // Prevent background scrolling when the chat is open (mobile UX)
    document.body.style.overflow = isChatOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [isChatOpen]);

  const features = [
    {
      title: "Verified Information",
      desc: "Answers cite official FUUAST pages, notices, prospectus, and documents. No guessing.",
      icon: "fa-circle-check",
    },
    {
      title: "Timetable & Sections",
      desc: "Ask for BS1A Monday schedule, rooms, labs, and sessions — get instant results.",
      icon: "fa-calendar-days",
    },
    {
      title: "Teacher Availability",
      desc: "Find which teacher is free at a specific day/time. Save time and avoid office visits.",
      icon: "fa-user-clock",
    },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Top Nav */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-slate-200 px-4 sm:px-8 py-3 sm:py-4 flex items-center justify-between sticky top-0 z-40 shadow-sm">
        <div className="flex items-center gap-3 sm:gap-4 group cursor-pointer">
          <div className="w-11 h-11 sm:w-12 sm:h-12 bg-[var(--brand-700)] rounded-xl flex items-center justify-center text-white shadow-lg transform group-hover:scale-105 transition-transform">
            <i className="fas fa-university text-2xl"></i>
          </div>
          <div>
            <h1 className="text-lg sm:text-xl font-black text-[var(--brand-700)] tracking-tight leading-none">
              FUUAST
            </h1>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.2em] mt-1">
              Gulshan Campus, Karachi
            </p>
          </div>
        </div>

        <div className="hidden lg:flex items-center gap-10 text-sm font-semibold text-slate-600">
          <a className="hover:text-[var(--brand-700)] transition-colors" href="#">
            Admissions
          </a>
          <a className="hover:text-[var(--brand-700)] transition-colors" href="#">
            Faculties
          </a>
          <a className="hover:text-[var(--brand-700)] transition-colors" href="#">
            Examinations
          </a>
          <a className="hover:text-[var(--brand-700)] transition-colors" href="#">
            Campus Life
          </a>
          <button className="bg-[var(--brand-700)] text-white px-7 py-2.5 rounded-full font-bold hover:bg-[var(--brand-800)] transition-all shadow-md hover:shadow-xl active:scale-95">
            Apply Now
          </button>
        </div>

        {/* Mobile CTA */}
        <button
          onClick={() => setIsChatOpen(true)}
          className="lg:hidden bg-[var(--brand-700)] text-white px-4 py-2 rounded-xl text-sm font-bold hover:bg-[var(--brand-800)] active:scale-95 transition-all"
        >
          Open UniBot
        </button>
      </nav>

      {/* HERO (Poster-like) */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[var(--brand-900)]" />
        <div className="absolute inset-0 opacity-25">
          <img
            src="https://fuuast.edu.pk/wp-content/uploads/2015/08/3-e1453894762294.png"
            alt="FUUAST"
            className="w-full h-full object-cover"
          />
        </div>
        <div className="absolute inset-0 bg-gradient-to-r from-black/60 via-black/30 to-transparent" />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-8 py-14 sm:py-20">
          <div className="grid lg:grid-cols-2 gap-10 items-start">
            {/* Left */}
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 bg-white/10 text-white/90 border border-white/15 px-4 py-2 rounded-full text-xs font-extrabold tracking-widest uppercase">
                <span className="w-2 h-2 rounded-full bg-[var(--accent-500)]" />
                AI Chatbot • UniBot • Verified
              </div>

              <h2 className="mt-7 text-4xl sm:text-5xl font-black text-white leading-tight">
                Official Answers{" "}
                <span className="text-[var(--accent-500)]">in Seconds</span>
              </h2>

              <p className="mt-5 text-slate-200 text-base sm:text-lg leading-relaxed">
                UniBot is a RAG-powered AI helpdesk that responds using verified
                FUUAST documents only — admissions, fees, timetables, rules, and
                notices.
              </p>

              <ul className="mt-7 space-y-3 text-slate-100 text-sm sm:text-base">
                <li className="flex gap-3">
                  <span className="mt-1 text-[var(--accent-500)]">
                    <i className="fas fa-check-circle"></i>
                  </span>
                  <span>
                    <b>Verified answers</b> — official sources shown for every response
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="mt-1 text-[var(--accent-500)]">
                    <i className="fas fa-check-circle"></i>
                  </span>
                  <span>
                    <b>No guessing</b> — says “Not found” if info isn’t in documents
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="mt-1 text-[var(--accent-500)]">
                    <i className="fas fa-check-circle"></i>
                  </span>
                  <span>
                    <b>Timetable + availability</b> — ask day/section and get results instantly
                  </span>
                </li>
              </ul>

              <div className="mt-9 flex flex-col sm:flex-row gap-4">
                <button
                  onClick={() => setIsChatOpen(true)}
                  className="bg-[var(--brand-700)] text-white px-8 py-4 rounded-2xl font-black hover:bg-[var(--brand-800)] transition-all shadow-2xl shadow-black/25 active:scale-95"
                >
                  <i className="fas fa-robot mr-2" />
                  Try UniBot
                </button>

                <button className="bg-white/10 border border-white/20 text-white px-8 py-4 rounded-2xl font-bold hover:bg-white/15 transition-all active:scale-95">
                  <i className="fas fa-circle-info mr-2" />
                  How it works
                </button>
              </div>
            </div>

            {/* Right: 01/02/03 Feature Cards */}
            <div className="grid gap-5">
              {features.map((f, idx) => {
                const num = String(idx + 1).padStart(2, "0");
                return (
                  <div
                    key={f.title}
                    className="relative bg-white rounded-3xl border border-slate-100 shadow-xl p-6 sm:p-7 overflow-hidden"
                  >
                    <div className="absolute -right-4 -top-8 text-[96px] font-black text-slate-100 select-none">
                      {idx + 1}
                    </div>

                    <div className="flex items-start gap-4 relative z-10">
                      <div className="w-12 h-12 rounded-2xl bg-[var(--brand-700)] text-white flex items-center justify-center shadow-md">
                        <i className={`fas ${f.icon} text-lg`} />
                      </div>

                      <div className="min-w-0">
                        <div className="text-xs font-black tracking-widest text-slate-400">
                          {num}
                        </div>
                        <h3 className="text-lg font-black text-slate-900 mt-1">
                          {f.title}
                        </h3>
                        <p className="text-slate-600 mt-2 leading-relaxed text-sm">
                          {f.desc}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}

              <div className="bg-white/10 border border-white/15 rounded-3xl p-6 text-white">
                <div className="font-black tracking-widest text-[var(--accent-500)] text-xs">
                  RAG-POWERED
                </div>
                <div className="mt-2 text-sm text-slate-100/90 leading-relaxed">
                  Retrieval-Augmented Generation: UniBot answers only from verified FUUAST sources.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Floating Action Button */}
      {!isChatOpen && (
        <button
          onClick={() => setIsChatOpen(true)}
          className="fixed bottom-4 right-4 sm:bottom-8 sm:right-8 w-14 h-14 sm:w-16 sm:h-16 bg-[var(--brand-700)] text-white rounded-2xl shadow-2xl flex items-center justify-center hover:bg-[var(--brand-800)] hover:scale-105 active:scale-95 transition-all z-50"
          aria-label="Open UniBot"
        >
          <i className="fas fa-comment-dots text-2xl"></i>
        </button>
      )}

      <ChatWindow isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
};

export default App;
