<img width="1409" height="880" alt="Screenshot 2026-05-22 at 9 13 01 PM" src="https://github.com/user-attachments/assets/c065af82-eb51-40d1-8c33-2e9bd2bb832b" />

# 🛡️ Threaty: The High-Signal Threat Intel Job Board

**Threaty** is a curated minimalist job board designed to filter out general engineering noise. It isolate roles specifically within **Cyber Threat Intelligence (CTI), Detection Engineering, Incident Response (IR), and Security Automation.**

By surfacing region constraints, work models, and dynamic recency metrics directly in the dashboard, Threaty helps you identify roles that match your specific geographic and authorization requirements instantly.

**Created by [Lacey Kasten](https://laceykasten.com/).**

**Powered by:** GitHub Actions, Gemini AI (Data Clerk), & Vanilla JavaScript.

*Threaty is an open-source project. Follow the project or contribute on [GitHub](https://github.com/koronkowy/Threaty).*

---
## 📥 How to Submit a Position

We welcome community contributions! To propose new roles for the board, follow these steps:

1. **Open an Issue:** Navigate to the GitHub Issues tab and click "New issue."
2. **Batch Your URLs:** Paste the direct URLs of the job postings into the issue body. (Please use *one URL per line* if submitting a batch).
3. **The Gatekeeper Review (Why the delay?):** To protect our backend API quotas from spam and ensure only high-signal Threat Intel roles make it to the board, **automation does not run immediately**. Once you submit your issue, a repository maintainer will manually review the links.
4. **Automation Trigger:** If the links fit our scope, the maintainer will manually apply the `job-submission` label. This label triggers our background "Data Clerk" to extract the job data and create a Pull Request.
5. **Live Deployment:** Once the generated data is merged by the maintainer, the roles will instantly appear live on the board.

> **Note:** Please submit only active job postings relevant to CTI, Detection Engineering, IR, or Security Automation. Submitting generic IT roles, non-job URLs, or "junk" data may result in submission privileges being revoked.

---

## 🛠️ System Architecture & Workflow

Threaty utilizes GitHub’s native infrastructure for a zero-cost, high-performance pipeline.

### The Ingestion Flow

1. **Trigger:** A labeled GitHub Issue initiates a **GitHub Action** runner.
2. **Extraction:** A Python-based "Data Clerk" (`parser.py`) scrapes the URL and uses **Gemini AI** to extract structured metadata.
3. **Deduplication:** The script validates the URL against `jobs.json`. Duplicate URLs are rejected; new jobs are assigned a sequential ID.
4. **Human Gatekeeper:** A **Pull Request** is generated. This allows for manual verification of scope (CTI relevance), data accuracy, and final approval before hitting `main`.

---

## 🤖 Automation: Daily Health Check

![Daily Health Check](https://github.com/koronkowy/Threaty/actions/workflows/health_check.yml/badge.svg)

To ensure the job board stays relevant, I’ve built an automated **Health Check** pipeline that runs daily to identify expired or broken job postings.

### How it works

The `health_check.py` script performs the following logic on every job in the database:

1. **Maintenance Awareness:** It scrapes page content for keywords (e.g., "maintenance," "scheduled-downtime"). If found, it skips the job, preventing false "expired" statuses during temporary outages.
2. **Deadline Verification:** Any job that has passed its `deadline` date is automatically flagged as `expired`.
3. **Link Integrity:** The script validates that the job URL is still a valid, unique posting. It detects:
   * **HTTP 404/410 Errors:** Confirmed broken links.
   * **Generic Redirects:** If a link redirects to a career portal homepage (instead of a specific job ID), it marks the listing as `expired`.
4. **Self-Healing:** Once a job is marked `expired`, the script updates the status in `jobs.json`, which automatically triggers the frontend to dim the listing and update the deadline display to "Expired".

### Automated Pipeline

This process is fully hands-free:

* **GitHub Actions:** A scheduled workflow runs the script every day at midnight (UTC).
* **Auto-Commit:** If any jobs are flagged as expired, the workflow automatically commits the changes to the `main` branch, keeping the live board updated without manual intervention.

---

## 🛡️ Security & Integrity

### Secret Management

Your **Gemini API Key** is never hardcoded. It is stored in **GitHub Repository Secrets** and injected into the workflow at runtime, ensuring complete security.

---

## 🗺️ Geographic & Regional Logic

| **Region**     | **Mapping Logic**                | **Examples / Hubs**                                                     |
| -------------------- | -------------------------------------- | ----------------------------------------------------------------------------- |
| **US-All**     | Nationwide remote roles                | US-based full remote; includes all regional hubs                              |
| **US-East**    | Covers East Coast & DC Metro (DMV)     | VA, DC, MD, NYC, Boston; includes DMV, Tri-State, Mid-Atlantic, NOVA          |
| **US-West**    | Covers West Coast & PNW                | Seattle, Portland, SF, LA; includes PNW, Mountain, Southwest, Bay Area, SOCAL |
| **US-Central** | Covers Midwest & South-Central & TOLA  | Austin, Chicago, Dallas, Houston; includes TOLA, Midwest                      |
| **EMEA**       | Covers Europe, UK, DACH, & Middle East | London, Berlin, Tel Aviv, Prague; includes DACH, Benelux, Gulf, Israel        |
| **APAC**       | Covers Asia/Pacific                    | Bangalore, India, Tokyo, Singapore, Sydney; includes ASEAN, ANZ               |
| **LATAM**      | Covers Latin America                   | São Paulo, Mexico City, Bogotá, Buenos Aires                                |

### Regional Logic Summary

* **Intelligent Expansion:** When you search for a specific hub (e.g., "Seattle"), the engine automatically expands the query to include the parent region (`US-West`) and nationwide remote roles (`US-All`).
* **Satellite Hub Normalization:** The search dictionary automatically maps commuter satellites (e.g., Redmond/Bellevue for Seattle; Reston/McLean for DMV) to their parent region, ensuring relevant roles are never missed due to localized naming.
* **Territory Alias Support:** The engine natively resolves industry shorthand. Typing territory codes like **TOLA**, **DMV**, **DACH**, **ANZ**, or **PNW** into the search bar instantly expands the query to include all associated cities, states, and regional authorization constraints.

---

*Built for the community. High signal, low noise.*
