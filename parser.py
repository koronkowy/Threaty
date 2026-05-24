import os
import requests
import json
import sys
from bs4 import BeautifulSoup
from datetime import date

def parse_job_with_gemini(url):
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # 1. Scrape the page
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)[:15000]
    except Exception as e:
        print(f"Error scraping {url}: {e}", file=sys.stderr)
        return None

    # 2. Gemini Prompt
    prompt = f"""
    Analyze the following job description and extract the data fields below.
    Required JSON Schema (Do not deviate):
    {{
      "title": "Job Title",
      "company": "Company Name",
      "status": "active",
      "url": "{url}",
      "company_url": "Main corporate website URL",
      "listed_locations": "Exact city/state listed",
      "eligibility_regions": "Map locations to: US-All, US-East, US-West, US-Central, EMEA, or APAC",
      "model": "Remote, Hybrid, or Onsite",
      "deadline": "YYYY-MM-DD or empty string",
      "post_date": "{date.today().isoformat()}"
    }}
    Rules: 
    - If a field is missing, use an empty string. Do not hallucinate.
    - Output ONLY the JSON block.
    - If listed_locations is Bangalore, Mumbai, Tokyo, etc., eligibility_regions MUST be 'APAC'.
    - If listed_locations is in Germany, UK, etc., eligibility_regions MUST be 'EMEA'.
    - deadline refers to is a job posting has a submission deadline or position closing date

    Job Text: {text}
    """
    
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    response = requests.post(endpoint, json=payload)
    
    if response.status_code == 200:
        content = response.json()['candidates'][0]['content']['parts'][0]['text']
        json_text = content.replace('```json', '').replace('```', '').strip()
        return json.loads(json_text)
    else:
        print(f"API Error for {url}: {response.text}", file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    # Split the input issue body into a list of URLs
    input_data = sys.argv[1]
    urls = [line.strip() for line in input_data.splitlines() if line.strip().startswith('http')]
    
    # Load existing database
    db_file = 'jobs.json'
    try:
        with open(db_file, 'r') as f:
            jobs = json.load(f)
    except FileNotFoundError:
        jobs = []

    # Process each URL
    for url in urls:
        print(f"[*] Processing: {url}")
        new_job = parse_job_with_gemini(url)
        if new_job:
            jobs.append(new_job)
            print(f"[+] Successfully added: {new_job['title']}")

    # Save the full updated list
    with open(db_file, 'w') as f:
        json.dump(jobs, f, indent=2)
    print(f"[*] Batch processing complete. Total jobs: {len(jobs)}")

if __name__ == "__main__":
    main()