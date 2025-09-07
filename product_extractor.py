import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class UniversalProductExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.huggingface_api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        self.hf_token = None
        
    def _scrape_with_selenium(self, url):
        """Use Selenium to scrape JavaScript-rendered content"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            # Use WebDriver Manager to automatically handle ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            driver.set_page_load_timeout(30)
            
            driver.get(url)
            
            # Wait for product content to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(2)  # Additional wait for dynamic content
            except:
                pass
            
            # Get page source and parse with BeautifulSoup
            page_source = driver.page_source
            driver.quit()
            
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'noscript', 'iframe', 'header', 'footer', 'nav', 'aside']):
                element.decompose()
            
            # Get clean text
            text = soup.get_text()
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text[:5000]  # Limit length
            
        except Exception as e:
            print(f"Selenium scraping failed: {e}")
            return None
    
    def _scrape_with_advanced_headers(self, url):
        """Advanced scraping with realistic headers"""
        try:
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Referer': 'https://www.google.com/',
            }
            
            time.sleep(2)
            
            response = self.session.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'noscript', 'iframe', 'header', 'footer', 'nav', 'aside']):
                element.decompose()
            
            # Get clean text
            text = soup.get_text()
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text[:3000]
            
        except Exception as e:
            print(f"Advanced headers scraping failed: {e}")
            return None
    
    def extract_text_from_url(self, url):
        """Extract text content from URL with multiple fallbacks"""
        approaches = [
            self._scrape_with_selenium,
            self._scrape_with_advanced_headers,
        ]
        
        for approach in approaches:
            try:
                result = approach(url)
                if result and len(result) > 100:
                    return result
            except Exception as e:
                print(f"Approach {approach.__name__} failed: {e}")
                continue
        
        # Final fallback - use URL structure and basic info
        return self._get_url_based_content(url)
    
    def _get_url_based_content(self, url):
        """Generate content based on URL structure when scraping fails"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path_parts = parsed_url.path.split('/')
        
        # Extract potential product info from URL
        product_info = []
        for part in path_parts:
            if part and len(part) > 3 and not any(x in part for x in ['http', 'www', 'com', 'product']):
                clean_part = part.replace('-', ' ').replace('_', ' ').title()
                product_info.append(clean_part)
        
        return f"Product page from {domain}. Product details: {' '.join(product_info)}"
    
    def query_llm(self, prompt):
        """Use Hugging Face's free inference API"""
        try:
            headers = {}
            if self.hf_token:
                headers["Authorization"] = f"Bearer {self.hf_token}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.1,
                    "return_full_text": False
                }
            }
            
            response = requests.post(
                self.huggingface_api_url, 
                headers=headers, 
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result[0]['generated_text']
            else:
                print(f"LLM API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"LLM query failed: {e}")
            return None
    
    def structure_with_llm(self, raw_text, url):
        """Use LLM to structure product data for ANY product type"""
        prompt = f"""
        Analyze this product webpage content and extract structured information.
        Return ONLY valid JSON format with these fields:
        
        {{
          "product_name": "string (extract the main product title)",
          "price": "string with currency symbol or null",
          "description": "string (brief product description) or null", 
          "image_url": "string or null",
          "availability": "string: 'In Stock', 'Out of Stock', 'Pre-order', or null",
          "rating": "number or null",
          "review_count": "number or null",
          "brand": "string or null",
          "category": "string (e.g., Electronics, Fashion, Home, Books, etc.) or null",
          "specifications": {{"key1": "value1", "key2": "value2"}} or null,
          "features": ["feature1", "feature2"] or null,
          "key_features": ["key feature 1", "key feature 2"] or null
        }}
        
        IMPORTANT: 
        - Extract only from the provided content
        - Use null for missing information
        - Return ONLY JSON, no other text
        - Be accurate for ANY type of product (electronics, clothing, books, etc.)
        
        Content: {raw_text}
        
        JSON:
        """
        
        try:
            llm_response = self.query_llm(prompt)
            
            if llm_response:
                # Clean and extract JSON from response
                cleaned_response = re.sub(r'```json|```', '', llm_response).strip()
                json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                
                if json_match:
                    product_data = json.loads(json_match.group(0))
                    product_data['url'] = url
                    product_data['scraped_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    product_data['extraction_method'] = 'llm_analysis'
                    return product_data
            
            # If LLM fails, use regex fallback
            return self._regex_fallback_extraction(raw_text, url)
            
        except Exception as e:
            print(f"LLM processing failed: {e}")
            return self._regex_fallback_extraction(raw_text, url)
    
    def _regex_fallback_extraction(self, text, url):
        """Regex-based fallback for when LLM fails"""
        try:
            # Basic pattern matching for common e-commerce data
            price_match = re.search(r'[₹$€£]\s*[\d,]+\.?\d*', text)
            rating_match = re.search(r'(\d+\.\d+)\s*(?:out of|stars?|rating)', text, re.IGNORECASE)
            reviews_match = re.search(r'(\d[\d,]*)\s*(reviews|ratings|customers)', text, re.IGNORECASE)
            
            return {
                "product_name": self._extract_name_from_url(url),
                "price": price_match.group(0) if price_match else None,
                "description": self._extract_description(text),
                "image_url": None,
                "availability": self._extract_availability(text),
                "rating": float(rating_match.group(1)) if rating_match else None,
                "review_count": int(reviews_match.group(1).replace(',', '')) if reviews_match else None,
                "brand": self._extract_brand(text, url),
                "category": self._extract_category(text, url),
                "specifications": self._extract_specifications(text),
                "features": self._extract_features(text),
                "key_features": self._extract_key_features(text),
                "seller": self._extract_seller(text),
                "url": url,
                "scraped_at": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "extraction_method": "regex_fallback"
            }
        except Exception as e:
            print(f"Regex fallback failed: {e}")
            return self._create_minimal_response(url)
    
    def _extract_name_from_url(self, url):
        """Extract product name from URL structure"""
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        for part in path_parts:
            if (len(part) > 10 and ('-' in part or '_' in part) and 
                not any(x in part for x in ['http', 'www', 'com', 'product'])):
                return part.replace('-', ' ').replace('_', ' ').title()
        return "Product"
    
    def _extract_description(self, text):
        """Extract potential description"""
        sentences = re.split(r'[.!?]', text)
        for sentence in sentences:
            clean_sentence = sentence.strip()
            if 20 <= len(clean_sentence) <= 150:
                return clean_sentence + '.'
        return None
    
    def _extract_availability(self, text):
        """Extract availability status"""
        text_lower = text.lower()
        if any(x in text_lower for x in ['out of stock', 'sold out', 'unavailable']):
            return "Out of Stock"
        if any(x in text_lower for x in ['pre-order', 'preorder', 'coming soon']):
            return "Pre-order"
        if any(x in text_lower for x in ['in stock', 'available', 'add to cart', 'buy now']):
            return "In Stock"
        return None
    
    def _extract_brand(self, text, url):
        """Extract brand information"""
        brands = ['samsung', 'apple', 'nike', 'adidas', 'sony', 'lg', 'xiaomi', 
                 'oneplus', 'dell', 'hp', 'lenovo', 'asus', 'canon', 'nikon', 'mi', 'croma']
        combined_text = (text + ' ' + url).lower()
        for brand in brands:
            if brand in combined_text:
                return brand.capitalize()
        return None
    
    def _extract_category(self, text, url):
        """Extract product category"""
        categories = {
            'electronics': ['phone', 'tv', 'laptop', 'camera', 'headphone', 'electronic', 'smartphone', 'tablet'],
            'fashion': ['shirt', 'dress', 'shoe', 'jeans', 'fashion', 'clothing', 'apparel', 'wear'],
            'home': ['furniture', 'kitchen', 'home', 'decor', 'appliance', 'garden', 'living'],
            'books': ['book', 'novel', 'author', 'publisher', 'literature'],
            'sports': ['sport', 'fitness', 'gym', 'outdoor', 'exercise', 'training']
        }
        
        combined_text = (text + ' ' + url).lower()
        for category, keywords in categories.items():
            if any(keyword in combined_text for keyword in keywords):
                return category.capitalize()
        return "General"
    
    def _extract_specifications(self, text):
        """Extract product specifications"""
        specs = {}
        # Look for key: value patterns
        spec_patterns = [
            r'([A-Za-z\s]+):\s*([^\n\.]+)',
            r'([A-Za-z\s]+)\s*[-–]\s*([^\n\.]+)'
        ]
        
        for pattern in spec_patterns:
            matches = re.findall(pattern, text)
            for key, value in matches:
                key = key.strip()
                value = value.strip()
                if 2 <= len(key) <= 30 and 1 <= len(value) <= 50:
                    specs[key] = value
        
        return specs if specs else None
    
    def _extract_features(self, text):
        """Extract product features"""
        features = []
        # Look for bullet points or feature lists
        bullet_patterns = [r'•\s*(.+?)(?=\.|$)', r'-\s*(.+?)(?=\.|$)', r'\d+\.\s*(.+?)(?=\.|$)']
        
        for pattern in bullet_patterns:
            matches = re.findall(pattern, text)
            features.extend([match.strip() for match in matches if 10 <= len(match.strip()) <= 100])
        
        return features[:5] if features else None
    
    def _extract_key_features(self, text):
        """Extract key features"""
        features = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if (20 <= len(line) <= 80 and 
                line[0].isupper() and 
                not any(char in line for char in ['http', 'www', '@', ':'])):
                features.append(line)
                if len(features) >= 5:
                    break
        return features if features else None
    
    def _extract_seller(self, text):
        """Extract seller name from text with improved patterns for multiple e-commerce sites"""
        # Common patterns for seller info across different e-commerce platforms
        patterns = [
            # General patterns that work across multiple sites
            r'Sold\s+by\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)(?:\s*\(.*\))?',
            r'Seller\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)(?:\s*\(.*\))?',
            r'Fulfilled\s+by\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)',
            r'Provided\s+by\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)',
            r'Distributed\s+by\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)',
            r'Vendor\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)',
            r'Retailer\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)',
            
            # Site-specific patterns
            # Amazon
            r'Ships from[s\s]*[:\-]?\s*([A-Za-z0-9 &.,\-]+)',
            r'by\s*([A-Za-z0-9 &.,\-]+)(?:\s*\|.*)?$',
            
            # eBay
            r'Sold\s+by\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)\s*\(\d+\)',
            r'from\s*([A-Za-z0-9 &.,\-]+)\s*\(\d+\)',
            
            # Walmart
            r'Sold\s+& shipped by\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)',
            
            # Best Buy
            r'Sold\s+by\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)\s*online',
        ]
        
        # First, try to find seller using patterns
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                seller = match.group(1).strip()
                # Clean up the seller name
                seller = re.sub(r'^\W+|\W+$', '', seller)  # Remove leading/trailing non-word chars
                seller = re.sub(r'\s+', ' ', seller)  # Normalize whitespace
                
                # Validate the seller name
                if self._is_valid_seller(seller):
                    return seller.title()
        
        # If no pattern matched, try to find seller in common e-commerce phrases
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(phrase in line_lower for phrase in ['sold by', 'seller:', 'fulfilled by', 'provided by']):
                # Extract the potential seller name after the phrase
                for phrase in ['sold by', 'seller', 'fulfilled by', 'provided by']:
                    if phrase in line_lower:
                        # Use regex to extract text after the phrase
                        match = re.search(r'{}\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)'.format(phrase), line, re.IGNORECASE)
                        if match:
                            potential_seller = match.group(1).strip()
                            if self._is_valid_seller(potential_seller):
                                return potential_seller.title()
        
        # If we still haven't found a seller, try to look for the brand name as a fallback
        brand_match = re.search(r'Brand\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)', text, re.IGNORECASE)
        if brand_match:
            brand = brand_match.group(1).strip()
            if self._is_valid_seller(brand):
                return brand.title()
        
        return None

    def _is_valid_seller(self, seller):
        """Check if the extracted seller name is valid"""
        if not seller or len(seller) < 2 or len(seller) > 50:
            return False
        
        # Common false positives to exclude
        false_positives = [
            'return', 'policy', 'warranty', 'description', 'cart', 'electronics', 
            'tvs', 'appliances', 'men', 'women', 'baby', 'kids', 'home', 'furniture',
            'sports', 'books', 'more', 'flights', 'offer', 'zone', 'add', 'buy', 'now',
            'early', 'bird', 'deals', 'starts', 'in', 'hrs', 'days', 'brand', 'audio',
            'video', 'support', 'service', 'help', 'contact', 'about', 'information'
        ]
        
        # Check if seller contains any false positive words
        seller_lower = seller.lower()
        for fp in false_positives:
            if fp in seller_lower:
                return False
        
        # Check for numeric sellers (e.g., "12345")
        if re.match(r'^\d+$', seller):
            return False
        
        return True
    
    def extract_product_data(self, url):
        """Main method to extract product data for ANY product"""
        try:
            print(f"🌐 Extracting from: {url}")
            print("⏳ This may take a moment...")
            
            raw_text = self.extract_text_from_url(url)
            print(f"📝 Content length: {len(raw_text)} characters")
            
            # If we have substantial content, try LLM processing
            if len(raw_text) > 100 and not raw_text.startswith("Product page from"):
                print("🤖 Analyzing with AI...")
                product_data = self.structure_with_llm(raw_text, url)
            else:
                # Use regex fallback for minimal content
                product_data = self._regex_fallback_extraction(raw_text, url)
            
            return product_data
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return self._create_minimal_response(url)

def main():
    print("=" * 60)
    print("🌐 UNIVERSAL PRODUCT EXTRACTOR")
    print("=" * 60)
    print("Works with ANY product category using AI")
    print("=" * 60)
    
    # Get URL from user
    url = input("Enter product URL: ").strip()
    
    if not url:
        print("❌ No URL provided. Exiting.")
        return
    
    if not url.startswith('http'):
        url = 'https://' + url
    
    # Create extractor
    extractor = UniversalProductExtractor()
    
    try:
        # Extract data
        result = extractor.extract_product_data(url)
        
        print("\n" + "=" * 60)
        print("✅ EXTRACTION COMPLETE")
        print("=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("=" * 60)
        
        # Save to file
        filename = f"product_data_{int(time.time())}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
