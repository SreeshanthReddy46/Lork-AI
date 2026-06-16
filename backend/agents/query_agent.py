import json
from agents.base import BaseAgent, AgentBus
from services.llm import LLMService

class QueryAgent(BaseAgent):
    def __init__(self, llm: LLMService, bus: AgentBus):
        super().__init__("Query Understanding Agent", llm, bus)

    def analyze(self, query: str) -> dict:
        self.log(f"Analyzing query: '{query}'")
        self.log("Extracting search intent, keywords, and entity context...")
        
        system_prompt = """You are a Query Understanding Agent.
Analyze the user's search query and extract search parameters in JSON format.
Include:
1. "intent": The category (e.g. 'informational', 'navigational', 'transactional', 'coding')
2. "keywords": Main keywords for indexing
3. "entities": Named Entities (name, type: Company/Person/Technology/Product/Event/Concept)
4. "confidence": Value from 0.0 to 1.0 representing intent confidence.

Format response as a JSON object only. Do not include markdown codeblocks or explanation.
"""
        try:
            response = self.llm.generate(query, system_prompt=system_prompt, json_mode=True)
            clean_resp = response.strip()
            if clean_resp.startswith("```json"):
                clean_resp = clean_resp.replace("```json", "", 1)
            if clean_resp.endswith("```"):
                clean_resp = clean_resp[:-3].strip()
            if clean_resp.startswith("```"):
                clean_resp = clean_resp.replace("```", "", 1).strip()
                
            analysis = json.loads(clean_resp)
            self.log(f"Intent classified: {analysis.get('intent')} (conf: {analysis.get('confidence', 0.9)}). Keywords: {analysis.get('keywords', [])}")
            return analysis
        except Exception as e:
            self.log(f"Query analysis fallback due to: {e}")
            return {
                "intent": "informational",
                "keywords": query.split(),
                "entities": [],
                "confidence": 0.5
            }
