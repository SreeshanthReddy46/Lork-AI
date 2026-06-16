import json
import logging
from services.database import get_db_connection
from services.llm import LLMService
from services.ranker import HybridRanker
from services.graph_service import KnowledgeGraphService
from services.indexer import SearchIndexer

logger = logging.getLogger("orchestrator")

class MultiAgentOrchestrator:
    def __init__(self):
        self.llm = LLMService()
        self.indexer = SearchIndexer(self.llm)
        self.ranker = HybridRanker(self.indexer)
        self.graph_service = KnowledgeGraphService(self.llm)

    def run_research_pipeline(self, query: str) -> dict:
        query_clean = query.strip()
        
        # 1. Database Cache Lookup for Instant (0ms) Answers
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT answer, citations, graph, related_queries FROM search_history WHERE LOWER(query) = LOWER(?)",
                (query_clean,)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                logger.info(f"Instant cache hit for query: '{query_clean}'")
                return {
                    "query": query,
                    "report": {
                        "title": f"Research Report: {query}",
                        "content": row["answer"]
                    },
                    "sources": json.loads(row["citations"]),
                    "graph": json.loads(row["graph"]),
                    "recommendations": json.loads(row["related_queries"]),
                    "logs": []
                }
        except Exception as e:
            logger.error(f"Cache lookup failed: {e}")

        # 2. Fast Pipeline Execution
        # Retrieve BM25 & vector search matches (Single embedding call)
        ranked_docs = self.ranker.rank(query_clean, limit=5)
        
        # Retrieve subgraph matching keywords
        keywords = query_clean.split()
        subgraph = self.graph_service.get_subgraph_around_query(keywords)
        
        if not ranked_docs:
            answer = "No index match found. Please crawl some websites first to ingest data into the local library!"
            sources = []
            recommendations = ["How to crawl pages", "Setup guide"]
        else:
            # Consolidate source data for single-pass prompt
            doc_context = ""
            sources = []
            for idx, doc in enumerate(ranked_docs):
                source_id = idx + 1
                doc_context += f"--- SOURCE [{source_id}] ---\nURL: {doc['url']}\nTitle: {doc['title']}\nContent: {doc['content'][:1500]}\n\n"
                sources.append({
                    "id": source_id,
                    "url": doc["url"],
                    "title": doc["title"],
                    "score": doc.get("final_score", 0.0)
                })
                
            graph_context = "--- KNOWLEDGE GRAPH ENTITIES & RELATIONS ---\n"
            for node in subgraph.get("nodes", []):
                graph_context += f"Entity: {node['label']} ({node['type']})\n"
            for link in subgraph.get("links", []):
                graph_context += f"Relationship: {link['source']} --[{link['relation']}]--> {link['target']}\n"

            # Combined single-pass prompt for query synthesis, citations, fact-checking, and followups
            system_prompt = """You are a highly efficient Research Agent. Given a query, source documents, and entity connections, compile a comprehensive Markdown report.
Guidelines:
1. Provide a detailed, structured, and premium cited answer.
2. Embed inline citations strictly in the format [1], [2], etc., corresponding to Source IDs.
3. Every claim must be supported by the sources. 
4. Recommend exactly 4 related questions for further search.

Format the output strictly as a JSON object only. Do not wrap in markdown quotes.
Structure:
{
  "answer": "Cited markdown answer text here...",
  "recommendations": ["question 1", "question 2", "question 3", "question 4"]
}
"""
            prompt = f"Query: {query_clean}\n\n{doc_context}\n\n{graph_context}"
            
            try:
                response = self.llm.generate(prompt, system_prompt=system_prompt, json_mode=True)
                clean_resp = response.strip()
                if clean_resp.startswith("```json"):
                    clean_resp = clean_resp.replace("```json", "", 1)
                if clean_resp.endswith("```"):
                    clean_resp = clean_resp[:-3].strip()
                if clean_resp.startswith("```"):
                    clean_resp = clean_resp.replace("```", "", 1).strip()
                    
                data = json.loads(clean_resp)
                answer = data.get("answer", "")
                recommendations = data.get("recommendations", [])
            except Exception as e:
                logger.error(f"Single-pass LLM pipeline generation failed: {e}")
                answer = "Generation failed. Try configuring API_KEY in backend/.env for stable completions."
                recommendations = ["Try another search"]

        # Cache the result to SQLite history for future instant hits
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO search_history (query, answer, citations, graph, related_queries, agent_logs)
                VALUES (?, ?, ?, ?, ?, '[]')
                """,
                (
                    query_clean,
                    answer,
                    json.dumps(sources),
                    json.dumps(subgraph),
                    json.dumps(recommendations)
                )
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Caching search results failed: {e}")

        return {
            "query": query,
            "report": {
                "title": f"Research Report: {query}",
                "content": answer
            },
            "sources": sources,
            "graph": subgraph,
            "recommendations": recommendations,
            "logs": []
        }
