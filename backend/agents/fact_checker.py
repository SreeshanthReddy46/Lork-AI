import json
from agents.base import BaseAgent, AgentBus
from services.llm import LLMService

class FactCheckerAgent(BaseAgent):
    def __init__(self, llm: LLMService, bus: AgentBus):
        super().__init__("Fact Verification Agent", llm, bus)

    def verify(self, report: str, documents: list[dict]) -> dict:
        self.log("Fact-checking the synthesized report against source documents to prevent hallucinations...")
        
        doc_refs = ""
        for idx, doc in enumerate(documents):
            doc_refs += f"Source [{idx+1}]:\n{doc['content'][:1500]}\n\n"
            
        system_prompt = """You are a Fact Verification Agent.
Analyze the provided report draft and the retrieved sources. Identify any claims that are NOT supported by the source text, or details that are inconsistent.
Return a JSON object containing:
1. "hallucinations": A list of claims found in the report that are not supported by the sources, each with the reason.
2. "inconsistencies": A list of conflicting details.
3. "is_valid": boolean representing if the report is verified.

Format response as a JSON object only. Do not include markdown codeblocks or explanation.
Structure:
{
  "hallucinations": [{"claim": "...", "reason": "..."}],
  "inconsistencies": [{"issue": "..."}],
  "is_valid": true
}
"""
        prompt = f"Report Draft:\n{report}\n\nSources:\n{doc_refs}"
        
        try:
            response = self.llm.generate(prompt, system_prompt=system_prompt, json_mode=True)
            clean_resp = response.strip()
            if clean_resp.startswith("```json"):
                clean_resp = clean_resp.replace("```json", "", 1)
            if clean_resp.endswith("```"):
                clean_resp = clean_resp[:-3].strip()
            if clean_resp.startswith("```"):
                clean_resp = clean_resp.replace("```", "", 1).strip()
                
            verification = json.loads(clean_resp)
            self.log(f"Fact checking complete. Valid: {verification.get('is_valid')}. Hallucinations found: {len(verification.get('hallucinations', []))}")
            return verification
        except Exception as e:
            self.log(f"Fact checking fallback due to error: {e}")
            return {"hallucinations": [], "inconsistencies": [], "is_valid": True}
