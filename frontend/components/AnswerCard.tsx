"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, HelpCircle } from "lucide-react";

interface Source {
  id: number;
  url: string;
  title: string;
}

interface AnswerCardProps {
  answer: string;
  sources: Source[];
}

export default function AnswerCard({ answer, sources }: AnswerCardProps) {
  const [hoveredCitation, setHoveredCitation] = useState<number | null>(null);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const [typedContent, setTypedContent] = useState("");

  useEffect(() => {
    if (!answer) {
      setTypedContent("");
      return;
    }
    
    let currentLength = 0;
    setTypedContent("");
    
    const interval = setInterval(() => {
      currentLength += 8;
      if (currentLength >= answer.length) {
        setTypedContent(answer);
        clearInterval(interval);
      } else {
        setTypedContent(answer.substring(0, currentLength));
      }
    }, 10);
    
    return () => clearInterval(interval);
  }, [answer]);

  // Parse text and identify [1], [2] tags to replace them with interactive elements
  const renderFormattedText = (text: string) => {
    if (!text) return null;
    
    // Regular expression matching [1], [2], etc.
    const citationRegex = /\[([0-9]+)\]/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = citationRegex.exec(text)) !== null) {
      const matchIndex = match.index;
      const citationId = parseInt(match[1]);

      // Add text leading up to the citation tag
      if (matchIndex > lastIndex) {
        parts.push(text.substring(lastIndex, matchIndex));
      }

      // Add interactive citation tag
      parts.push({ id: citationId, raw: match[0] });
      lastIndex = citationRegex.lastIndex;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    if (parts.length === 0) {
      return text;
    }

    return parts.map((part, index) => {
      if (typeof part === "string") {
        // Renders basic paragraph split by spacing
        return <span key={index} className="whitespace-pre-line leading-relaxed">{part}</span>;
      } else {
        const source = sources.find(s => s.id === part.id);
        if (!source) return <span key={index}>{part.raw}</span>;

        return (
          <span
            key={index}
            onMouseEnter={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              setCoords({ x: rect.left + window.scrollX, y: rect.bottom + window.scrollY + 5 });
              setHoveredCitation(part.id);
            }}
            onMouseLeave={() => setHoveredCitation(null)}
            className="relative mx-0.5 inline-flex items-center justify-center w-3.5 h-3.5 text-[8px] font-mono font-bold bg-neutral-900 hover:bg-white border border-neutral-800 text-neutral-400 hover:text-black rounded-sm cursor-pointer transition select-none align-super"
          >
            {part.id}
          </span>
        );
      }
    });
  };

  const getDomain = (urlStr: string) => {
    try {
      const url = new URL(urlStr);
      return url.hostname.replace("www.", "");
    } catch {
      return urlStr;
    }
  };

  const hoveredSource = hoveredCitation ? sources.find(s => s.id === hoveredCitation) : null;

  return (
    <div className="w-full select-text relative">
      
      {/* Title */}
      <div className="flex items-center space-x-2 border-b border-neutral-900 pb-3 mb-5 select-none">
        <Sparkles className="w-3.5 h-3.5 text-neutral-400" />
        <span className="font-mono text-xs uppercase tracking-widest text-neutral-400 font-bold">
          Synthesized Answer
        </span>
      </div>

      {/* Answer Body Text */}
      <div className="font-mono text-sm text-neutral-200 leading-relaxed space-y-4">
        {typedContent ? (
          <div>{renderFormattedText(typedContent)}</div>
        ) : (
          <div className="text-neutral-500 italic">No search execution trace recorded.</div>
        )}
      </div>

      {/* Floating Citation Preview Card */}
      {hoveredSource && (
        <div
          style={{
            position: "absolute",
            left: `${coords.x}px`,
            top: `${coords.y}px`,
            zIndex: 9999,
          }}
          className="w-56 p-3 bg-[#0d0d0d] border border-neutral-800 text-[10px] font-mono text-neutral-300 rounded shadow-2xl animate-fadeIn pointer-events-none"
        >
          <div className="text-[8px] text-neutral-500 uppercase tracking-widest font-bold mb-1 flex items-center justify-between">
            <span>Reference [{hoveredSource.id}]</span>
            <span className="text-neutral-400">{getDomain(hoveredSource.url)}</span>
          </div>
          <div className="text-white font-bold leading-normal">{hoveredSource.title}</div>
          <div className="text-neutral-500 mt-1 truncate">{hoveredSource.url}</div>
        </div>
      )}
    </div>
  );
}
