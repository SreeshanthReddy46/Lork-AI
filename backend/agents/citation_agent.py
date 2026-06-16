from agents.base import BaseAgent, AgentBus
from services.llm import LLMService

class CitationAgent(BaseAgent):
    def __init__(self, llm: LLMService, bus: AgentBus):
        super().__init__("Citation Agent", llm, bus)

    def append_citations(self, query: str, report: str, documents: list[dict]) -> tuple[str, list[dict]]:
        self.log("Tracing evidence segments and embedding inline citation link codes [1], [2], etc...")
        
        doc_refs = ""
        sources = []
        for idx, doc in enumerate(documents):
            source_id = idx + 1
            doc_refs += f"Source [{source_id}]: {doc['title']} (URL: {doc['url']})\nSnippet: {doc['content'][:600]}\n\n"
            sources.append({
                "id": source_id,
                "url": doc["url"],
                "title": doc["title"]
            })
            
        system_prompt = """You are a Citation Agent.
Given a user query, a research report, and a list of sources, rewrite the report to embed inline citations like [1], [2] next to claims that match the respective sources.
Keep the overall markdown structures (headings, lists, comparisons) intact.
Only cite sources when their snippets actually contain evidence for the claim.
If a claim is not supported by any source, remove it or rewrite it to align with the sources.

Format response as text only.
"""
        prompt = f"Query: {query}\n\nReport:\n{report}\n\nSources:\n{doc_refs}"
        
        try:
            cited_text = self.llm.generate(prompt, system_prompt=system_prompt)
            self.log("Citation and source linking completed.")
            return cited_text, sources
        except Exception as e:
            self.log(f"Citation linking failed: {e}")
            return report, sources
class QueryUnderstandingAgent:
    pass
