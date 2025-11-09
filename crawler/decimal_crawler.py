import sys
import os
import scrapy
import re
import json
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
import uuid
import time
from urllib.parse import urlparse, urlunparse

# 🛠 Fix import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import insert_data, initialize_database

# ✅ Import AI and NER modules
from ner_utils import extract_entities
from ai_utils import GeminiAIProcessor, detect_and_classify_leaks
import json

# 🛡 Setup Proxy
os.environ['http_proxy'] = 'http://127.0.0.1:8118'
os.environ['https_proxy'] = 'http://127.0.0.1:8118'

# 🚀 Read URL from argument
if len(sys.argv) < 2:
    print("❌ ERROR: Please provide a starting .onion URL as an argument.\nExample:\n  python3 crawler/decimal_crawler.py http://example.onion/")
    sys.exit(1)

start_url = sys.argv[1].strip()

# 🌎 Track visited URLs (use canonical, queryless dedupe key)
visited_urls = set()
pages_scraped = 0


def make_dedupe_key(url: str) -> str:
    """Create a canonical key for URL de-duplication.
    - lower-case scheme/host
    - strip query and fragment
    - normalize trailing slash
    """
    try:
        parsed = urlparse(url)
        scheme = (parsed.scheme or 'http').lower()
        netloc = (parsed.netloc or '').lower()
        path = parsed.path or '/'
        # Collapse multiple trailing slashes to single and ensure at least '/'
        path = re.sub(r'/+$', '/', path) if path != '/' else '/'
        return urlunparse((scheme, netloc, path, '', '', ''))
    except Exception:
        return url

