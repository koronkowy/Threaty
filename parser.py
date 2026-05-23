import os
import requests
import json
import sys
from bs4 import BeautifulSoup
from datetime import date

def parse_job(url):
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not set in environment.", file=sys.stderr)
        sys.exit(1)

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)[:15000]
    except Exception as e:
        print(f"Error scraping: {e}", file=sys.stderr)
        sys.exit(1)

    prompt = f"""
    Analyze the following job description and extract the data fields below.
    Required JSON Schema:
    {{
      "title": "Job Title",
      "company": "Company Name",
      "url": "{url}",
      "company_url": "Main corporate website URL",
      "listed_locations": "Exact location text",
      "eligibility_regions": "US-All, US-East, US-West, US-Central, or EMEA",
      "model": "Remote, Hybrid, or Onsite",
      "deadline": "YYYY-MM-DD or empty string",
      "post_date": "{date.today().isoformat()}"
    }}
    Job Text: {text}
    """
    
    # Use the proven 'gemini-1.5-flash' endpoint
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    response = requests.post(endpoint, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        content = data['candidates'][0]['content']['parts'][0]['text']
        json_text = content.replace('```json', '').replace('```', '').strip()
        parsed_json = json.loads(json_text)
        parsed_json['id'] = 0 # Placeholder for PR review
        return json.dumps(parsed_json, indent=2)
    else:
        print(f"API Error: {response.text}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Print ONLY the JSON output to stdout so it gets captured by the workflow
        print(parse_job(sys.argv[1]))
    else:
        sys.exit(1)