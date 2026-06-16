import logging
from datetime import datetime
import math

from services.database import get_db_connection
from services.indexer import SearchIndexer

logger = logging.getLogger("ranker_service")

def normalize_scores(results: list[dict], score_key: str = "score") -> list[dict]:
    if not results:
        return results
        
    scores = [r[score_key] for r in results]
    min_score = min(scores)
    max_score = max(scores)
    
    denom = max_score - min_score
    for r in results:
        if denom > 0:
            r["norm_score"] = (r[score_key] - min_score) / denom
        else:
            r["norm_score"] = 1.0
            
    return results

class HybridRanker:
    def __init__(self, indexer: SearchIndexer = None):
        self.indexer = indexer or SearchIndexer()

    def rank(self, query: str, limit: int = 10) -> list[dict]:
        bm25_results = self.indexer.search_bm25(query, limit=limit * 2)
        semantic_results = self.indexer.search_semantic(query, limit=limit * 2)
        
        bm25_norm = normalize_scores(bm25_results)
        semantic_norm = normalize_scores(semantic_results)
        
        bm25_map = {r["id"]: r for r in bm25_norm}
        semantic_map = {r["id"]: r for r in semantic_norm}
        
        all_ids = set(bm25_map.keys()).union(set(semantic_map.keys()))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        ranked_list = []
        
        for p_id in all_ids:
            cursor.execute(
                "SELECT id, url, title, clean_content, authority, freshness, click_count FROM pages WHERE id = ?", 
                (p_id,)
            )
            row = cursor.fetchone()
            if not row:
                continue
                
            # Freshness
            freshness_str = row["freshness"]
            freshness_bonus = 0.0
            try:
                ts_str = freshness_str.replace("T", " ").replace("Z", "")
                ts_str = ts_str.split(".")[0]
                dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                days_diff = (datetime.now() - dt).days
                freshness_bonus = 0.15 * math.exp(-0.05 * max(0, days_diff)) # Boosted weight to matches user's 15% freshness target
            except Exception:
                pass
                
            # Click count bias
            clicks = row["click_count"]
            click_bonus = 0.02 * math.log1p(clicks)
            
            norm_bm25 = bm25_map[p_id]["norm_score"] if p_id in bm25_map else 0.0
            norm_semantic = semantic_map[p_id]["norm_score"] if p_id in semantic_map else 0.0
            
            # PageRank authority
            norm_authority = min(1.0, row["authority"] / 10.0)
            
            # User PRD: Score = 40% Semantic + 25% BM25 + 20% Authority + 15% Freshness + Clicks
            relevance_score = (
                0.25 * norm_bm25 + 
                0.40 * norm_semantic + 
                0.20 * norm_authority +
                0.15 * freshness_bonus
            )
            
            final_score = relevance_score + click_bonus
            
            ranked_list.append({
                "id": row["id"],
                "url": row["url"],
                "title": row["title"],
                "content": row["clean_content"],
                "relevance_score": relevance_score,
                "click_bonus": click_bonus,
                "final_score": final_score
            })
            
        conn.close()
        
        ranked_list.sort(key=lambda x: x["final_score"], reverse=True)
        return ranked_list[:limit]
