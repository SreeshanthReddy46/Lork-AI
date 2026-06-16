import os
import sqlite3
import logging

logger = logging.getLogger("database_service")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "search_engine.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Pages table (stores crawled documents)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE NOT NULL,
        title TEXT,
        clean_content TEXT,
        summary TEXT,
        raw_html TEXT,
        crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        authority REAL DEFAULT 1.0,
        freshness TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        click_count INTEGER DEFAULT 0
    )
    """)
    
    # FTS5 Virtual Table for BM25 Search
    try:
        cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(title, content);")
    except sqlite3.OperationalError:
        cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts3(title, content);")
        
    # Vector Embeddings storage
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS page_embeddings (
        page_id INTEGER PRIMARY KEY,
        embedding TEXT NOT NULL,
        FOREIGN KEY (page_id) REFERENCES pages (id) ON DELETE CASCADE
    )
    """)
    
    # Crawl Queue table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crawl_queue (
        url TEXT PRIMARY KEY,
        status TEXT DEFAULT 'pending', -- 'pending', 'crawling', 'done', 'failed'
        depth INTEGER DEFAULT 0,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Knowledge Graph Nodes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        id TEXT PRIMARY KEY, 
        label TEXT NOT NULL,
        type TEXT NOT NULL, -- 'Company', 'Person', 'Technology', 'Product', 'Event', 'Concept'
        metadata TEXT DEFAULT '{}'
    )
    """)
    
    # Knowledge Graph Edges table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS edges (
        source TEXT,
        target TEXT,
        relation TEXT, 
        weight REAL DEFAULT 1.0,
        PRIMARY KEY (source, target, relation),
        FOREIGN KEY (source) REFERENCES nodes (id) ON DELETE CASCADE,
        FOREIGN KEY (target) REFERENCES nodes (id) ON DELETE CASCADE
    )
    """)

    # Document-to-Entity linking table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_entities (
        page_id INTEGER,
        entity_id TEXT,
        PRIMARY KEY (page_id, entity_id),
        FOREIGN KEY (page_id) REFERENCES pages (id) ON DELETE CASCADE,
        FOREIGN KEY (entity_id) REFERENCES nodes (id) ON DELETE CASCADE
    )
    """)
    
    # Search History & Cache
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT UNIQUE NOT NULL,
        answer TEXT,
        citations TEXT, 
        graph TEXT, 
        related_queries TEXT, 
        agent_logs TEXT, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    logger.info(f"SQLite database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
