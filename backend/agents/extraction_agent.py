from agents.base import BaseAgent, AgentBus
from services.llm import LLMService
from services.crawler_service import ContentExtractor

class ExtractionAgent(BaseAgent):
    def __init__(self, llm: LLMService, bus: AgentBus):
        super().__init__("Content Extraction Agent", llm, bus)

    def extract_page_data(self, html: str, url: str) -> dict:
        self.log(f"Parsing raw HTML from {url}...")
        
        extracted = ContentExtractor.extract(html, url)
        
        char_count = len(extracted.get("content", ""))
        link_count = len(extracted.get("links", []))
        heading_count = len(extracted.get("headings", []))
        
        self.log(f"Extraction successful: title='{extracted['title']}', size={char_count} chars, links={link_count}, headings={heading_count}")
        return extracted
