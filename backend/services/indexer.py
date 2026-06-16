import json
import logging

from services.database import get_db_connection
from services.llm import LLMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("indexer_service")

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm1 = sum(a**2 for a in v1) ** 0.5
    norm2 = sum(b**2 for b in v2) ** 0.5
    if norm1 * norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)

class SearchIndexer:
    def __init__(self, llm_service: LLMService = None):
        self.llm = llm_service or LLMService()

    def generate_embeddings_for_all(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.id, p.title, p.clean_content 
            FROM pages p
            LEFT JOIN page_embeddings pe ON p.id = pe.page_id
            WHERE pe.page_id IS NULL
        """)
        rows = cursor.fetchall()
        
        if not rows:
            conn.close()
            return
            
        logger.info(f"Generating embeddings for {len(rows)} pages...")
        for row in rows:
            page_id = row["id"]
            text_to_embed = f"{row['title']}\n{row['clean_content'][:1500]}"
            try:
                vector = self.llm.get_embedding(text_to_embed)
                cursor.execute(
                    "INSERT OR REPLACE INTO page_embeddings (page_id, embedding) VALUES (?, ?)",
                    (page_id, json.dumps(vector))
                )
                conn.commit()
            except Exception as e:
                logger.error(f"Error embedding page {page_id}: {e}")
                conn.rollback()
                
        conn.close()

    def add_page_embedding(self, page_id: int, title: str, content: str):
        text_to_embed = f"{title}\n{content[:1500]}"
        vector = self.llm.get_embedding(text_to_embed)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO page_embeddings (page_id, embedding) VALUES (?, ?)",
            (page_id, json.dumps(vector))
        )
        conn.commit()
        conn.close()

    def search_bm25(self, query: str, limit: int = 10) -> list[dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        import re
        # Strip non-alphanumeric and group as quoted OR terms
        clean_words = re.findall(r'\w+', query)
        if not clean_words:
            conn.close()
            return []
            
        fts_query = " OR ".join([f'"{w}"' for w in clean_words])
        
        try:
            cursor.execute("""
                SELECT 
                    p.id, 
                    p.url, 
                    p.title, 
                    p.clean_content, 
                    p.authority,
                    p.freshness,
                    (-bm25(pages_fts)) as score
                FROM pages_fts fts
                JOIN pages p ON p.id = fts.rowid
                WHERE pages_fts MATCH ?
                ORDER BY score DESC
                LIMIT ?
            """, (fts_query, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "url": row["url"],
                    "title": row["title"],
                    "content": row["clean_content"],
                    "authority": row["authority"],
                    "freshness": row["freshness"],
                    "score": float(row["score"])
                })
            return results
        except Exception as e:
            logger.error(f"BM25 Search Error for query '{query}': {e}")
            return []
        finally:
            conn.close()

    def search_semantic(self, query: str, limit: int = 10) -> list[dict]:
        query_vector = self.llm.get_embedding(query)
        if not query_vector:
            return []
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pe.page_id, pe.embedding, p.url, p.title, p.clean_content, p.authority, p.freshness
            FROM page_embeddings pe
            JOIN pages p ON pe.page_id = p.id
        """)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return []
            
        results = []
        for row in rows:
            try:
                doc_vec = json.loads(row["embedding"])
                score = cosine_similarity(query_vector, doc_vec)
                results.append({
                    "id": row["page_id"],
                    "url": row["url"],
                    "title": row["title"],
                    "content": row["clean_content"],
                    "authority": row["authority"],
                    "freshness": row["freshness"],
                    "score": score
                })
            except Exception:
                continue
                
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
