
import React, { useState } from 'react';
import ChatWindow from './components/ChatWindow';

const App: React.FC = () => {
  const [isChatOpen, setIsChatOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Top Banner / Navigation */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-slate-200 px-8 py-4 flex items-center justify-between sticky top-0 z-40 shadow-sm">
        <div className="flex items-center gap-4 group cursor-pointer">
          <div className="w-12 h-12 bg-[#1e3a8a] rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-900/20 transform group-hover:scale-105 transition-transform">
            <i className="fas fa-university text-2xl"></i>
          </div>
          <div>
            <h1 className="text-xl font-black text-[#1e3a8a] tracking-tight leading-none">FUUAST</h1>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.2em] mt-1">Gulshan Campus, Karachi</p>
          </div>
        </div>
        
        <div className="hidden lg:flex items-center gap-10 text-sm font-semibold text-slate-600">
          <a href="#" className="hover:text-[#1e3a8a] transition-colors relative after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-[2px] after:bg-[#1e3a8a] hover:after:w-full after:transition-all">Admissions</a>
          <a href="#" className="hover:text-[#1e3a8a] transition-colors relative after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-[2px] after:bg-[#1e3a8a] hover:after:w-full after:transition-all">Faculties</a>
          <a href="#" className="hover:text-[#1e3a8a] transition-colors relative after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-[2px] after:bg-[#1e3a8a] hover:after:w-full after:transition-all">Examinations</a>
          <a href="#" className="hover:text-[#1e3a8a] transition-colors relative after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-[2px] after:bg-[#1e3a8a] hover:after:w-full after:transition-all">Campus Life</a>
          <button className="bg-[#1e3a8a] text-white px-7 py-2.5 rounded-full font-bold hover:bg-blue-800 transition-all shadow-md hover:shadow-xl active:scale-95">
            Apply Now
          </button>
        </div>
      </nav>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative h-[600px] bg-[#0f172a] overflow-hidden">
          <div className="absolute inset-0 z-0">
            <img 
              src="https://fuuast.edu.pk/wp-content/uploads/2015/08/3-e1453894762294.png" 
              alt="University Library" 
              className="w-full h-full object-cover opacity-40 scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-[#0f172a] via-transparent to-transparent"></div>
          </div>
          
          <div className="relative z-10 max-w-7xl mx-auto h-full flex flex-col justify-center px-8">
            <div className="max-w-3xl animate-in slide-in-from-left duration-700">
              <span className="inline-block bg-blue-600/20 text-blue-400 text-xs font-black px-4 py-1.5 rounded-full uppercase tracking-widest mb-6 border border-blue-500/30">
                Education for the Future
              </span>
              <h2 className="text-6xl font-black text-white mb-6 leading-tight drop-shadow-2xl">
                Advancing Knowledge, <br/>
                <span className="text-blue-400">Empowering Minds.</span>
              </h2>
              <p className="text-xl text-slate-300 mb-10 leading-relaxed font-light">
                Discover a community dedicated to intellectual growth and professional excellence at Pakistan's premier Urdu-medium university.
              </p>
              <div className="flex gap-4">
                <button className="bg-white text-[#0f172a] px-10 py-4 rounded-xl font-black hover:bg-slate-100 transition-all shadow-xl shadow-white/5 active:scale-95">
                  Explore Programs
                </button>
                <button 
                  onClick={() => setIsChatOpen(true)}
                  className="bg-transparent border-2 border-white/30 text-white px-10 py-4 rounded-xl font-bold hover:bg-white/10 hover:border-white transition-all backdrop-blur-sm active:scale-95"
                >
                  Virtual Assistant
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Info Blocks */}
        <section className="py-24 px-8 max-w-7xl mx-auto">
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: 'fa-book-reader', title: 'Quality Education', desc: 'Curriculum designed to meet global standards with local relevance.', color: 'blue' },
              { icon: 'fa-microscope', title: 'Research & Innovation', desc: 'Promoting critical thinking and indigenous scientific research.', color: 'emerald' },
              { icon: 'fa-award', title: 'Accreditation', desc: 'Recognized by HEC and professional accreditation councils.', color: 'amber' }
            ].map((item, idx) => (
              <div key={idx} className="bg-white p-10 rounded-3xl border border-slate-100 shadow-sm hover:shadow-xl transition-all group hover:-translate-y-2">
                <div className={`w-16 h-16 bg-${item.color}-50 rounded-2xl flex items-center justify-center text-${item.color}-600 mb-8 group-hover:scale-110 transition-transform`}>
                  <i className={`fas ${item.icon} text-2xl`}></i>
                </div>
                <h3 className="text-xl font-black text-slate-800 mb-4">{item.title}</h3>
                <p className="text-slate-500 leading-relaxed text-sm">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </section>
        
        {/* FYP Showcase Notice */}
        <section className="bg-slate-900 py-20 px-8 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl -mr-48 -mt-48"></div>
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-emerald-600/10 rounded-full blur-3xl -ml-32 -mb-32"></div>
          
          <div className="max-w-4xl mx-auto relative z-10 text-center">
            <span className="bg-white/10 text-white/60 text-[10px] font-black px-4 py-1 rounded-full uppercase tracking-[0.3em] mb-6 inline-block">
              FYP Project Demonstration
            </span>
            <h4 className="text-3xl font-black text-white mb-6 tracking-tight">AI-Powered Institutional Support</h4>
            <p className="text-slate-400 mb-10 text-lg leading-relaxed max-w-2xl mx-auto">
              This system demonstrates a fully integrated <strong>Retrieval-Augmented Generation (RAG)</strong> stack. 
              The frontend connects to a document-grounded AI that utilizes semantic search logic implemented in Python.
            </p>
            
            <div className="flex flex-col sm:flex-row justify-center gap-6">
              <button 
                onClick={() => setIsChatOpen(true)}
                className="bg-blue-600 text-white px-12 py-5 rounded-2xl font-black text-lg flex items-center justify-center gap-4 hover:bg-blue-700 transition-all shadow-2xl shadow-blue-500/20 active:scale-95"
              >
                <i className="fas fa-robot"></i>
                Try AI Helpdesk
              </button>
            </div>

            <div className="mt-12 flex flex-wrap justify-center gap-8 opacity-40 grayscale hover:grayscale-0 transition-all">
              <span className="text-xs font-bold text-white uppercase tracking-widest flex items-center gap-2"><i className="fab fa-python text-lg"></i> Python Backend</span>
              <span className="text-xs font-bold text-white uppercase tracking-widest flex items-center gap-2"><i className="fas fa-brain text-lg"></i> RAG Principles</span>
              <span className="text-xs font-bold text-white uppercase tracking-widest flex items-center gap-2"><i className="fas fa-database text-lg"></i> Semantic Retrieval</span>
            </div>
          </div>
        </section>
      </main>

      {/* Modern Footer */}
      <footer className="bg-white border-t border-slate-200 pt-16 pb-8 px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-12 mb-16">
            <div className="col-span-2">
              <div className="flex items-center gap-3 mb-6">
                <i className="fas fa-university text-3xl text-[#1e3a8a]"></i>
                <span className="text-[#1e3a8a] font-black text-xl tracking-tighter">FUUAST GULSHAN</span>
              </div>
              <p className="text-slate-500 text-sm max-w-sm leading-relaxed">
                The Federal Urdu University of Arts, Science and Technology is a public research university with main campus in Islamabad and satellite campuses in Karachi.
              </p>
            </div>
            <div>
              <h5 className="font-black text-slate-800 uppercase text-xs tracking-widest mb-6">Explore</h5>
              <ul className="text-slate-500 text-sm space-y-3">
                <li><a href="#" className="hover:text-blue-600">Alumni Portal</a></li>
                <li><a href="#" className="hover:text-blue-600">Student Portal</a></li>
                <li><a href="#" className="hover:text-blue-600">E-Library</a></li>
                <li><a href="#" className="hover:text-blue-600">Job Opportunities</a></li>
              </ul>
            </div>
            <div>
              <h5 className="font-black text-slate-800 uppercase text-xs tracking-widest mb-6">Contact</h5>
              <ul className="text-slate-500 text-sm space-y-3">
                <li><i className="fas fa-map-marker-alt mr-2 text-blue-500"></i> University Road, Karachi</li>
                <li><i className="fas fa-phone mr-2 text-blue-500"></i> +92 21 99244141</li>
                <li><i className="fas fa-envelope mr-2 text-blue-500"></i> info@fuuast.edu.pk</li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t border-slate-100 flex flex-col md:flex-row justify-between items-center gap-4 text-slate-400">
            <p className="text-xs font-medium">© 2024 Federal Urdu University. All Rights Reserved.</p>
            <div className="flex gap-6 text-sm">
              <a href="#" className="hover:text-slate-900 transition-colors"><i className="fab fa-facebook-f"></i></a>
              <a href="#" className="hover:text-slate-900 transition-colors"><i className="fab fa-twitter"></i></a>
              <a href="#" className="hover:text-slate-900 transition-colors"><i className="fab fa-linkedin-in"></i></a>
            </div>
            <p className="text-[10px] font-black uppercase tracking-widest opacity-60">CS Department FYP Project</p>
          </div>
        </div>
      </footer>

      {/* Floating Action Button */}
      {!isChatOpen && (
        <button 
          onClick={() => setIsChatOpen(true)}
          className="fixed bottom-8 right-8 w-16 h-16 bg-[#1e3a8a] text-white rounded-2xl shadow-2xl shadow-blue-900/30 flex items-center justify-center hover:bg-blue-800 hover:scale-105 active:scale-95 transition-all z-50 group overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/10 to-transparent transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
          <i className="fas fa-comment-alt text-2xl"></i>
          <span className="absolute -top-12 right-0 bg-slate-900 text-white text-[10px] px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap font-black uppercase tracking-widest">
            AI Helpdesk
          </span>
        </button>
      )}

      <ChatWindow isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
};

export default App;
