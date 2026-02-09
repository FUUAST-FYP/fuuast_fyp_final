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

  // Smooth scroll to section
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // Open chat and scroll to it
  const openChatScrolled = () => {
    setIsChatOpen(true);
    // Scroll to chat after a brief delay to ensure it's rendered
    setTimeout(() => {
      const chatElement = document.getElementById("try-now");
      if (chatElement) {
        chatElement.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }, 100);
  };

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
          <button onClick={() => scrollToSection("features")} className="hover:text-[var(--brand-700)] transition-colors bg-none border-none cursor-pointer"
          >
            Features
          </button>
          <button onClick={() => scrollToSection("how-it-works")} className="hover:text-[var(--brand-700)] transition-colors bg-none border-none cursor-pointer"
          >
            How it Works
          </button>
          <button onClick={() => scrollToSection("faq")} className="hover:text-[var(--brand-700)] transition-colors bg-none border-none cursor-pointer"
          >
            FAQ
          </button>
          <button onClick={() => scrollToSection("contact")} className="hover:text-[var(--brand-700)] transition-colors bg-none border-none cursor-pointer"
          >
            Contact
          </button>
          <button onClick={() => openChatScrolled()} className="bg-[var(--brand-700)] text-white px-7 py-2.5 rounded-full font-bold hover:bg-[var(--brand-800)] transition-all shadow-md hover:shadow-xl active:scale-95">
            Try Now
          </button>
        </div>

        {/* Mobile CTA */}
        <button
          onClick={() => openChatScrolled()}
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
                  onClick={() => openChatScrolled()}
                  className="bg-[var(--brand-700)] text-white px-8 py-4 rounded-2xl font-black hover:bg-[var(--brand-800)] transition-all shadow-2xl shadow-black/25 active:scale-95"
                >
                  <i className="fas fa-robot mr-2" />
                  Try UniBot
                </button>

                <button onClick={() => scrollToSection("how-it-works")} className="bg-white/10 border border-white/20 text-white px-8 py-4 rounded-2xl font-bold hover:bg-white/15 transition-all active:scale-95">
                  <i className="fas fa-circle-info mr-2" />
                  How it works
                </button>
              </div>
            </div>

            {/* Right: 01/02/03 Feature Cards */}
            <div id="features" className="grid gap-5">
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

      {/* How It Works Section */}
      <section id="how-it-works" className="max-w-7xl mx-auto px-4 sm:px-8 py-20 sm:py-28">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-black text-slate-900">How UniBot Works</h2>
          <p className="mt-4 text-slate-600 max-w-2xl mx-auto text-lg">
            Three simple steps to get verified answers about FUUAST in seconds
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            { step: "1", title: "Ask", desc: "Type your question naturally — admissions, timetables, fees, or any FUUAST topic." },
            { step: "2", title: "Search", desc: "UniBot searches verified FUUAST documents using RAG technology." },
            { step: "3", title: "Answer", desc: "Get sources cited for every response. Click links for official pages." }
          ].map((item) => (
            <div key={item.step} className="bg-white rounded-2xl p-8 border border-slate-200 shadow-md hover:shadow-lg transition-all">
              <div className="w-12 h-12 rounded-full bg-[var(--brand-700)] text-white flex items-center justify-center font-black text-lg mb-4">
                {item.step}
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">{item.title}</h3>
              <p className="text-slate-600 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features Showcase Section */}
      <section id="faq" className="bg-slate-900 text-white py-20 sm:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-black">FAQ</h2>
            <p className="mt-4 text-slate-300 max-w-2xl mx-auto text-lg">
              Common questions about UniBot
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {[
              { q: "Is UniBot always accurate?", a: "UniBot only answers from verified FUUAST sources. If info isn't in documents, it says so." },
              { q: "Does it work for admissions queries?", a: "Yes! Ask about programs, fee structures, merit requirements, deadlines — all from official docs." },
              { q: "Can it check teacher schedules?", a: "Yes! Ask 'Is Dr Uzma free Monday?' or 'BS1A Friday timetable' for instant results." },
              { q: "Is my data safe?", a: "UniBot doesn't store personal data. Conversation history is session-based only." }
            ].map((item, idx) => (
              <div key={idx} className="bg-white/10 border border-white/20 rounded-2xl p-6">
                <h3 className="font-bold text-lg mb-2">{item.q}</h3>
                <p className="text-slate-300 text-sm leading-relaxed">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="max-w-7xl mx-auto px-4 sm:px-8 py-20 sm:py-28">
        <div className="bg-gradient-to-br from-[var(--brand-700)] to-[var(--brand-800)] rounded-3xl p-10 sm:p-16 text-white text-center">
          <h2 className="text-3xl sm:text-4xl font-black mb-4">Ready to Get Started?</h2>
          <p className="text-lg text-white/90 mb-8 max-w-2xl mx-auto">
            Open UniBot below and ask your first question. Get verified answers about FUUAST in seconds.
          </p>
          <button
            onClick={() => openChatScrolled()}
            className="bg-white text-[var(--brand-700)] px-10 py-4 rounded-full font-bold text-lg hover:bg-slate-100 transition-all shadow-xl active:scale-95"
          >
            <i className="fas fa-robot mr-2" />
            Try UniBot Now
          </button>
        </div>
      </section>

      {/* Chat Widget Section */}
      <section id="try-now" className="max-w-7xl mx-auto px-4 sm:px-8 py-12">
        <div className="text-center mb-6">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Start Chatting with UniBot</h2>
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
