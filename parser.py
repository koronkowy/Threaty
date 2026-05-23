import os
import requests
import json
import sys
from bs4 import BeautifulSoup
from datetime import date

def parse_job(url):
    # Retrieve API key from environment (GitHub Secrets will inject this)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set in environment.")
        sys.exit(1)

    print(f"Scraping: {url}...")
    
    # 1. Fetch the raw page content
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise error for bad status codes
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)[:15000]
    except Exception as e:
        return f"Error scraping: {e}"

    # 2. Refined Prompt for the 'Data Clerk'
    prompt = f"""
    Analyze the following job description and extract the data fields below.
    If a field is not found, use an empty string.

    Required JSON Schema:
    {{
      "title": "Job Title",
      "company": "Company Name",
      "url": "{url}",
      "company_url": "Main corporate website URL",
      "listed_locations": "Exact location text from the page",
      "eligibility_regions": "US-All, US-East, US-West, US-Central, or EMEA",
      "model": "Remote, Hybrid, or Onsite",
      "deadline": "YYYY-MM-DD or empty string",
      "post_date": "{date.today().isoformat()}"
    }}
    
    Job Text: {text}
    """
    
    # 3. REST call to Gemini
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    response = requests.post(endpoint, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        content = data['candidates'][0]['content']['parts'][0]['text']
        json_text = content.replace('```json', '').replace('```', '').strip()
        
        # Parse and return the structured JSON
        parsed_json = json.loads(json_text)
        # We leave 'id' for the GitHub Action to handle (or keep as 0 for review)
        parsed_json['id'] = 0 
        return json.dumps(parsed_json, indent=2)
    else:
        return f"API Error (Status {response.status_code}): {response.text}"

if __name__ == "__main__":
    # Allow URL to be passed via command line instead of manual input
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        print(parse_job(target_url))
    else:
        print("Usage: python parser.py <url>")