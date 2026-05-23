<img width="1409" height="880" alt="Screenshot 2026-05-22 at 9 13 01 PM" src="https://github.com/user-attachments/assets/c065af82-eb51-40d1-8c33-2e9bd2bb832b" />

# 🛡️ Threaty: The High-Signal Threat Intel Job Board

**Threaty** is a curated minimalist job board designed to filter out general engineering noise. It isolate roles specifically within **Cyber Threat Intelligence (CTI), Detection Engineering, Incident Response (IR), and Security Automation.**

By surfacing region constraints, work models, and dynamic recency metrics directly in the dashboard, Threaty helps you identify roles that match your specific geographic and authorization requirements instantly.

**Created by [Lacey Kasten](https://laceykasten.com/).**

**Powered by:** GitHub Actions, Gemini AI (Data Clerk), & Vanilla JavaScript.

*Threaty is an open-source project. Follow the project or contribute on [GitHub](https://github.com/koronkowy/Threaty).*

---

## 📥 How to Submit a Position

To add a new role to the board, follow these three simple steps:

1. **Open an Issue:** Navigate to the [GitHub Issues](https://github.com/koronkowy/Threaty/issues) tab and click "New issue." *Note: You can title the issue anything you want; it does not affect the submission.*
2. **Paste & Label:** Paste the direct URL of the job posting into the issue body. **Crucial:** Add the `job-submission` label to the issue so the automated pipeline detects it.
3. **Review & Merge:** Our background "Data Clerk" will automatically scrape the listing and create a Pull Request. The team will receive a notification to review the generated JSON. Once we approve the changes, the role will be merged and appear live on the board.

> **Note:** Please submit only active job postings. Submitting non-job URLs or "junk" data may result in submission privileges being revoked.

---

## 🛠️ System Architecture & Workflow

Threaty utilizes GitHub’s native infrastructure for a zero-cost, high-performance pipeline.

### The Ingestion Flow

1. **Trigger:** A labeled GitHub Issue initiates a **GitHub Action** runner.
2. **Extraction:** A Python-based "Data Clerk" (`parser.py`) scrapes the URL and uses **Gemini AI** to extract structured metadata.
3. **Deduplication:** The script validates the URL against `jobs.json`. Duplicate URLs are rejected; new jobs are assigned a sequential ID.
4. **Human Gatekeeper:** A **Pull Request** is generated. This allows for manual verification of scope (CTI relevance), data accuracy, and final approval before hitting `main`.

---

## 🛡️ Security & Integrity

### Branch Protection (The Gatekeeper)

To ensure the integrity of our dataset, `main` is a protected branch.

* **Ruleset:** We utilize GitHub Branch Rulesets to enforce that no code can be merged without:
  * A successful pull request.
  * A manual review/approval (Human-in-the-Loop).
  * Passing status checks (the parser must succeed).
* **Force Push/Deletion:** Disabled to ensure history remains immutable and accidental deletions are impossible.

### Secret Management

Your **Gemini API Key** is never hardcoded. It is stored in **GitHub Repository Secrets** and injected into the workflow at runtime, ensuring complete security.

---

## 🗺️ Geographic & Regional Logic

Threaty implements a dual-layer mapping system to handle the inconsistency of job board listings.

| **Region**        | **Mapping Logic**       | **Examples**               |
| ----------------------- | ----------------------------- | -------------------------------- |
| **US-All**        | Nationwide remote roles       | US-based full remote             |
| **US-East / DMV** | Covers East Coast & DC Metro  | VA, DC, MD, NYC, Boston          |
| **US-West / PNW** | Covers West Coast & Tech Hubs | Seattle, Portland, SF, LA        |
| **EMEA / DACH**   | Covers Europe/UK/Middle East  | London, Berlin, Tel Aviv, Prague |
| **APAC**          | Covers Asia/Pacific           | Bangalore, Tokyo, Singapore      |

* **Logic:** When you search for "Seattle," the engine automatically expands the query to include `US-West` and `US-All` roles.
* **Satellite Hubs:** Our search dictionary maps commuter satellites (e.g., Redmond/Bellevue for Seattle; Reston/McLean for DMV) to their parent region automatically.

*Built for the community. High signal, low noise.*
