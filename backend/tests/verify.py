import sys
import os
import asyncio
import json

# Adjust python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import init_db, get_db_connection
from services.crawler_service import WebCrawlerService
from services.indexer import SearchIndexer
from services.graph_service import KnowledgeGraphService
from agents.orchestrator import MultiAgentOrchestrator

def verify_pipeline():
    print("=== Initializing SQLite Database ===")
    init_db()
    
    print("=== Populating Demo Content ===")
    # Insert 3 sample pages representing our AI Coding Agents
    conn = get_db_connection()
    cursor = conn.cursor()
    
    pages_data = [
        (
            "https://example.com/aider",
            "Aider - AI Pair Programming in Your Terminal",
            "Aider is an open source AI coding assistant that lets you pair program with LLMs in your terminal. It connects to OpenAI, Anthropic, or local models. Created by Paul Gauthier, Aider is built in Python and runs Git integrations automatically to commit code changes. It uses a graph-based code map to understand project architecture.",
            "Aider is a terminal-based open source AI pair programming tool created by Paul Gauthier."
        ),
        (
            "https://example.com/cursor",
            "Cursor - The AI-First Code Editor",
            "Cursor is an AI-powered code editor built as a fork of VS Code. It is developed by Anysphere, a startup backed by OpenAI. Cursor supports features like Composer, Cmd+K inline editing, and chat-based workspace indexing. It integrates OpenAI and Claude models natively to assist developers write code.",
            "Cursor is a VS Code fork with deep AI integrations developed by Anysphere."
        ),
        (
            "https://example.com/openhands",
            "OpenHands - Autonomous Dev Agent",
            "OpenHands (formerly OpenDevin) is an open-source autonomous agentic platform designed to write software. It runs inside Docker containers to safely execute shell commands and modify code. Backed by the All-Hands community and built with Python, OpenHands supports multiple LLM providers.",
            "OpenHands is a containerized open-source autonomous software developer agent."
        )
    ]
    
    for url, title, content, summary in pages_data:
        cursor.execute(
            """
            INSERT OR REPLACE INTO pages (url, title, clean_content, summary, raw_html, crawled_at, authority, freshness)
            VALUES (?, ?, ?, ?, '', CURRENT_TIMESTAMP, 1.0, CURRENT_TIMESTAMP)
            """,
            (url, title, content, summary)
        )
        page_id = cursor.lastrowid
        
        # Populate FTS
        cursor.execute("DELETE FROM pages_fts WHERE rowid = ?", (page_id,))
        cursor.execute("INSERT INTO pages_fts (rowid, title, content) VALUES (?, ?, ?)", (page_id, title, content))
        
    conn.commit()
    conn.close()
    print("Demo pages inserted successfully.")
    
    print("=== Generating Vector Embeddings ===")
    indexer = SearchIndexer()
    indexer.generate_embeddings_for_all()
    print("Vector embeddings generated successfully.")
    
    print("=== Building Knowledge Graph ===")
    graph_service = KnowledgeGraphService()
    
    # We will inject some manually structured nodes for testing
    graph_service.save_node("Aider", "Aider", "Product", {"creator": "Paul Gauthier", "type": "Terminal"})
    graph_service.save_node("Cursor", "Cursor", "Product", {"company": "Anysphere", "base": "VS Code"})
    graph_service.save_node("OpenHands", "OpenHands", "Product", {"runner": "Docker"})
    graph_service.save_node("OpenAI", "OpenAI", "Company", {"country": "US"})
    graph_service.save_node("Anysphere", "Anysphere", "Company", {})
    
    graph_service.save_edge("OpenAI", "Cursor", "BACKS", 1.0)
    graph_service.save_edge("Anysphere", "Cursor", "DEVELOPED", 1.0)
    graph_service.save_edge("OpenAI", "Aider", "POWERS", 1.0)
    
    # Update PageRank
    graph_service.update_page_authorities()
    print("Knowledge Graph populated and centrality computed.")
    
    print("=== Running Multi-Agent Search Pipeline ===")
    orchestrator = MultiAgentOrchestrator()
    result = orchestrator.run_research_pipeline("open-source coding assistants like Aider")
    
    print("\n=== PIPELINE OUTPUT RESULT ===")
    print("Query:", result["query"])
    print("Report Title:", result["report"]["title"])
    print("Report Content Snippet:\n", result["report"]["content"][:400])
    print("Sources Citations:", json.dumps(result["sources"], indent=2))
    print("Subgraph Nodes Count:", len(result["graph"]["nodes"]))
    print("Recommendations Suggested:", result["recommendations"])
    print("Trace Logs Count:", len(result["logs"]))
    
    print("\n=== Sample Agent Trace Logs ===")
    for log in result["logs"][:8]:
        print(f"[{log['timestamp']}] {log['agent']}: {log['message']}")
        
    print("\n=== Test Verification Completed Successfully ===")

if __name__ == "__main__":
    verify_pipeline()
