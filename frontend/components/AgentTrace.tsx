"use client";

import React, { useEffect, useRef } from "react";

interface LogEntry {
  timestamp: string;
  agent: string;
  message: string;
}

interface AgentTraceProps {
  logs: LogEntry[];
  isSearching: boolean;
}

export default function AgentTrace({ logs, isSearching }: AgentTraceProps) {
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll terminal to bottom on new logs
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs, isSearching]);

  // Color mapping based on agent role for premium visual coding structure
  const getAgentColor = (agent: string) => {
    switch (agent) {
      case "Orchestrator":
        return "text-neutral-200 border-neutral-700 bg-neutral-900";
      case "Query Understanding Agent":
        return "text-white border-neutral-800 bg-neutral-950";
      case "Search Planning Agent":
        return "text-neutral-400 border-neutral-900 bg-neutral-950";
      case "Web Search Agent":
      case "Semantic Retrieval Agent":
        return "text-neutral-300 border-neutral-800 bg-neutral-950";
      case "Ranking Agent":
        return "text-white border-neutral-700 bg-neutral-900";
      case "Knowledge Graph Agent":
      case "Entity Extraction Agent":
        return "text-neutral-200 border-neutral-900 bg-[#0e0e0e]";
      case "Research Agent":
        return "text-neutral-100 border-neutral-600 bg-neutral-900";
      case "Fact Verification Agent":
        return "text-white border-neutral-800 bg-neutral-950";
      case "Citation Agent":
      case "Report Generation Agent":
        return "text-white border-neutral-600 bg-[#0f0f0f]";
      default:
        return "text-neutral-400 border-neutral-900 bg-neutral-950";
    }
  };

  return (
    <div className="w-full bg-[#070707] border border-neutral-900 rounded font-mono text-[11px] text-neutral-400 overflow-hidden shadow-2xl flex flex-col h-[280px] md:h-[320px]">
      
      {/* Terminal Title Bar */}
      <div className="bg-[#0b0b0b] px-4 py-2 border-b border-neutral-900 flex justify-between items-center select-none shrink-0">
        <div className="flex items-center space-x-2">
          {/* Mac-style traffic lights */}
          <span className="w-2.5 h-2.5 rounded-full bg-neutral-800"></span>
          <span className="w-2.5 h-2.5 rounded-full bg-neutral-800"></span>
          <span className="w-2.5 h-2.5 rounded-full bg-neutral-800"></span>
          <span className="text-[10px] text-neutral-500 uppercase tracking-widest font-bold ml-2">
            Agent Bus Trace Logs
          </span>
        </div>
        
        {/* Connection status indicator */}
        <div className="flex items-center space-x-1.5">
          <span className={`w-1.5 h-1.5 rounded-full ${isSearching ? "bg-white animate-pulse" : "bg-neutral-800"}`} />
          <span className="text-[9px] text-neutral-500 uppercase tracking-wider font-bold">
            {isSearching ? "Processing Pipeline" : "Idle"}
          </span>
        </div>
      </div>

      {/* Logs Shell Output */}
      <div className="p-4 overflow-y-auto flex-1 space-y-2.5 scrollbar-thin scrollbar-thumb-neutral-800 scrollbar-track-transparent">
        {logs.length === 0 ? (
          <div className="h-full flex flex-col justify-center items-center text-neutral-600 italic select-none">
            <span>No agent trace recorded. Submit a query to trigger pipeline.</span>
          </div>
        ) : (
          logs.map((log, idx) => (
            <div key={idx} className="flex flex-col md:flex-row md:items-start md:space-x-3 text-neutral-300 animate-fadeIn">
              
              {/* Timestamp tag */}
              <span className="text-neutral-600 select-none shrink-0 md:pt-0.5">{log.timestamp}</span>
              
              <div className="flex-1">
                {/* Agent Tag */}
                <span className={`inline-block px-1.5 py-0.5 border text-[9px] rounded font-bold uppercase tracking-wider select-none mr-2 ${getAgentColor(log.agent)}`}>
                  {log.agent}
                </span>
                
                {/* Message Body */}
                <span className="text-neutral-400 break-words leading-relaxed">{log.message}</span>
              </div>
            </div>
          ))
        )}
        
        {/* Active running pulse line */}
        {isSearching && (
          <div className="flex items-center space-x-2 text-white font-bold animate-pulse">
            <span className="text-neutral-600 select-none">--:--:--.--</span>
            <span className="text-[9px] uppercase border border-neutral-700 px-1 bg-neutral-900 tracking-wider">SYSTEM</span>
            <span className="text-xs">Orchestration pipeline executing steps...</span>
            <span className="w-1.5 h-3 bg-white inline-block animate-blink" />
          </div>
        )}
        
        <div ref={terminalEndRef} />
      </div>
    </div>
  );
}
