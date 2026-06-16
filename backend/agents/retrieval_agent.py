from agents.base import BaseAgent, AgentBus
from services.llm import LLMService
from services.indexer import SearchIndexer

class RetrievalAgent(BaseAgent):
    def __init__(self, llm: LLMService, bus: AgentBus, indexer: SearchIndexer = None):
        super().__init__("Semantic Retrieval Agent", llm, bus)
        self.indexer = indexer or SearchIndexer(llm)

    def retrieve_semantic(self, query: str, limit: int = 5) -> list[dict]:
        self.log(f"Generating vector embedding for query: '{query}'...")
        self.log("Executing cosine similarity lookup against SQLite vector embeddings...")
        
        matches = self.indexer.search_semantic(query, limit=limit)
        self.log(f"Retrieved {len(matches)} vector similarities (top cosine: {matches[0]['score'] if matches else 0.0:.3f})")
        return matches
