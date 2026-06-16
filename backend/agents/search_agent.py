from agents.base import BaseAgent, AgentBus
from services.llm import LLMService
from services.ranker import HybridRanker

class SearchAgent(BaseAgent):
    def __init__(self, llm: LLMService, bus: AgentBus, ranker: HybridRanker = None):
        super().__init__("Web Search Agent", llm, bus)
        self.ranker = ranker or HybridRanker()

    def search_index(self, query: str, sub_queries: list[str]) -> list[dict]:
        self.log(f"Searching index files for query: '{query}'...")
        
        seen_ids = set()
        results = []
        
        # Primary search
        primary_matches = self.ranker.rank(query, limit=10)
        for doc in primary_matches:
            if doc["id"] not in seen_ids:
                seen_ids.add(doc["id"])
                results.append(doc)
                
        # Expanded searches
        for sub_q in sub_queries:
            if len(results) >= 8:
                break
            if sub_q == query:
                continue
            self.log(f"Executing secondary expansion search: '{sub_q}'")
            sub_matches = self.ranker.rank(sub_q, limit=5)
            for doc in sub_matches:
                if doc["id"] not in seen_ids:
                    seen_ids.add(doc["id"])
                    results.append(doc)
                    
        self.log(f"Collected {len(results)} search results matching requirements.")
        return results[:8]
