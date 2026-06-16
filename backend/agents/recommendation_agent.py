import json
from agents.base import BaseAgent, AgentBus
from services.llm import LLMService

class RecommendationAgent(BaseAgent):
    def __init__(self, llm: LLMService, bus: AgentBus):
        super().__init__("Recommendation Agent", llm, bus)

    def suggest_related(self, query: str, query_analysis: dict) -> list[str]:
        self.log("Generating suggested queries and trending associated topics...")
        
        system_prompt = """You are a Recommendation Agent.
Given a search query and its details, suggest 4 related research questions or queries that a user might want to explore next.
Format response as a JSON object only. Do not include markdown codeblocks or explanation.
Structure:
{
  "recommendations": ["query 1", "query 2", "query 3", "query 4"]
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
            recommendations = data.get("recommendations", [])
            self.log(f"Generated recommendations: {recommendations}")
            return recommendations
        except Exception as e:
            self.log(f"Recommendation fallback due to error: {e}")
            # simple fallback
            return [
                f"{query} vs competitor",
                f"latest news about {query}",
                f"{query} tutorial",
                f"open source alternatives to {query}"
            ]
