import json
import requests
import os
import datetime
from datetime import date
from bs4 import BeautifulSoup
from error_tracker import update_badges

# Add phrases that indicate a temporary outage, not a permanent closure
TEMPORARY_OUTAGE_KEYWORDS = ["maintenance", "scheduled-downtime", "temporary"]

def check_link(job_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(job_url, headers=headers, allow_redirects=True, timeout=10)
        
        # 1. Check for 404 or generic redirects
        if response.status_code in [404, 410]:
            return False

        soup = BeautifulSoup(response.content, 'html.parser')
        body_text = soup.get_text().lower()

        # 2. Check for temporary maintenance
        if any(keyword in body_text for keyword in TEMPORARY_OUTAGE_KEYWORDS):
            return "skip" # Signal to skip this check and leave status as is
        
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

        # 3. Check for suspiciously short text (skeleton pages)
        text = soup.get_text(separator=' ', strip=True)[:15000]
        combined_text = text + " " + " ".join(extra_text)

        if len(combined_text) < 200:
            return "manual_check_required"

        # 4. Check for dead link keywords
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
            return False

        # Add your canonical redirect check here...
        return True
    except Exception as e:
        print(f"Exception checking {job_url}: {e}")
        return "manual_check_required"

def create_github_issue(jobs_to_review):
    if not jobs_to_review:
        return

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not found, skipping issue creation.")
        return

    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo:
        print("GITHUB_REPOSITORY not found, skipping issue creation.")
        return

    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    body = "The following jobs require a manual health check because they could not be verified automatically:\n\n"
    for job in jobs_to_review:
        body += f"- [{job.get('title')} at {job.get('company')}]({job.get('url')})\n"

    data = {
        "title": "Manual Health Check Required",
        "body": body,
        "labels": ["health-check"]
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print("Successfully created GitHub issue for manual review.")
        today = date.today().isoformat()
        for job in jobs_to_review:
            job['last_manual_check'] = today
    else:
        print(f"Failed to create GitHub issue: {response.status_code} - {response.text}")

with open('jobs.json', 'r+') as f:
    jobs = json.load(f)
    today = date.today().isoformat()
    
    jobs_needing_review_today = []

    for job in jobs:
        if job.get('status') == 'expired':
            continue
            
        # Check Deadline
        if job.get('deadline') and job['deadline'] < today:
            job['status'] = 'expired'
            job['deadline'] = 'Expired' # Updating the field as requested
            print(f"Marking {job['title']} as expired (Deadline passed).")
            job['needs_manual_check'] = False
            continue
            
        # Check Link Health
        health = check_link(job['url'])
        if health == "skip":
            print(f"Skipping {job['title']} due to temporary maintenance.")
            continue
        elif health == True:
            job['needs_manual_check'] = False
        elif health == "manual_check_required":
            job['needs_manual_check'] = True
            print(f"Marking {job['title']} as needing manual check.")
        elif health == False:
            job['status'] = 'expired'
            job['needs_manual_check'] = False
            print(f"Marking {job['title']} as expired (Link dead).")

        # If it needs manual check, gather it if it hasn't been checked recently
        if job.get('needs_manual_check'):
            last_check = job.get('last_manual_check')
            # If never checked, or checked more than 6 days ago (to be safe if it runs a bit early)
            if not last_check:
                jobs_needing_review_today.append(job)
            else:
                try:
                    last_check_date = date.fromisoformat(last_check)
                    if (date.today() - last_check_date).days >= 6:
                        jobs_needing_review_today.append(job)
                except ValueError:
                    jobs_needing_review_today.append(job)

    # If today is Monday, create issue
    if datetime.datetime.today().weekday() == 0 and jobs_needing_review_today:
        print(f"It's Monday. Creating issue for {len(jobs_needing_review_today)} jobs.")
        create_github_issue(jobs_needing_review_today)
            
    f.seek(0)
    json.dump(jobs, f, indent=2)
    f.truncate()

# Update error tracking badges so they decay after 24h
update_badges()
