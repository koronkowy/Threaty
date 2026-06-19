import os
import requests
import json
import sys
import time
import random
from bs4 import BeautifulSoup
from datetime import date

def parse_job_with_gemini(url):
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not set in environment.", file=sys.stderr)
        return None
    
    # 1. Scrape the page
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
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
      "eligibility_regions": "Map locations to: US-All, US-East, US-West, US-Central, EMEA, LATAM, or APAC",
      "model": "Remote, Hybrid, or Onsite",
      "deadline": "YYYY-MM-DD or empty string",
      "post_date": "{date.today().isoformat()}"
    }}

    Rules:
        - If a field is missing, use an empty string. Do not hallucinate.
        - Output ONLY the JSON block.

        - Work Model ('model') Extraction Logic:
        1. Scan the raw text or scraping tags for explicit ATS telemetry, tracking properties, or metadata labels such as:
            - '#LI-Remote', '#LI-Hybrid', '#LI-Onsite'
            - 'workplaceTypes: 2' (LinkedIn Remote indicator)
            - 'Location Type: Remote', 'Work Style: Hybrid'
        2. If any matching tag or string is found, accurately set the model parameter to 'Remote', 'Hybrid', or 'Onsite'.
        3. Fallback: If no metadata markers exist, evaluate the body text for standard structural clauses (e.g., "work from anywhere", "in-office requirements", "2 days a week in our Prague office") to deduce the correct setting.

        - Regional Mapping logic:
        - Foster City, Sunnyvale, Draper, Salt Lake City, Provo, Santa Clara, Milpitas, Redwood City, Cupertino: Map to 'US-West'.
        - Queretaro, Monterrey, Guadalajara, Mexico City: Map to 'LATAM'.
        - Bangalore, Mumbai, Tokyo, etc.: Map to 'APAC'.
        - Germany, UK, etc.: Map to 'EMEA'.

    Job Text: {text}
    """
    
    # 3. Use the verified 2.0-flash model to avoid 404s
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    # 4. Exponential backoff loop to handle 503/429 spikes safely
    max_retries = 5
    base_delay = 4
    
    for attempt in range(max_retries):
        try:
            response = requests.post(endpoint, json=payload, timeout=30)
            
            # Catch server overloads and apply randomized jitter
            if response.status_code in [429, 503]:
                delay = (base_delay ** attempt) + random.uniform(0, 2)
                print(f"[!] Server reported {response.status_code}. Retrying in {delay:.2f}s... (Attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                time.sleep(delay)
                continue
                
            response.raise_for_status()
            content = response.json()['candidates'][0]['content']['parts'][0]['text']
            json_text = content.replace('```json', '').replace('```', '').strip()
            return json.loads(json_text)
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"API Error for {url}: {e}", file=sys.stderr)
                return None
            time.sleep(base_delay)

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    input_data = sys.argv[1]
    urls = [line.strip() for line in input_data.splitlines() if line.strip().startswith('http')]
    
    db_file = 'jobs.json'
    try:
        with open(db_file, 'r') as f:
            jobs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        jobs = []

    failed_urls = []
    success_count = 0
    
    for url in urls:
        # Deduplication check - save your API quota!
        if any(job.get('url') == url for job in jobs):
            print(f"[-] Skipping duplicate link: {url}")
            continue
            
        print(f"[*] Processing: {url}")
        new_job = parse_job_with_gemini(url)
        
        if new_job:
            jobs.append(new_job)
            success_count += 1
            print(f"[+] Successfully added: {new_job.get('title', 'Unknown Title')}")
            time.sleep(2) # Polite spacer between API calls
        else:
            failed_urls.append(url)

    # Save the full updated list safely
    with open(db_file, 'w') as f:
        json.dump(jobs, f, indent=2)
    
    # Print failure block for the GitHub Action to catch
    if failed_urls:
        print("\nFAILED_URLS_START")
        for f_url in failed_urls:
            print(f_url)
        print("FAILED_URLS_END")
        
    print(f"[*] Batch processing complete. Added: {success_count}, Failed: {len(failed_urls)}")

if __name__ == "__main__":
    main()