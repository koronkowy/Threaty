import json
import requests
from datetime import date
from bs4 import BeautifulSoup

# Add phrases that indicate a temporary outage, not a permanent closure
TEMPORARY_OUTAGE_KEYWORDS = ["maintenance", "scheduled-downtime", "temporary"]

def check_link(job_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(job_url, headers=headers, allow_redirects=True, timeout=10)
        
        # 1. Check for temporary maintenance
        soup = BeautifulSoup(response.content, 'html.parser')
        body_text = soup.get_text().lower()
        if any(keyword in body_text for keyword in TEMPORARY_OUTAGE_KEYWORDS):
            return "skip" # Signal to skip this check and leave status as is
        
        # 2. Check for 404 or generic redirects (same as before)
        if response.status_code == 404:
            return False
            
        # Add your canonical redirect check here...
        return True
    except:
        return False

with open('jobs.json', 'r+') as f:
    jobs = json.load(f)
    today = date.today().isoformat()
    
    for job in jobs:
        if job.get('status') == 'expired':
            continue
            
        # Check Deadline
        if job.get('deadline') and job['deadline'] < today:
            job['status'] = 'expired'
            job['deadline'] = 'Expired' # Updating the field as requested
            print(f"Marking {job['title']} as expired (Deadline passed).")
            continue
            
        # Check Link Health
        health = check_link(job['url'])
        if health == "skip":
            print(f"Skipping {job['title']} due to temporary maintenance.")
            continue
        elif health == False:
            job['status'] = 'expired'
            print(f"Marking {job['title']} as expired (Link dead).")
            
    f.seek(0)
    json.dump(jobs, f, indent=2)
    f.truncate()