# 📄 Load keywords from keywords.json
def load_keywords():
    try:
        with open('keywords.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ ERROR loading keywords.json: {e}")
        return []

keywords_list = load_keywords()

def generate_run_id():
    return str(uuid.uuid4()) + "_" + str(int(time.time()))

class DecimalCrawlerSpider(scrapy.Spider):
    name = "decimal_crawler"

    custom_settings = {
        'DOWNLOAD_DELAY': 1.5,
        'RETRY_TIMES': 5,
        'HTTPPROXY_ENABLED': True,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
        },
        'LOG_LEVEL': 'WARNING',
        'REQUEST_FINGERPRINTER_IMPLEMENTATION': '2.7'
    }

    def __init__(self, *args, **kwargs):
        super(DecimalCrawlerSpider, self).__init__(*args, **kwargs)
        initialize_database()
        self.start_urls = [start_url]
        self.run_id = generate_run_id()
        
        # Initialize AI processor (respect AI_PROCESSING_ENABLED)
        self.ai_enabled = os.getenv('AI_PROCESSING_ENABLED', 'true').lower() in ('1', 'true', 'yes', 'on')
        if self.ai_enabled:
            try:
                self.ai_processor = GeminiAIProcessor()
                print(f"🧠 AI processor initialized successfully")
            except Exception as e:
                print(f"⚠ AI processor failed to initialize: {str(e)}")
                print("Continuing with basic regex-only detection...")
                self.ai_processor = None
                self.ai_enabled = False
        else:
            self.ai_processor = None
            print("ℹ️ AI processing disabled via AI_PROCESSING_ENABLED=false; running regex-only.")
        
        print(f"🚀 Starting crawl with run ID: {self.run_id}")

    def parse(self, response):
        global visited_urls, pages_scraped

        url = response.url
        dedupe_key = make_dedupe_key(url)
        if dedupe_key in visited_urls:
            return
        visited_urls.add(dedupe_key)

        print(f"🔍 Processing URL: {url} -> {dedupe_key}")

        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else 'No Title'
        text = soup.get_text()

        # 🔎 Enhanced Entity Extraction with AI
        entities = extract_entities(text)
        flat_entities = []
        for category, matches in entities.items():
            for value in matches:
                flat_entities.append(f"{category}:{value}")
        entity_str = ",".join(flat_entities)
        
        # Traditional keyword matching
        matched_keywords = [kw for kw in keywords_list.get('terms', []) if kw.lower() in text.lower()]
        
        # AI-powered leak detection and classification
        ai_classification = None
        leak_severity = None
        ai_confidence = 0.0
        detection_method = "regex"
        local_detection_results = None
        gemini_detection_results = None
        
        if self.ai_enabled and (entities or matched_keywords):
            try:
                # Run AI detection workflow
                ai_results = detect_and_classify_leaks(text, self.ai_processor)
                
                # Extract AI analysis results
                if ai_results.get('detection_method') == 'hybrid':
                    detection_method = "ai_hybrid"
                    local_detection_results = json.dumps(ai_results.get('local_detection', {}))
                    
                    gemini_results = ai_results.get('ai_detection', {})
                    gemini_detection_results = json.dumps(gemini_results)
                    
                    if gemini_results.get('leak_detected', False):
                        ai_confidence = gemini_results.get('confidence_score', 0) / 100.0
                        leak_severity = gemini_results.get('severity', 'LOW')
                        
                        # Determine primary classification based on detected entities
                        detected_entities = gemini_results.get('detected_entities', {})
                        if detected_entities.get('Aadhaar'):
                            ai_classification = "Aadhaar"
                        elif detected_entities.get('PAN'):
                            ai_classification = "PAN"
                        elif detected_entities.get('Banking'):
                            ai_classification = "Banking/Financial"
                        elif detected_entities.get('Telecom'):
                            ai_classification = "Telecom"
                        else:
                            ai_classification = "General PII"
                        
                        print(f"🤖 AI Detection: {ai_classification} ({leak_severity}) - Confidence: {ai_confidence:.2f}")
                    else:
                        detection_method = "regex"
                else:
                    detection_method = "regex"
                    local_detection_results = json.dumps(ai_results.get('local_detection', {}))
                    
            except Exception as e:
                print(f"⚠ AI processing failed for {url}: {str(e)}")
                detection_method = "regex"
        
        print(f"🧠 Entities Found at {url}: {entity_str}")
        if ai_classification:
            print(f"🎯 AI Classification: {ai_classification} | Severity: {leak_severity} | Confidence: {ai_confidence:.2f}")

        # Insert data with AI results (store canonical URL to avoid DB duplicates)
        insert_data(
            url=dedupe_key,
            title=title,
            matched_keywords=','.join(matched_keywords),
            run_id=self.run_id,
            named_entities=entity_str,
            ai_classification=ai_classification,
            leak_severity=leak_severity,
            ai_confidence=ai_confidence,
            detection_method=detection_method,
            local_detection_results=local_detection_results,
            gemini_detection_results=gemini_detection_results
        )

        pages_scraped += 1
        print(f"✅ [{pages_scraped}] Scraped and saved: {dedupe_key}")

        if pages_scraped % 10 == 0:
            print(f"💓 Heartbeat: {pages_scraped} pages scraped so far...")

        # Continue crawling links
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            if any(href.startswith(prefix) for prefix in ('javascript:', 'mailto:', '#', 'tel:', 'ftp:', '220:')):
                continue

            if href.startswith("http://") or href.startswith("https://"):
                next_link = href
            elif href.startswith("/"):
                next_link = response.urljoin(href)
            else:
                continue

            try:
                parsed = urlparse(next_link)
                if not parsed.scheme or not parsed.netloc:
                    continue
            except Exception as e:
                print(f"⚠ Skipping malformed URL: {href} — {e}")
                continue

            next_key = make_dedupe_key(next_link)
            if next_key not in visited_urls:
                yield scrapy.Request(url=next_link, callback=self.parse)

if __name__ == "__main__":
    print("\n🚀 Starting Decimal Crawler...\n")
    process = CrawlerProcess()
    process.crawl(DecimalCrawlerSpider)
    process.start()
