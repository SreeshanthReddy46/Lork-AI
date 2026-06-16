import json
from agents.base import BaseAgent, AgentBus
from services.llm import LLMService

class PlannerAgent(BaseAgent):
    def __init__(self, llm: LLMService, bus: AgentBus):
        super().__init__("Search Planning Agent", llm, bus)

    def plan(self, query: str, query_analysis: dict) -> list[str]:
        self.log("Decomposing search task and expanding query variations...")
        
        system_prompt = """You are a Search Planning Agent.
Given a user query and its intent analysis, generate 3 specific sub-queries or search terms to crawl/search the web.
Ensure the sub-queries are optimized for keyword indices and coverage.

Format response as a JSON object only. Do not include markdown codeblocks or explanation.
Structure:
{
  "sub_queries": ["query 1", "query 2", "query 3"]
}
"""
        prompt = f"Query: {query}\nAnalysis: {json.dumps(query_analysis)}"
        
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
            queries = data.get("sub_queries", [query])
            self.log(f"Generated search variations: {queries}")
            return queries
        except Exception as e:
            self.log(f"Planning fallback: {e}")
            return [query]
