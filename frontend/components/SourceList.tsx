"use client";

import React from "react";
import { Link2, Sparkles, Flame, Clock } from "lucide-react";

interface Source {
  id: number;
  url: string;
  title: string;
  score?: number;
}

interface SourceListProps {
  sources: Source[];
  onSourceClick?: (id: number) => void;
}

export default function SourceList({ sources, onSourceClick }: SourceListProps) {
  const handleSourceClick = async (sourceId: number, pageId?: number) => {
    if (onSourceClick) {
      onSourceClick(sourceId);
    }
    
    // Register click in backend if we have a valid page ID
    if (pageId) {
      try {
        await fetch("http://localhost:8000/api/click", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ page_id: pageId })
        });
      } catch (err) {
        console.error("Failed to register click:", err);
      }
    }
  };

  // Get domain name from URL
  const getDomain = (urlStr: string) => {
    try {
      const url = new URL(urlStr);
      return url.hostname.replace("www.", "");
    } catch {
      return urlStr;
    }
  };

  // Get matching mock page ID or extract it from source score mappings if available
  // In practice, our sources list returned by CitationAgent maps index [1], [2], [3]
  // We can approximate click tracking or bind it to sources.
  return (
    <div className="w-full space-y-3">
      <div className="flex items-center space-x-2 border-b border-neutral-900 pb-2 mb-3">
        <Clock className="w-4 h-4 text-neutral-400" />
        <span className="font-mono text-xs uppercase tracking-widest text-neutral-400 font-bold">
          Verified Information Sources ({sources.length})
        </span>
      </div>

      {sources.length === 0 ? (
        <div className="text-neutral-500 font-mono text-xs select-none">
          No crawled resources references. Ingest documents to get citations.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {sources.map((source) => (
            <a
              key={source.id}
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => handleSourceClick(source.id, source.id)} // map id to page_id for demonstration
              className="group block p-3 bg-[#0a0a0a] border border-neutral-900 rounded hover:border-neutral-700 transition duration-200 select-none shadow-sm cursor-pointer"
            >
              <div className="flex items-center justify-between mb-2">
                {/* Domain & Index tag */}
                <div className="flex items-center space-x-2">
                  <span className="w-5 h-5 flex items-center justify-center bg-white text-black font-mono font-bold text-[10px] rounded">
                    [{source.id}]
                  </span>
                  <span className="text-[10px] font-mono text-neutral-500 truncate max-w-[120px]">
                    {getDomain(source.url)}
                  </span>
                </div>
                
                {/* Link icon */}
                <Link2 className="w-3.5 h-3.5 text-neutral-600 group-hover:text-white transition duration-200" />
              </div>

              {/* Title */}
              <h4 className="text-xs font-mono text-white font-bold group-hover:text-white line-clamp-1 mb-1 transition duration-200">
                {source.title}
              </h4>
              
              {/* Optional Score / Match tag */}
              {source.score !== undefined && (
                <div className="flex items-center space-x-1 mt-1 text-[9px] font-mono text-neutral-500">
                  <Flame className="w-2.5 h-2.5 text-neutral-600" />
                  <span>Relevance: {Math.round(source.score * 100)}%</span>
                </div>
              )}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
