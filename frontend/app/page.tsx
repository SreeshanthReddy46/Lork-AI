"use client";

import React, { useState, useEffect } from "react";
import { 
  Search, 
  Globe, 
  Database, 
  ArrowRight, 
  BookOpen, 
  Layers, 
  Plus, 
  X,
  Sparkles,
  ExternalLink,
  Menu,
  ChevronLeft,
  ChevronRight
} from "lucide-react";

import AnswerCard from "../components/AnswerCard";
import SourceList from "../components/SourceList";
import GraphViewer from "../components/GraphViewer";

export default function Home() {
  // Search state
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [researchMode, setResearchMode] = useState(false);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [activeQuestion, setActiveQuestion] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showGraphDrawer, setShowGraphDrawer] = useState(false);
  
  // Pipeline response state
  const [result, setResult] = useState<{
    query: string;
    report: { title: string; content: string; raw_cited_text?: string };
    sources: any[];
    graph: { nodes: any[]; links: any[] };
    recommendations: string[];
  } | null>(null);

  // Dynamic crawl ingestion states
  const [crawlUrl, setCrawlUrl] = useState("");
  const [isCrawling, setIsCrawling] = useState(false);
  const [showCrawlDrawer, setShowCrawlDrawer] = useState(false);
  const [crawlStatus, setCrawlStatus] = useState<{
    pages_crawled: number;
    queue_stats: Record<string, number>;
    recent_queue: any[];
  } | null>(null);

  // Spotlight mouse track coordinates
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  const fetchCrawlStats = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/crawl/status");
      if (res.ok) {
        const data = await res.json();
        setCrawlStatus(data);
        const activeCount = (data.queue_stats.crawling || 0) + (data.queue_stats.pending || 0);
        setIsCrawling(activeCount > 0);
      }
    } catch (err) {
      console.error("Failed to fetch crawl status:", err);
    }
  };

  const fetchSearchHistory = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/history");
      if (res.ok) {
        const data = await res.json();
        setSearchHistory(data.map((h: any) => h.query));
      }
    } catch (err) {
      console.error("Failed to fetch search history:", err);
    }
  };

  useEffect(() => {
    fetchCrawlStats();
    fetchSearchHistory();
    const interval = setInterval(() => {
      fetchCrawlStats();
    }, 4500);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const handleSearch = async (e?: React.FormEvent, customQuery?: string) => {
    if (e) e.preventDefault();
    const activeQuery = customQuery || query;
    if (!activeQuery || !activeQuery.trim()) return;
    
    setActiveQuestion(activeQuery);
    setQuery(""); // Clear the input box instantly!
    setIsSearching(true);
    setResult(null);

    const headers: Record<string, string> = {};
    if (process.env.NEXT_PUBLIC_API_KEY) {
      headers["x-api-key"] = process.env.NEXT_PUBLIC_API_KEY;
    }

    try {
      const res = await fetch(`http://localhost:8000/api/search?q=${encodeURIComponent(activeQuery)}`, {
        headers
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
        fetchSearchHistory();
      } else if (res.status === 401) {
        alert("Unauthorized request. Please configure NEXT_PUBLIC_API_KEY.");
      } else {
        alert("Search failed. Ensure backend server is running.");
      }
    } catch (err) {
      console.error("Search error:", err);
      alert("Backend API is unreachable. Start FastAPI server first!");
    } finally {
      setIsSearching(false);
    }
  };

  const handleCrawl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!crawlUrl || !crawlUrl.trim()) return;
    
    setIsCrawling(true);
    const headers: Record<string, string> = {
      "Content-Type": "application/json"
    };
    if (process.env.NEXT_PUBLIC_API_KEY) {
      headers["x-api-key"] = process.env.NEXT_PUBLIC_API_KEY;
    }

    try {
      const res = await fetch("http://localhost:8000/api/crawl", {
        method: "POST",
        headers,
        body: JSON.stringify({
          url: crawlUrl,
          max_pages: researchMode ? 15 : 5,
          max_depth: researchMode ? 2 : 1
        })
      });
      if (res.ok) {
        alert(`Indexing triggered for: ${crawlUrl}`);
        setCrawlUrl("");
        fetchCrawlStats();
      } else {
        alert("Crawl request failed.");
      }
    } catch (err) {
      console.error("Crawl error:", err);
    }
  };

  const isLanding = !result && !isSearching;

  return (
    <div className="relative min-h-screen bg-[#080808] text-white font-mono overflow-x-hidden flex">
      {/* Collapsible Left Sidebar */}
      <aside 
        className={`fixed top-0 left-0 bottom-0 z-50 bg-[#090909] border-r border-neutral-900/60 flex flex-col p-5 transition-all duration-300 ease-in-out select-none
          ${sidebarOpen ? "translate-x-0 w-64" : "-translate-x-full w-64"}`}
      >
        {/* Sidebar Header */}
        <div className="flex justify-between items-center border-b border-neutral-950 pb-3 mb-6 select-none">
          <button 
            type="button"
            onClick={() => {
              setResult(null);
              setIsSearching(false);
              setActiveQuestion("");
              setQuery("");
            }}
            className="flex items-center space-x-2 text-white hover:opacity-80 transition cursor-pointer bg-transparent border-none"
          >
            <Globe className="w-4 h-4 text-white" />
            <span className="text-xs font-bold uppercase tracking-widest">LORK-AI</span>
          </button>
          <button
            type="button"
            onClick={() => setSidebarOpen(false)}
            className="text-neutral-500 hover:text-white transition cursor-pointer border-none bg-transparent"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        </div>

        {/* Action buttons */}
        <button
          type="button"
          onClick={() => {
            setResult(null);
            setIsSearching(false);
            setActiveQuestion("");
            setQuery("");
          }}
          className="w-full py-2 bg-white text-black font-mono font-bold text-xs uppercase tracking-wider hover:bg-neutral-200 transition rounded flex items-center justify-center space-x-1.5 mb-4 cursor-pointer border-none shadow-md"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Search</span>
        </button>

        {/* Ingest button */}
        <button
          type="button"
          onClick={() => setShowCrawlDrawer(true)}
          className="w-full py-2 border border-neutral-800 hover:bg-neutral-950 text-neutral-400 hover:text-white transition rounded text-[10px] font-bold uppercase tracking-wider mb-6 flex items-center justify-center space-x-1.5 cursor-pointer bg-transparent"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Ingest URL</span>
        </button>

        {/* History list */}
        <div className="flex-1 flex flex-col min-h-0">
          <span className="text-[9px] text-neutral-600 uppercase tracking-widest font-bold block mb-3 select-none">
            Search History
          </span>
          {searchHistory.length === 0 ? (
            <div className="text-[10px] text-neutral-600 italic select-none">No history yet</div>
          ) : (
            <div className="space-y-1.5 overflow-y-auto max-h-[calc(100vh-280px)] pr-2 scrollbar-thin">
              {searchHistory.slice(0, 15).map((h_query, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setQuery("");
                    handleSearch(undefined, h_query);
                  }}
                  className="w-full text-left truncate font-mono text-[11px] text-neutral-400 hover:text-white bg-transparent hover:bg-neutral-950 px-2 py-1.5 rounded transition cursor-pointer border-none"
                  title={h_query}
                >
                  ↳ {h_query}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="border-t border-neutral-950 pt-4 mt-auto select-none">
          <div className="flex items-center space-x-2 border border-neutral-900 bg-[#0c0c0c] px-2.5 py-1.5 rounded text-[10px] text-neutral-400 select-none">
            <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
            <span>INDEX: {crawlStatus?.pages_crawled || 0} PAGES</span>
          </div>
        </div>
      </aside>

      {/* Main Workspace Area */}
      <div 
        className={`flex-grow min-h-screen flex flex-col transition-all duration-300 ease-in-out relative
          ${sidebarOpen ? "md:pl-64" : "md:pl-0"}`}
      >
        {/* Sidebar Toggle Button (floating when closed) */}
        {!sidebarOpen && (
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="fixed top-4 left-4 z-50 bg-[#090909] border border-neutral-900 p-2 rounded hover:bg-neutral-950 transition text-neutral-400 hover:text-white cursor-pointer flex items-center justify-center shadow-lg"
          >
            <Menu className="w-4 h-4" />
          </button>
        )}

        {/* Background Spotlight Tracking */}
        <div 
          style={{
            background: `radial-gradient(500px circle at ${mousePos.x}px ${mousePos.y}px, rgba(255,255,255,0.015), transparent 80%)`,
          }}
          className="pointer-events-none fixed inset-0 z-30"
        />

        {/* Center Landing / Bottom Settled Search Container */}
        <div 
          className={`fixed transition-all duration-700 ease-in-out z-40 w-full px-6
            ${sidebarOpen ? "left-[calc(50%+128px)]" : "left-1/2"} -translate-x-1/2
            ${isLanding 
              ? "top-1/2 -translate-y-1/2 max-w-xl text-center" 
              : "top-[calc(100%-80px)] -translate-y-1/2 max-w-2xl bg-[#080808]/90 backdrop-blur-md border border-neutral-900/60 p-3 rounded-lg shadow-2xl"
            }`}
        >
          {/* Landing Logo */}
          <div className={`transition-all duration-500 select-none ${isLanding ? "opacity-100 max-h-40 mb-6" : "opacity-0 max-h-0 overflow-hidden pointer-events-none mb-0"}`}>
            <h2 className="text-3xl font-extrabold tracking-[0.25em] text-white">LORK-AI</h2>
            <span className="text-[10px] text-neutral-500 uppercase tracking-widest mt-1 block">Minimalist AI Search Engine</span>
          </div>

          {/* Inline Form Search */}
          <form 
            onSubmit={(e) => handleSearch(e)} 
            className="relative flex items-center w-full"
          >
            <input
              type="text"
              placeholder="Search crawled information..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full bg-[#0d0d0d] border border-neutral-900 text-xs font-mono px-4 py-3.5 pr-12 rounded focus:outline-none focus:border-neutral-700 focus:ring-1 focus:ring-neutral-800 text-white placeholder-neutral-700 transition"
              disabled={isSearching}
            />
            <button
              type="submit"
              className="absolute right-2.5 w-9 h-9 bg-white text-black hover:bg-neutral-200 transition rounded flex items-center justify-center cursor-pointer border-none"
              disabled={isSearching}
            >
              <Search className="w-4 h-4" />
            </button>
          </form>

          {/* Landing controls & suggestions */}
          <div className={`transition-all duration-500 ${isLanding ? "opacity-100 max-h-64 mt-5" : "opacity-0 max-h-0 overflow-hidden pointer-events-none mt-0"}`}>
            <div className="flex justify-center items-center space-x-6 text-[10px] text-neutral-500 select-none">
              <label className="relative flex items-center space-x-2 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={researchMode} 
                  onChange={(e) => setResearchMode(e.target.checked)} 
                  className="sr-only peer"
                />
                <div className="w-7 h-3.5 bg-neutral-900 border border-neutral-800 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-neutral-400 after:rounded-full after:h-2.5 after:w-2.5 after:transition-all peer-checked:bg-white peer-checked:after:bg-black relative"></div>
                <span className="uppercase tracking-wider font-bold">Deep Research Mode</span>
              </label>
            </div>

            <div className="pt-2 border-t border-neutral-950 mt-4">
              <span className="text-[9px] text-neutral-600 uppercase tracking-widest font-bold block mb-2 select-none">Suggestions</span>
              <div className="flex justify-center flex-wrap gap-2">
                {searchHistory.length === 0 ? (
                  <button
                    type="button"
                    onClick={() => {
                      setQuery("open-source coding assistants like Aider");
                      handleSearch(undefined, "open-source coding assistants like Aider");
                    }}
                    className="px-2.5 py-1.5 bg-[#0a0a0a] hover:bg-neutral-900 border border-neutral-900 hover:border-neutral-700 transition rounded text-[10px] text-neutral-400 cursor-pointer"
                  >
                    open-source coding assistants like Aider
                  </button>
                ) : (
                  searchHistory.slice(0, 3).map((h_query, idx) => (
                    <button
                      type="button"
                      key={idx}
                      onClick={() => {
                        setQuery(h_query);
                        handleSearch(undefined, h_query);
                      }}
                      className="px-2.5 py-1.5 bg-[#0a0a0a] hover:bg-neutral-900 border border-neutral-900 hover:border-neutral-700 transition rounded text-[10px] text-neutral-400 cursor-pointer"
                    >
                      {h_query}
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Main Results panel */}
        <main className="flex-grow max-w-3xl mx-auto w-full p-6 pt-16 pb-32 z-10 relative">
          
          {/* Active Question Slot (Closed Box) */}
          {activeQuestion && (
            <div className="mb-10 animate-slideUpQuestion select-text">
              <div className="bg-[#0a0a0a] border border-neutral-900 rounded-lg p-5 shadow-lg flex items-start space-x-4">
                <div className="w-6 h-6 rounded bg-neutral-900 border border-neutral-800 text-[10px] text-neutral-400 font-bold flex items-center justify-center select-none uppercase tracking-widest shrink-0 mt-0.5">
                  Q
                </div>
                <div className="flex-grow">
                  <span className="text-[9px] text-neutral-600 uppercase tracking-widest font-bold block mb-1.5 select-none">
                    Your Question
                  </span>
                  <p className="font-mono text-sm md:text-base font-semibold text-white leading-relaxed">
                    {activeQuestion}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Loading State */}
          {isSearching && (
            <div className="py-32 flex flex-col items-center justify-center text-center space-y-6">
              <div className="flex space-x-2 justify-center items-center">
                <span className="w-2.5 h-2.5 bg-white rounded-full animate-dot-bounce-1"></span>
                <span className="w-2.5 h-2.5 bg-white rounded-full animate-dot-bounce-2"></span>
                <span className="w-2.5 h-2.5 bg-white rounded-full animate-dot-bounce-3"></span>
              </div>
              <span className="font-mono text-[10px] text-neutral-500 uppercase tracking-widest animate-pulse">
                Synthesizing research answer...
              </span>
            </div>
          )}

          {/* Results Panel */}
          {result && !isSearching && (
            <div className="space-y-8 animate-fadeIn">
              
              {/* Backside Map Inspector Header */}
              <div className="flex justify-between items-center border-b border-neutral-900 pb-3 select-none">
                <span className="font-mono text-[10px] uppercase tracking-widest text-neutral-500 font-bold">
                  Research Brief
                </span>
                <button
                  type="button"
                  onClick={() => setShowGraphDrawer(true)}
                  className="flex items-center space-x-1.5 border border-neutral-800 hover:border-neutral-700 bg-neutral-950 text-xs px-3 py-1.5 rounded text-neutral-400 hover:text-white transition cursor-pointer"
                >
                  <Layers className="w-3.5 h-3.5 text-white" />
                  <span>Inspect Knowledge Map</span>
                </button>
              </div>

              {/* Answer Card (Frameless Typewriter) */}
              <AnswerCard 
                answer={result.report.content} 
                sources={result.sources} 
              />
              
              {/* Sources */}
              <div className="pt-6 border-t border-neutral-900">
                <SourceList 
                  sources={result.sources} 
                />
              </div>

              {/* Suggestions */}
              {result.recommendations && result.recommendations.length > 0 && (
                <div className="pt-6 border-t border-neutral-900">
                  <span className="text-[10px] text-neutral-500 uppercase tracking-widest font-bold block mb-3 select-none">
                    Suggested Next Questions
                  </span>
                  <div className="space-y-2">
                    {result.recommendations.map((rec, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          setQuery("");
                          handleSearch(undefined, rec);
                        }}
                        className="w-full text-left font-mono text-xs text-neutral-400 hover:text-white hover:translate-x-1.5 transition select-none flex items-center space-x-2 cursor-pointer py-1"
                      >
                        <span className="text-neutral-600">↳</span>
                        <span>{rec}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

            </div>
          )}

        </main>

        {/* Crawl URL Sliding Ingestion Drawer Overlay */}
        {showCrawlDrawer && (
          <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-all duration-300">
            {/* Close click backdrop click */}
            <div className="flex-1" onClick={() => setShowCrawlDrawer(false)} />
            
            <div className="w-full max-w-sm bg-[#090909] border-l border-neutral-900 h-full p-6 flex flex-col justify-between shadow-2xl animate-slideLeft">
              <div>
                <div className="flex justify-between items-center border-b border-neutral-950 pb-3 mb-6 select-none">
                  <span className="text-xs font-bold uppercase tracking-widest text-white flex items-center space-x-2">
                    <Database className="w-4 h-4 text-neutral-400" />
                    <span>Knowledge Ingestion</span>
                  </span>
                  <button 
                    type="button"
                    onClick={() => setShowCrawlDrawer(false)}
                    className="text-neutral-500 hover:text-white transition cursor-pointer border-none bg-transparent"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <p className="text-[11px] text-neutral-500 leading-relaxed font-mono mb-5 select-none">
                  Submit web URLs to crawl and parse. The extraction engine automatically updates your search indexes and embeds relationships into the visual knowledge map.
                </p>

                <form onSubmit={handleCrawl} className="space-y-3">
                  <input
                    type="url"
                    placeholder="URL to index (https://example.com)..."
                    value={crawlUrl}
                    onChange={(e) => setCrawlUrl(e.target.value)}
                    className="w-full bg-[#0c0c0c] border border-neutral-900 text-xs font-mono px-3 py-3 rounded focus:outline-none focus:border-neutral-700 text-white placeholder-neutral-700 transition"
                    disabled={isCrawling}
                    required
                  />
                  
                  <button
                    type="submit"
                    className="w-full py-2.5 bg-white text-black font-bold text-xs uppercase tracking-wider hover:bg-neutral-200 transition rounded flex items-center justify-center space-x-1.5 cursor-pointer border-none"
                    disabled={isCrawling}
                  >
                    <span>{isCrawling ? "Crawling & indexing..." : "Crawl & Ingest"}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>

              {/* Ingestion stats */}
              <div className="border-t border-neutral-950 pt-4 select-none">
                <span className="text-[9px] text-neutral-600 uppercase tracking-widest font-bold block mb-2">Ingestion Status</span>
                <div className="space-y-2 text-[10px] text-neutral-400 font-mono">
                  <div className="flex justify-between">
                    <span>Library size:</span>
                    <span className="text-white font-bold">{crawlStatus?.pages_crawled || 0} pages</span>
                  </div>
                  {isCrawling && (
                    <div className="flex items-center space-x-1 text-white animate-pulse">
                      <span className="w-1.5 h-1.5 rounded-full bg-white" />
                      <span>Crawl thread actively processing in background...</span>
                    </div>
                  )}
                </div>
              </div>

            </div>
          </div>
        )}

        {/* Knowledge Graph Slide-over Drawer (Backside) */}
        {showGraphDrawer && result && (
          <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-all duration-300">
            {/* Close click backdrop click */}
            <div className="flex-1" onClick={() => setShowGraphDrawer(false)} />
            
            <div className="w-full max-w-3xl bg-[#090909] border-l border-neutral-900 h-full p-6 flex flex-col justify-between shadow-2xl animate-slideLeft">
              <div className="flex-1 flex flex-col min-h-0">
                <div className="flex justify-between items-center border-b border-neutral-950 pb-3 mb-4 select-none">
                  <span className="text-xs font-bold uppercase tracking-widest text-white flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-white" />
                    <span>Knowledge Map</span>
                  </span>
                  <button 
                    type="button"
                    onClick={() => setShowGraphDrawer(false)}
                    className="text-neutral-500 hover:text-white transition cursor-pointer border-none bg-transparent"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                
                <p className="text-[10px] text-neutral-500 mb-4 select-none">
                  This entity-relationship map is built dynamically in the background by analyzing semantic ties in retrieved sources.
                </p>
                
                <div className="flex-1 min-h-0 bg-[#070707] border border-neutral-900 rounded p-2 relative">
                  <GraphViewer data={result.graph} />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer bar */}
        <footer className="border-t border-neutral-950 py-5 text-center select-none text-[9px] font-mono text-neutral-600 uppercase tracking-widest mt-auto">
          © 2026 Lork-AI • Secured Zero Docker Engine
        </footer>
      </div>
    </div>
  );
}
