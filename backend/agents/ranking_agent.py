from agents.base import BaseAgent, AgentBus
from services.llm import LLMService
from services.ranker import HybridRanker

class RankingAgent(BaseAgent):
    def __init__(self, llm: LLMService, bus: AgentBus, ranker: HybridRanker = None):
        super().__init__("Ranking Agent", llm, bus)
        self.ranker = ranker or HybridRanker()

    def merge_and_rank(self, query: str, limit: int = 5) -> list[dict]:
        self.log(f"Fusing scores using rank formula (40% Semantic, 25% BM25, 20% PageRank, 15% Freshness)...")
        
        ranked_docs = self.ranker.rank(query, limit=limit)
        
        # Log top rank
        if ranked_docs:
            top = ranked_docs[0]
            self.log(f"Top Document ranked: '{top['title']}' (Score: {top['relevance_score']:.3f})")
            
        return ranked_docs
