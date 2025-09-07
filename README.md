Universal Product Extractor

The Universal Product Extractor is a Python-based tool for extracting structured product data from any e-commerce website.
It combines Selenium, BeautifulSoup, and Requests for scraping, and can optionally use Hugging Face LLMs for natural language processing and JSON structuring.

Extracts:

Product Name
Price
Description
Features & Specifications
Rating & Review Count
Availability Status
Brand & Category
Seller Information
Refund/Return Policy

AI-Powered Structuring with Hugging Face LLMs (optional)
Regex-based fallback extraction (when AI or dynamic scraping fails)
Exports results as JSON

Installation
1. Clone the repository
```
git clone https://github.com/your-username/universal-product-extractor.git
cd universal-product-extractor
```

3. Create a virtual environment (recommended)
```
python -m venv venv
```

Activate it:
Windows:
```
venv\Scripts\activate
```

macOS/Linux:
```
source venv/bin/activate
```

4. Install Dependency
```
pip install requests beautifulsoup4 selenium webdriver-manager
```

Optional (for Hugging Face API):
```
pip install huggingface-hub
```

Requirements
Python 3.8+
Google Chrome (latest)
ChromeDriver (handled automatically by webdriver-manager)
Hugging Face Account
 + API Token (optional)

Usage
Run the script:
```
python product_extractor.py
```

You’ll be prompted for a product URL:
Enter product URL: https://www.amazon.com/dp/B0C12345XYZ

The script will:
Scrape the page with Selenium or Requests
Clean and parse text with BeautifulSoup
Structure extracted data using LLM (if available) or regex fallback
Save results into a JSON file
📊 Example Output
{
  "product_name": "Apple iPhone 14 Pro Max",
  "price": "$1099.00",
  "description": "Latest iPhone model with Dynamic Island and A16 Bionic chip.",
  "image_url": null,
  "availability": "In Stock",
  "rating": 4.7,
  "review_count": 15234,
  "brand": "Apple",
  "category": "Electronics",
  "specifications": {
    "Screen Size": "6.7 inches",
    "Storage": "256 GB",
    "Camera": "48 MP"
  },
  "features": [
    "Dynamic Island for seamless alerts",
    "48 MP camera with ProRAW",
    "Super Retina XDR display"
  ],
  "key_features": [
    "Powerful A16 Bionic chip",
    "Ceramic Shield glass",
    "5G Enabled"
  ],
  "seller": "Apple Store",
  "url": "https://www.amazon.com/dp/B0C12345XYZ",
  "scraped_at": "2025-09-06T18:45:00Z",
  "extraction_method": "llm_analysis"
}
