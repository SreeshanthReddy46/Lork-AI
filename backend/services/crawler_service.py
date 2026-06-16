import asyncio
import logging
import httpx
from urllib.parse import urlparse, urljoin
import urllib.robotparser
from bs4 import BeautifulSoup
import re

from services.database import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crawler_service")

USER_AGENT = "LorkAIBot/1.0"

def clean_whitespace(text: str) -> str:
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()

class ContentExtractor:
    @staticmethod
    def extract(html: str, base_url: str) -> dict:
        if not html:
            return {
                "title": "",
                "content": "",
                "headings": [],
                "links": [],
                "images": [],
                "tables": [],
                "metadata": {}
            }
            
        soup = BeautifulSoup(html, "html.parser")
        
        # Title
        title_tag = soup.find("title")
        title = title_tag.get_text().strip() if title_tag else ""
        
        # Metadata
        metadata = {}
        for meta in soup.find_all("meta"):
            name = meta.get("name", meta.get("property", "")).lower()
            content = meta.get("content", "").strip()
            if name and content:
                metadata[name] = content
                
        if not title and "title" in metadata:
            title = metadata["title"]
            
        # Clean boilerplate
        boilerplate_selectors = [
            "script", "style", "noscript", "iframe", "svg",
            "nav", "header", "footer", "aside", ".sidebar", ".navigation",
            ".nav", ".footer", ".menu", ".ads", ".advertisement", "#sidebar",
            "#header", "#footer", ".cookie-consent", ".modal"
        ]
        
        for selector in boilerplate_selectors:
            for element in soup.select(selector):
                element.decompose()
                
        # Headings
        headings = []
        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            heading_text = h.get_text().strip()
            if heading_text:
                headings.append({
                    "level": int(h.name[1]),
                    "text": heading_text
                })
                
        # Tables
        tables = []
        for table in soup.find_all("table"):
            table_data = []
            for row in table.find_all("tr"):
                row_data = [cell.get_text().strip() for cell in row.find_all(["td", "th"])]
                if any(row_data):
                    table_data.append(row_data)
            if table_data:
                tables.append(table_data)
                
        # Images
        images = []
        for img in soup.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", "").strip()
            if src:
                abs_src = urljoin(base_url, src)
                images.append({"src": abs_src, "alt": alt})
                
        # Links
        links = []
        base_domain = urlparse(base_url).netloc
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            link_text = a.get_text().strip()
            
            if not href or href.startswith("#") or href.lower().startswith("javascript:"):
                continue
                
            abs_url = urljoin(base_url, href)
            parsed_abs = urlparse(abs_url)
            
            if parsed_abs.scheme not in ["http", "https"]:
                continue
                
            link_item = {
                "url": abs_url,
                "text": link_text,
                "is_internal": parsed_abs.netloc == base_domain
            }
            if link_item not in links:
                links.append(link_item)
                
        # Content body text extraction
        content_lines = []
        body = soup.find("body") or soup
        for child in body.descendants:
            if child.name in ["p", "li"]:
                text = clean_whitespace(child.get_text())
                if text:
                    content_lines.append(text)
            elif child.name in ["h1", "h2", "h3"]:
                text = clean_whitespace(child.get_text())
                if text:
                    prefix = "#" * int(child.name[1])
                    content_lines.append(f"\n{prefix} {text}\n")
            elif child.name == "pre":
                text = child.get_text().strip()
                if text:
                    content_lines.append(f"\n```\n{text}\n```\n")
                    
        if not content_lines:
            text = clean_whitespace(body.get_text())
            if text:
                content_lines.append(text)
                
        clean_content = "\n".join(content_lines)
        clean_content = clean_whitespace(clean_content)
        
        return {
            "title": title or "Untitled Page",
            "content": clean_content,
            "headings": headings,
            "links": links,
            "images": images[:15],
            "tables": tables[:5],
            "metadata": metadata
        }

