
import React from 'react';

interface SourceCodeViewerProps {
  isOpen: boolean;
  onClose: () => void;
}

const SourceCodeViewer: React.FC<SourceCodeViewerProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const pythonCode = `
import os
import json
import logging
from datetime import datetime
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Academic Project: FUUAST AI Academic Assistant
# Module: RAG Backend Logic (Semantic Processing Layer)

app = FastAPI()

# Configure Logging for Academic Evaluation
logging.basicConfig(
    filename='query_logs.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class QueryRequest(BaseModel):
    query: string
    user_id: string

class KnowledgeBase:
    def __init__(self, data_path: str):
        with open(data_path, 'r') as f:
            self.entries = json.load(f)
        self.vectorizer = TfidfVectorizer()
        self.stop_words = set(stopwords.words('english'))

    def preprocess(self, text: str) -> str:
        """
        1. Tokenization
        2. Lowercasing
        3. Stopword removal
        """
        tokens = word_tokenize(text.lower())
        filtered = [w for w in tokens if w.isalnum() and w not in self.stop_words]
        return " ".join(filtered)

    def get_relevant_context(self, user_query: str, top_k: int = 3) -> List[Dict]:
        """
        2. Semantic relevance scoring using Cosine Similarity
        """
        processed_query = self.preprocess(user_query)
        corpus = [self.preprocess(e['content']) for e in self.entries]
        
        # Add query to corpus for vectorization
        tfidf_matrix = self.vectorizer.fit_transform(corpus + [processed_query])
        
        # Calculate cosine similarity between query (last item) and entries
        similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
        
        # Rank and filter top entries
        ranked_indices = similarities.argsort()[::-1]
        
        results = []
        for idx in ranked_indices[:top_k]:
            if similarities[idx] > 0.15: # Confidence threshold
                results.append({
                    **self.entries[idx],
                    "confidence_score": float(similarities[idx])
                })
        
        return results

kb = KnowledgeBase('fuuast_records.json')

@app.post("/api/v1/process-query")
async def process_academic_query(request: QueryRequest):
    # Log the incoming query
    logging.info(f"User: {request.user_id} | Query: {request.query}")
    
    try:
        # Step 3: Context Filtering
        context = kb.get_relevant_context(request.query)
        
        # Step 4: Log evaluation metrics
        avg_confidence = sum(c['confidence_score'] for c in context) / len(context) if context else 0
        logging.info(f"Response Category: {context[0]['category'] if context else 'None'} | Confidence: {avg_confidence}")
        
        return {
            "status": "success",
            "context": context,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "model_instructions": "official_academic_tone"
            }
        }
    except Exception as e:
        logging.error(f"Processing Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal processing error")
`;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm">
      <div className="bg-[#1e1e1e] w-full max-w-4xl h-[80vh] rounded-2xl shadow-2xl flex flex-col border border-slate-700 overflow-hidden animate-in fade-in zoom-in duration-200">
        {/* Editor Header */}
        <div className="bg-[#2d2d2d] px-4 py-3 flex items-center justify-between border-b border-slate-700">
          <div className="flex items-center gap-4">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <div className="w-3 h-3 rounded-full bg-amber-500"></div>
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
            </div>
            <div className="flex items-center gap-2 bg-[#1e1e1e] px-4 py-1.5 rounded-t-lg border-t border-x border-slate-700 -mb-3 ml-2">
              <i className="fab fa-python text-blue-400"></i>
              <span className="text-xs text-slate-300 font-mono">backend_logic.py</span>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <i className="fas fa-times"></i>
          </button>
        </div>

        {/* Code Content */}
        <div className="flex-1 overflow-auto p-6 font-mono text-sm leading-relaxed chat-scroll">
          <pre className="text-slate-300">
            {pythonCode.split('\n').map((line, i) => (
              <div key={i} className="flex gap-6 group">
                <span className="w-8 text-right text-slate-600 select-none">{i + 1}</span>
                <span className={
                  line.trim().startsWith('#') ? 'text-green-600' :
                  line.trim().startsWith('class') || line.trim().startsWith('def') ? 'text-blue-400' :
                  line.includes('"') || line.includes("'") ? 'text-amber-300' :
                  'text-slate-300'
                }>
                  {line}
                </span>
              </div>
            ))}
          </pre>
        </div>

        {/* Editor Footer */}
        <div className="bg-[#2d2d2d] px-4 py-2 flex items-center justify-between text-[10px] text-slate-500 border-t border-slate-700">
          <div className="flex gap-4 uppercase tracking-widest font-bold">
            <span>Python 3.10</span>
            <span>UTF-8</span>
            <span>FastAPI Layer</span>
          </div>
          <div className="flex gap-2">
            <i className="fas fa-check-circle text-green-500"></i>
            <span>System Ready</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SourceCodeViewer;
