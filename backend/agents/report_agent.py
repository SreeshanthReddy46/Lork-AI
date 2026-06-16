from agents.base import BaseAgent, AgentBus
from services.llm import LLMService

class ReportAgent(BaseAgent):
    def __init__(self, llm: LLMService, bus: AgentBus):
        super().__init__("Report Generation Agent", llm, bus)

    def generate_report(self, query: str, cited_text: str, sources: list[dict]) -> dict:
        self.log("Structuring final presentation layouts (Executive Summary, Key Metrics, Timeline, and References)...")
        
        # We can construct a clean structured layout.
        # Let's organize citations section
        refs_md = "\n## Sources & References\n\n"
        for s in sources:
            refs_md += f"- **[{s['id']}]** [{s['title']}]({s['url']})\n"
            
        full_report = cited_text + "\n" + refs_md
        
        self.log("Report compilation and template formatting finished.")
        return {
            "title": f"Research Report: {query}",
            "content": full_report,
            "raw_cited_text": cited_text
        }
