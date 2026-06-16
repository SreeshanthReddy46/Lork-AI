import asyncio
from fastapi import FastAPI, BackgroundTasks, Query, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import json

from services.database import init_db, get_db_connection
from services.crawler_service import WebCrawlerService
from services.indexer import SearchIndexer
from services.graph_service import KnowledgeGraphService
from agents.orchestrator import MultiAgentOrchestrator

from starlette.middleware.base import BaseHTTPMiddleware
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_main")

app = FastAPI(title="Lork-AI Research Operating System API", version="1.0.0")

# Restrict CORS to specific localhost origins to block external site requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Secure headers middleware to protect against clickjacking, sniff, XSS, and frame injection
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Secure API validation key from environment config
API_KEY = os.getenv("API_KEY")

def verify_token(authorization: str = Header(None), x_api_key: str = Header(None)):
    token = x_api_key or (authorization.split(" ")[1] if authorization and authorization.startswith("Bearer ") else authorization)
    if API_KEY and token != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized. Invalid API Key.")

@app.on_event("startup")
def startup_event():
    init_db()
    logger.info("Lork-AI Research OS backend started. SQLite DB ready.")

class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 5
    max_depth: int = 1

class ClickRequest(BaseModel):
    page_id: int

async def run_crawl_background(url: str, max_pages: int, max_depth: int):
    crawler = WebCrawlerService()
    logger.info(f"Crawl process triggered in background for: {url}")
    
    # 1. Run web crawling
    await crawler.crawl_site(url, max_pages=max_pages, max_depth=max_depth)
    
    # 2. Generate vector embeddings for newly crawled pages
    indexer = SearchIndexer()
    indexer.generate_embeddings_for_all()
    
    # 3. Extract knowledge graph nodes & edges from newly crawled pages
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, clean_content FROM pages")
    rows = cursor.fetchall()
    conn.close()
    
    graph_service = KnowledgeGraphService()
    for row in rows:
        graph_service.extract_and_build_graph(row["id"], row["clean_content"])
        
    logger.info(f"Crawl process completed for: {url}")

@app.get("/api/search")
def search(q: str = Query(..., description="Search query"), _ = Depends(verify_token)):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")
    
    orchestrator = MultiAgentOrchestrator()
    result = orchestrator.run_research_pipeline(q)
    return result

@app.post("/api/crawl")
def crawl(req: CrawlRequest, background_tasks: BackgroundTasks, _ = Depends(verify_token)):
    if not req.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL format. Must start with http:// or https://")
        
    background_tasks.add_task(
        run_crawl_background, 
        req.url, 
        req.max_pages, 
        req.max_depth
    )
    return {"status": "queued", "message": f"Crawling queued in background for: {req.url}"}

@app.get("/api/crawl/status")
def crawl_status(_ = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM pages")
    crawled_count = cursor.fetchone()["count"]
    
    cursor.execute("SELECT status, COUNT(*) as count FROM crawl_queue GROUP BY status")
    queue_stats = {row["status"]: row["count"] for row in cursor.fetchall()}
    
    cursor.execute("SELECT url, status, depth FROM crawl_queue ORDER BY added_at DESC LIMIT 5")
    recent_queue = [{"url": row["url"], "status": row["status"], "depth": row["depth"]} for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "pages_crawled": crawled_count,
        "queue_stats": queue_stats,
        "recent_queue": recent_queue
    }

@app.get("/api/graph")
def get_graph(_ = Depends(verify_token)):
    graph_service = KnowledgeGraphService()
    nodes_list = []
    links_list = []
    
    for node in graph_service.graph.nodes:
        node_data = graph_service.graph.nodes[node]
        nodes_list.append({
            "id": node,
            "label": node_data.get("label", node),
            "type": node_data.get("type", "Concept")
        })
        
    for u, v in graph_service.graph.edges:
        links_list.append({
            "source": u,
            "target": v,
            "relation": graph_service.graph.edges[u, v].get("relation", "LINKED")
        })
        
    return {"nodes": nodes_list, "links": links_list}

@app.get("/api/history")
def get_history(_ = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT query, created_at FROM search_history ORDER BY created_at DESC LIMIT 10")
    history = [{"query": row["query"], "created_at": row["created_at"]} for row in cursor.fetchall()]
    conn.close()
    return history

@app.post("/api/click")
def register_click(req: ClickRequest, _ = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM pages WHERE id = ?", (req.page_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Page not found.")
        
    cursor.execute("UPDATE pages SET click_count = click_count + 1 WHERE id = ?", (req.page_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Click count incremented."}
