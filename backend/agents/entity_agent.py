import json
from agents.base import BaseAgent, AgentBus
from services.llm import LLMService

class EntityAgent(BaseAgent):
    def __init__(self, llm: LLMService, bus: AgentBus):
        super().__init__("Entity Extraction Agent", llm, bus)

    def extract_triples(self, text: str) -> dict:
        self.log("Scanning document text for entities and semantic relationships...")
        
        system_prompt = """You are an Entity and Relation Extraction Agent.
Given a document text, identify main entities and their semantic relationships.
Entity types: Company, Person, Technology, Product, Event, Concept.

Format response as a JSON object only. Do not include markdown codeblocks or explanation.
Structure:
{
  "nodes": [
    {"id": "EntityID", "label": "Readable Entity Name", "type": "Company/Person/Technology/etc.", "metadata": {}}
  ],
  "edges": [
    {"source": "SourceEntityID", "target": "TargetEntityID", "relation": "RELATIONSHIP", "weight": 1.0}
  ]
}
"""
        prompt = f"Extract entities & edges from this content:\n{text[:2500]}"
        
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
            self.log(f"Extracted {len(data.get('nodes', []))} entities and {len(data.get('edges', []))} relationships.")
            return data
        except Exception as e:
            self.log(f"Entity extraction fallback due to error: {e}")
            return {"nodes": [], "edges": []}
