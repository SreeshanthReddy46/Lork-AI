import asyncio
from agents.base import BaseAgent, AgentBus
from services.llm import LLMService
from services.crawler_service import WebCrawlerService

class CrawlerAgent(BaseAgent):
    def __init__(self, llm: LLMService, bus: AgentBus, crawler_service: WebCrawlerService = None):
        super().__init__("Crawler Agent", llm, bus)
        self.crawler = crawler_service or WebCrawlerService()

    async def crawl(self, start_url: str, max_pages: int = 5, max_depth: int = 1) -> int:
        self.log(f"Queuing recursive crawl starting at '{start_url}' (max_pages={max_pages}, depth={max_depth})...")
        
        # We can run this in an async task
        pages_crawled = await self.crawler.crawl_site(start_url, max_pages=max_pages, max_depth=max_depth)
        self.log(f"Crawl job completed successfully. Added {pages_crawled} new documents to index.")
        return pages_crawled
