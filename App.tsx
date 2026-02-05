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

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Top Banner / Navigation */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-slate-200 px-4 sm:px-8 py-3 sm:py-4 flex items-center justify-between sticky top-0 z-40 shadow-sm">
        <div className="flex items-center gap-3 sm:gap-4 group cursor-pointer">
          <div className="w-11 h-11 sm:w-12 sm:h-12 bg-emerald-700 rounded-xl flex items-center justify-center text-white shadow-lg transform group-hover:scale-105 transition-transform">
            <i className="fas fa-university text-2xl"></i>
          </div>
          <div>
            <h1 className="text-lg sm:text-xl font-black text-emerald-800 tracking-tight leading-none">
              FUUAST
            </h1>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.2em] mt-1">
              Gulshan Campus, Karachi
            </p>
          </div>
        </div>

        <div className="hidden lg:flex items-center gap-10 text-sm font-semibold text-slate-600">
          <a
            href="#"
            className="hover:text-emerald-700 transition-colors relative after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-[2px] after:bg-emerald-700 hover:after:w-full after:transition-all"
          >
            Admissions
          </a>
          <a
            href="#"
            className="hover:text-emerald-700 transition-colors relative after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-[2px] after:bg-emerald-700 hover:after:w-full after:transition-all"
          >
            Faculties
          </a>
          <a
            href="#"
            className="hover:text-emerald-700 transition-colors relative after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-[2px] after:bg-emerald-700 hover:after:w-full after:transition-all"
          >
            Examinations
          </a>
          <a
            href="#"
            className="hover:text-emerald-700 transition-colors relative after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-[2px] after:bg-emerald-700 hover:after:w-full after:transition-all"
          >
            Campus Life
          </a>
          <button className="bg-emerald-700 text-white px-7 py-2.5 rounded-full font-bold hover:bg-emerald-800 transition-all shadow-md hover:shadow-xl active:scale-95">
            Apply Now
          </button>
        </div>

        {/* Mobile CTA */}
        <button
          onClick={() => setIsChatOpen(true)}
          className="lg:hidden bg-emerald-700 text-white px-4 py-2 rounded-xl text-sm font-bold hover:bg-emerald-800 active:scale-95 transition-all"
        >
          Assistant
        </button>
      </nav>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative min-h-[520px] sm:h-[600px] bg-[#0f172a] overflow-hidden">
          <div className="absolute inset-0 z-0">
            <img
              src="https://fuuast.edu.pk/wp-content/uploads/2015/08/3-e1453894762294.png"
              alt="University Library"
              className="w-full h-full object-cover opacity-40 scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-[#0f172a] via-transparent to-transparent"></div>
          </div>

          <div className="relative z-10 max-w-7xl mx-auto h-full flex flex-col justify-center px-4 sm:px-8">
            <div className="max-w-3xl">
              <span className="inline-block bg-emerald-600/20 text-emerald-300 text-xs font-black px-4 py-1.5 rounded-full uppercase tracking-widest mb-6 border border-emerald-500/30">
                Education for the Future
              </span>
              <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white mb-5 sm:mb-6 leading-tight drop-shadow-2xl">
                Advancing Knowledge, <br />
                <span className="text-emerald-300">Empowering Minds.</span>
              </h2>
              <p className="text-base sm:text-xl text-slate-300 mb-8 sm:mb-10 leading-relaxed font-light">
                Discover a community dedicated to intellectual growth and
                professional excellence at Pakistan&apos;s premier Urdu-medium
                university.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <button className="bg-white text-[#0f172a] px-8 sm:px-10 py-3.5 sm:py-4 rounded-xl font-black hover:bg-slate-100 transition-all shadow-xl shadow-white/5 active:scale-95 w-full sm:w-auto">
                  Explore Programs
                </button>
                <button
                  onClick={() => setIsChatOpen(true)}
                  className="bg-transparent border-2 border-white/30 text-white px-8 sm:px-10 py-3.5 sm:py-4 rounded-xl font-bold hover:bg-white/10 hover:border-white transition-all backdrop-blur-sm active:scale-95 w-full sm:w-auto"
                >
                  Virtual Assistant
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Info Blocks */}
        <section className="py-16 sm:py-24 px-4 sm:px-8 max-w-7xl mx-auto">
          <div className="grid md:grid-cols-3 gap-6 sm:gap-8">
            {[
              {
                icon: "fa-book-reader",
                title: "Quality Education",
                desc: "Curriculum designed to meet global standards with local relevance.",
                color: "emerald",
              },
              {
                icon: "fa-microscope",
                title: "Research & Innovation",
                desc: "Promoting critical thinking and indigenous scientific research.",
                color: "emerald",
              },
              {
                icon: "fa-award",
                title: "Accreditation",
                desc: "Recognized by HEC and professional accreditation councils.",
                color: "emerald",
              },
            ].map((item, idx) => (
              <div
                key={idx}
                className="bg-white p-7 sm:p-10 rounded-3xl border border-slate-100 shadow-sm hover:shadow-xl transition-all group hover:-translate-y-1"
              >
                <div
                  className={`w-14 h-14 sm:w-16 sm:h-16 bg-${item.color}-50 rounded-2xl flex items-center justify-center text-${item.color}-700 mb-7 sm:mb-8 group-hover:scale-110 transition-transform`}
                >
                  <i className={`fas ${item.icon} text-2xl`}></i>
                </div>
                <h3 className="text-lg sm:text-xl font-black text-slate-800 mb-3 sm:mb-4">
                  {item.title}
                </h3>
                <p className="text-slate-500 leading-relaxed text-sm">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* FYP Showcase Notice */}
        <section className="bg-slate-900 py-16 sm:py-20 px-4 sm:px-8 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl -mr-48 -mt-48"></div>
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-emerald-600/10 rounded-full blur-3xl -ml-32 -mb-32"></div>

          <div className="max-w-4xl mx-auto relative z-10 text-center">
            <span className="bg-white/10 text-white/70 text-[10px] font-black px-4 py-1 rounded-full uppercase tracking-[0.3em] mb-6 inline-block">
              FYP Project Demonstration
            </span>
            <h4 className="text-2xl sm:text-3xl font-black text-white mb-5 sm:mb-6 tracking-tight">
              AI-Powered Institutional Support
            </h4>
            <p className="text-slate-400 mb-8 sm:mb-10 text-base sm:text-lg leading-relaxed max-w-2xl mx-auto">
              This system demonstrates a fully integrated{" "}
              <strong>Retrieval-Augmented Generation (RAG)</strong> stack. The
              frontend connects to a document-grounded AI that utilizes semantic
              search logic implemented in Python.
            </p>

            <div className="flex flex-col sm:flex-row justify-center gap-5 sm:gap-6">
              <button
                onClick={() => setIsChatOpen(true)}
                className="bg-emerald-600 text-white px-10 sm:px-12 py-4 sm:py-5 rounded-2xl font-black text-base sm:text-lg flex items-center justify-center gap-4 hover:bg-emerald-700 transition-all shadow-2xl shadow-emerald-500/20 active:scale-95"
              >
                <i className="fas fa-robot"></i>
                Try AI Helpdesk
              </button>
            </div>
          </div>
        </section>
      </main>

      {/* Floating Action Button */}
      {!isChatOpen && (
        <button
          onClick={() => setIsChatOpen(true)}
          className="fixed bottom-4 right-4 sm:bottom-8 sm:right-8 w-14 h-14 sm:w-16 sm:h-16 bg-emerald-700 text-white rounded-2xl shadow-2xl flex items-center justify-center hover:bg-emerald-800 hover:scale-105 active:scale-95 transition-all z-50 group overflow-hidden"
          aria-label="Open assistant"
        >
          <i className="fas fa-comment-alt text-2xl"></i>
        </button>
      )}

      <ChatWindow isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
};

export default App;
