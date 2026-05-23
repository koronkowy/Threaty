# 🛡️ Threaty: The High-Signal Threat Intel Job Board

**Threaty** is a curated minimalist job board designed to filter out general engineering noise. It isolate roles specifically within **Cyber Threat Intelligence (CTI), Detection Engineering, Incident Response (IR), and Security Automation.**

By surfacing region constraints, work models, and dynamic recency metrics directly in the dashboard, Threaty helps you identify roles that match your specific geographic and authorization requirements instantly.

---

## 📥 How to Submit a Position

To add a new role to the board, follow these three simple steps:

1. **Open an Issue:** Navigate to the [GitHub Issues](https://github.com/koronkowy/Threaty/issues) tab and click "New issue." *Note: You can title the issue anything you want; it does not affect the submission.*
2. **Paste & Label:** Paste the direct URL of the job posting into the issue body. **Crucial:** Add the `job-submission` label to the issue so the automated pipeline detects it.
3. **Review & Merge:** Our background "Data Clerk" will automatically scrape the listing and create a Pull Request. The team will receive a notification to review the generated JSON. Once we approve the changes, the role will be merged and appear live on the board.

> **Note:** Please submit only active job postings. Submitting non-job URLs or "junk" data may result in submission privileges being revoked.

---

## 🛠️ The Architecture

Threaty is built to be lightning-fast, cost-free, and easy to maintain.

* **Frontend:** A high-density, text-first dashboard built with Vanilla JavaScript and CSS.
* **Database:** A flat, structured `jobs.json` file—serving as the "Source of Truth."
* **Hosting & Automation:** Threaty is fully hosted on **GitHub Pages**, providing instantaneous, zero-cost delivery. Backend tasks—including scraping, data parsing via Gemini AI, and deduplication—are managed entirely through automated **GitHub Actions**.

---

## 🛡️ About Threaty / Purpose

Threaty is a curated job board built to filter out general engineering noise. We isolate high-signal positions focused on **Cyber Threat Intelligence (CTI), Detection Engineering, Incident Response (IR), and Security Automation.** By surfacing region constraints directly in the dashboard, we help you identify roles that match your specific geographic and authorization requirements instantly.

**Created by [Lacey Kasten](https://laceykasten.com/).**

**Powered by:** GitHub Actions, Gemini AI (Data Clerk), & Vanilla JavaScript.

*Threaty is an open-source project. Follow the project or contribute on [GitHub](https://github.com/koronkowy/Threaty).*

---

*Built for the community. High signal, low noise.*
