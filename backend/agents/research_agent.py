from agents.base import BaseAgent, AgentBus
from services.llm import LLMService

class ResearchAgent(BaseAgent):
    def __init__(self, llm: LLMService, bus: AgentBus):
        super().__init__("Research Agent", llm, bus)

    def synthesize(self, query: str, documents: list[dict], graph_data: dict) -> str:
        self.log("Synthesizing documents and knowledge graph connections into a cohesive analysis layout...")
        
        # Format document lists
        doc_summaries = ""
        for idx, doc in enumerate(documents):
            doc_summaries += f"Source [{idx+1}]: {doc['title']} (URL: {doc['url']})\nSnippet:\n{doc['content'][:800]}\n\n"
            
        # Format graph relationships
        nodes = [f"{n['label']} ({n['type']})" for n in graph_data.get("nodes", [])]
        relations = [f"{l['source']} --[{l['relation']}]--> {l['target']}" for l in graph_data.get("links", [])]
        
        graph_text = f"Entities: {', '.join(nodes)}\nRelationships:\n" + "\n".join(relations)
        
        system_prompt = """You are a Research Agent.
Your job is to read search result documents and a related entity knowledge graph to build a detailed, high-fidelity research analysis.
Structure the text cleanly:
1. Executive Summary
2. Detailed Key Findings
3. Competitive / Architecture Insights (incorporating knowledge graph connections)
4. Knowledge Graph Context Summary

Make sure you do not include inline citations yet. Just synthesize the structured information clearly.
"""
        prompt = f"""User Query: {query}

Documents:
{doc_summaries}

Knowledge Graph context:
{graph_text}
"""
        try:
            report = self.llm.generate(prompt, system_prompt=system_prompt)
            self.log(f"Synthesis complete. Generated report size: {len(report)} characters.")
            return report
        except Exception as e:
            self.log(f"Research synthesis error: {e}")
            return "Unable to synthesize information."