class WebCrawlerService:
    def __init__(self, concurrency: int = 5, delay: float = 0.5):
        self.concurrency = concurrency
        self.delay = delay
        self.semaphore = asyncio.Semaphore(concurrency)
        self.robots_cache = {}

    def can_crawl(self, url: str) -> bool:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        if domain not in self.robots_cache:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(urljoin(domain, "/robots.txt"))
            try:
                import requests
                resp = requests.get(urljoin(domain, "/robots.txt"), headers={"User-Agent": USER_AGENT}, timeout=2)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    rp.allow_all = True
            except Exception:
                rp.allow_all = True
            self.robots_cache[domain] = rp
            
        return self.robots_cache[domain].can_fetch(USER_AGENT, url)

    async def fetch_page(self, client: httpx.AsyncClient, url: str) -> str:
        if not self.can_crawl(url):
            logger.warning(f"Robots block: {url}")
            return ""
            
        async with self.semaphore:
            try:
                headers = {"User-Agent": USER_AGENT}
                response = await client.get(url, headers=headers, timeout=8.0, follow_redirects=True)
                if response.status_code == 200:
                    content_type = response.headers.get("Content-Type", "")
                    if "text/html" in content_type:
                        await asyncio.sleep(self.delay)
                        return response.text
            except Exception as e:
                logger.error(f"Fetch error {url}: {e}")
            return ""

    def add_url_to_queue(self, url: str, depth: int = 0):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO crawl_queue (url, status, depth) VALUES (?, 'pending', ?)",
                (url, depth)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error enqueueing {url}: {e}")
        finally:
            conn.close()

    def update_queue_status(self, url: str, status: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE crawl_queue SET status = ? WHERE url = ?", (status, url))
        conn.commit()
        conn.close()

    def save_crawled_page(self, url: str, data: dict) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        page_id = None
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO pages (url, title, clean_content, summary, raw_html, crawled_at, authority, freshness)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1.0, CURRENT_TIMESTAMP)
                """,
                (url, data["title"], data["content"], data.get("summary", ""), "", "")
            )
            page_id = cursor.lastrowid
            
            cursor.execute("DELETE FROM pages_fts WHERE rowid = ?", (page_id,))
            cursor.execute(
                "INSERT INTO pages_fts (rowid, title, content) VALUES (?, ?, ?)",
                (page_id, data["title"], data["content"])
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Db save error {url}: {e}")
            conn.rollback()
        finally:
            conn.close()
        return page_id

    async def crawl_site(self, start_url: str, max_pages: int = 10, max_depth: int = 2):
        self.add_url_to_queue(start_url, 0)
        pages_crawled = 0
        
        async with httpx.AsyncClient() as client:
            while pages_crawled < max_pages:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT url, depth FROM crawl_queue WHERE status = 'pending' ORDER BY depth ASC, added_at ASC LIMIT 1"
                )
                row = cursor.fetchone()
                conn.close()
                
                if not row:
                    break
                    
                target_url, depth = row["url"], row["depth"]
                self.update_queue_status(target_url, "crawling")
                
                if depth > max_depth:
                    self.update_queue_status(target_url, "done")
                    continue

                html = await self.fetch_page(client, target_url)
                if not html:
                    self.update_queue_status(target_url, "failed")
                    continue
                    
                extracted = ContentExtractor.extract(html, target_url)
                page_id = self.save_crawled_page(target_url, extracted)
                self.update_queue_status(target_url, "done")
                pages_crawled += 1
                
                if depth < max_depth and page_id:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    for link in extracted["links"]:
                        if link["is_internal"]:
                            cursor.execute("INSERT OR IGNORE INTO crawl_queue (url, status, depth) VALUES (?, 'pending', ?)", (link["url"], depth + 1))
                    conn.commit()
                    conn.close()

                await asyncio.sleep(0.1)
                
        return pages_crawled
