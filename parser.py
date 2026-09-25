import os
import time
import requests
import json
import sys
from bs4 import BeautifulSoup
from datetime import date
from error_tracker import log_api_error, update_badges

def parse_job_with_gemini(url):
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # 1. Scrape the page
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code in [404, 410]:
            print(f"Dead link detected (HTTP {response.status_code}): {url}", file=sys.stderr)
            return None, "DEAD_LINK"

        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract extra text from application/ld+json
        extra_text = []
        for script in soup.find_all('script', type='application/ld+json'):
            if script.string:
                extra_text.append(script.string)

        # Extract meta tags
        for meta in soup.find_all('meta', attrs={'name': ['description', 'keywords']}):
            if meta.get('content'):
                extra_text.append(meta['content'])
        for meta in soup.find_all('meta', property=['og:description', 'og:title']):
            if meta.get('content'):
                extra_text.append(meta['content'])

        text = soup.get_text(separator=' ', strip=True)[:15000]
        combined_text = text + " " + " ".join(extra_text)

        if len(combined_text) < 200:
            print(f"Unverifiable link detected (suspiciously short text, likely skeleton page): {url}", file=sys.stderr)
            return None, "MANUAL_CHECK_REQUIRED"

        dead_link_keywords = [
            "job not found",
            "position has been closed",
            "page you're looking for doesn't exist",
            "the job you are looking for does not exist",
            "this job is no longer available",
            "this job has expired"
        ]
        text_lower = combined_text.lower()
        if any(keyword in text_lower for keyword in dead_link_keywords):
            print(f"Dead link detected (keyword match): {url}", file=sys.stderr)
            return None, "DEAD_LINK"

        # Update text to pass into Gemini Prompt
        text = combined_text

    except requests.exceptions.Timeout as e:
        print(f"Timeout scraping {url}: {e}", file=sys.stderr)
        return None, "TIMEOUT"
    except Exception as e:
        print(f"Error scraping {url}: {e}", file=sys.stderr)
        return None, "OTHER"

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
      "post_date": "{date.today().isoformat()}",
      "needs_manual_check": false,
      "last_manual_check": ""
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

        - Regional Mapping logic (Assign all that apply, comma-separated):
        - If "Remote (US)", "Nationwide", "United States", "Americas", or "Global Remote": Map to 'US-All'.
        - East Coast & DMV (VA, DC, MD, NYC, NY, Boston, MA, PA, NC, NJ, SC, FL, GA, OH, CT, ME, DMV, Washington DC, Washington, DC, Washington, D.C., D.C.): Map to 'US-East'.
        - West Coast & PNW (WA, Seattle, Portland, OR, CA, SF, LA, San Francisco, UT, NV, AZ, CO, HI, PNW, Bay Area, SOCAL, Sunnyvale, Santa Clara, Draper, Costa Mesa, Mountain View, Burbank): Map to 'US-West'. Note: "Washington" means 'US-West' unless it says "Washington, DC", "Washington, D.C.", "Washington DC", or "D.C." ('US-East').
        - Midwest & South-Central (TX, Austin, Dallas, Houston, IL, Chicago, MN, TN, AL, MO, NE, ND, WI, MI, TOLA, Midwest): Map to 'US-Central'.
        - Europe, Middle East, Africa (Europe, UK, Germany, London, Berlin, Tel Aviv, Prague, Czechia, Switzerland, Zurich, Poland, Ireland, Scotland, Wales, Austria, Luxembourg, Saudi Arabia, Bratislava, DACH, EMEA): Map to 'EMEA'.
        - Asia/Pacific (India, Bangalore, Tokyo, Singapore, Sydney, Australia, Japan, Philippines, Manila, APAC, ANZ): Map to 'APAC'.
        - Latin America (São Paulo, Mexico, Bogotá, Buenos Aires, Queretaro, Monterrey, Guadalajara, LATAM): Map to 'LATAM'.
        - Canada (Canada, ON, Ontario, Toronto, Ottawa, Vancouver): Map to 'Canada'.

    Job Text: {text}
    """
    
    models_to_try = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash-lite"
    ]

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    max_retries = 3
    base_delay = 2
    
    for model_index, model in enumerate(models_to_try):
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

        for attempt in range(max_retries):
            try:
                response = requests.post(endpoint, json=payload, timeout=60)

                if response.status_code == 200:
                    content = response.json()['candidates'][0]['content']['parts'][0]['text']
                    json_text = content.replace('```json', '').replace('```', '').strip()
                    try:
                        return json.loads(json_text), None
                    except json.JSONDecodeError as e:
                        print(f"JSON Decode Error for {url} with model {model}: {e}\nResponse text: {json_text}", file=sys.stderr)
                        # JSON decode error is usually due to bad formatting, retrying same model might not help but different model might.
                        break # Break inner loop, try next model
                elif response.status_code in [429, 500, 502, 503, 504]:
                    print(f"API Error for {url} with model {model}: Status {response.status_code} on attempt {attempt + 1}/{max_retries}", file=sys.stderr)
                    if response.status_code in [429, 503]:
                        log_api_error(response.status_code)

                    if response.status_code == 429:
                        # If we hit a rate limit, don't keep hammering the same model. Break to try next model immediately.
                        break
                else:
                    print(f"API Error for {url} with model {model}: {response.text}", file=sys.stderr)
                    # Other API errors, might be model specific, let's try next model
                    break

            except requests.exceptions.Timeout as e:
                print(f"Timeout Exception for {url} with model {model}: {e} on attempt {attempt + 1}/{max_retries}", file=sys.stderr)
                # Will retry on next iteration
            except requests.exceptions.RequestException as e:
                print(f"Request Exception for {url} with model {model}: {e} on attempt {attempt + 1}/{max_retries}", file=sys.stderr)

            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"Retrying {url} in {delay} seconds...", file=sys.stderr)
                time.sleep(delay)
            else:
                # Max retries reached for this model
                pass

        print(f"Failed to process {url} with model {model} after {max_retries} attempts.", file=sys.stderr)

    print(f"Failed to process {url} after trying all fallback models.", file=sys.stderr)
    return None, "API_ERROR"

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    input_data = sys.argv[1]
    urls = [line.strip() for line in input_data.splitlines() if line.strip().startswith('http')]
    
    db_file = 'jobs.json'
    try:
        with open(db_file, 'r') as f:
            jobs = json.load(f)
    except FileNotFoundError:
        jobs = []

    failed_categories = {
        "DUPLICATE": [],
        "DEAD_LINK": [],
        "TIMEOUT": [],
        "API_ERROR": [],
        "JSON_ERROR": [],
        "MANUAL_CHECK_REQUIRED": [],
        "OTHER": [],
        "SHELVED": []
    }

    existing_urls = {job.get('url') for job in jobs if job.get('url')}
    
    success_count = 0
    consecutive_api_errors = 0
    MAX_CONSECUTIVE_ERRORS = 3

    for index, url in enumerate(urls):
        print(f"[*] Processing: {url}")

        if consecutive_api_errors >= MAX_CONSECUTIVE_ERRORS:
            print(f"[-] Aborting batch due to multiple consecutive API errors. Shelving: {url}")
            failed_categories["SHELVED"].append(url)
            continue

        if url in existing_urls:
            print(f"[-] Duplicate found, skipping: {url}")
            failed_categories["DUPLICATE"].append(url)
            continue

        new_job, error_reason = parse_job_with_gemini(url)
        if new_job:
            # Explicitly enforce new fields to handle potential Gemini hallucination
            new_job['needs_manual_check'] = False
            new_job['last_manual_check'] = ""

            jobs.append(new_job)
            existing_urls.add(new_job['url'])
            success_count += 1
            consecutive_api_errors = 0 # reset on success
            print(f"[+] Successfully added: {new_job['title']}")
        else:
            reason = error_reason if error_reason in failed_categories else "OTHER"
            failed_categories[reason].append(url)
            if reason == "API_ERROR":
                consecutive_api_errors += 1
            else:
                consecutive_api_errors = 0

    # Save the full updated list
    with open(db_file, 'w') as f:
        json.dump(jobs, f, indent=2)
    
    # Print failure blocks for the GitHub Action to capture
    for category, f_urls in failed_categories.items():
        if f_urls:
            print(f"\n{category}_URLS_START")
            for f_url in f_urls:
                print(f_url)
            print(f"{category}_URLS_END")

    total_failures = sum(len(v) for v in failed_categories.values())
    print(f"[*] Batch processing complete. Added: {success_count}, Failed: {total_failures}")

    update_badges()

if __name__ == "__main__":
    main()