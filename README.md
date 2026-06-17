<p align="center">
  <img src="assets/logo.png" width="140" alt="SUTRA Core logo" />
</p>

<h1 align="center">SUTRA Core</h1>

<p align="center">
  <strong>AI-Powered WhatsApp ERP for India's 63 Million MSMEs</strong><br />
  Voice. Text. Hinglish. Zero training. Runs on a ₹800/month VPS.
</p>

<p align="center">
  <a href="https://github.com/ravikumarve/sutra-core/stargazers">
    <img src="https://img.shields.io/github/stars/ravikumarve/sutra-core?style=social" alt="Stars" />
  </a>
  <a href="https://github.com/ravikumarve/sutra-core/forks">
    <img src="https://img.shields.io/github/forks/ravikumarve/sutra-core?style=social" alt="Forks" />
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/status-production--ready-brightgreen" alt="Status" />
  <img src="https://img.shields.io/badge/Deploy-Docker%20%7C%20systemd-lightgrey" alt="Deploy" />
  <a href="https://github.com/ravikumarve/sutra-core/actions">
    <img src="https://github.com/ravikumarve/sutra-core/actions/workflows/ci-cd.yml/badge.svg" alt="CI/CD" />
  </a>
  <a href="https://gumroad.com/l/sutra-core">
    <img src="https://img.shields.io/badge/Buy-Gumroad-FF90E8?logo=gumroad" alt="Gumroad" />
  </a>
</p>

---

> **SUTRA** *(Systematic Unstructured Text & Resource Allocator)* — a textile merchant in Surat sends a Hinglish voice note; SUTRA transcribes, checks stock, confirms the order, deducts inventory, generates a GST invoice, and sends it back via WhatsApp. No app. No login. No training.

---

## ✨ Features

| Capability | What It Does |
|------------|-------------|
| **🎙️ Voice-to-Order** | Hinglish voice notes → transcribed → structured order in <30s |
| **📦 Auto Inventory** | Stock deducted on confirmation. Restock alerts before stockout. |
| **💰 Udhaar (Credit) Mgmt** | Track credit limits, aging, auto-reminders on WhatsApp |
| **🧾 GST Invoicing** | PDF invoices generated and delivered in the same WhatsApp thread |
| **🏢 Multi-Tenant** | One deployment serves unlimited businesses with isolated data |
| **🔐 SOC 2 Ready** | AES-256 encryption, JWT auth, webhook security, RBAC |
| **🖥️ Owner Dashboard** | Analytics-only Next.js dashboard for month-end review |
| **📡 Monitoring** | Prometheus + Grafana stack. Alertmanager for critical events. |

---

## 🚀 Quick Start

```bash
git clone https://github.com/ravikumarve/sutra-core.git
cd sutra-core && cp .env.example .env   # configure your API keys
docker compose up --build                # starts FastAPI + Redis + PostgreSQL
```

That's it. Your webhook listener is live at `http://localhost:8000`. Configure it as your Meta WhatsApp webhook URL and start receiving orders.

📖 [Full deployment guide →](docs/PRODUCTION_DEPLOYMENT_EXECUTION_GUIDE.md)

---

## 🧠 How It Works

SUTRA is an **asynchronous multi-agent mesh**. Three specialized agents process every message through an event-driven pipeline:

```text
  WhatsApp ──► Webhook ──► Redis Queue ──► ┌─────────┐    ┌───────────┐
  (Voice/Text)            (Event Bus)        │ Liaison │───►│ Strategist│
                                             │ (Intent)│    │(Execution)│
                                             └─────────┘    └─────┬─────┘
                                                                  │
                                              ┌─────────┐         │
                                              │ Auditor │◄────────┘
                                              │(Ledger) │──► PDF Invoice
                                              └─────────┘    WhatsApp Reply
```

| Agent | Role | Integrations |
|-------|------|-------------|
| **Liaison** | Decode intent from raw text/audio | Whisper-Hinglish, Sentiment Analyzer |
| **Strategist** | Validate & execute against DB | Inventory, Credit Scoring, Pricing |
| **Auditor** | Immutable ledger + compliance | PDF Generator, GST Validator |

No agent calls another directly. All communication is through `AgentMessage` objects on Redis Streams — enabling independent scaling, restart, and replacement.

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python 3.12+) |
| **Database** | PostgreSQL 15 with schema-level multi-tenancy |
| **Queue** | Redis Streams (per-tenant namespaced) |
| **STT** | OpenAI Whisper (CPU, Hinglish post-processing) |
| **Dashboard** | Next.js 14 + shadcn/ui (analytics-only) |
| **Monitoring** | Prometheus + Grafana + Alertmanager |
| **CI/CD** | GitHub Actions (test → lint → security scan → deploy) |
| **Deployment** | Docker Compose / systemd |

---

## 📊 Architecture Decisions

| Decision | Why |
|----------|-----|
| **Headless (WhatsApp-first)** | Shop owners are on WhatsApp 8 hours/day. No app to install. Zero adoption friction. |
| **PostgreSQL over NoSQL** | Financial ledger requires ACID. Udhaar entries must be atomic with inventory. |
| **Redis Streams over Kafka** | Single VPS deployment. Kafka is overkill. Redis handles the throughput comfortably. |
| **CPU-only Whisper** | 30s async transcription latency is acceptable. No GPU = deployable anywhere. |

---

## 📈 Roadmap

| Feature | Status |
|---------|--------|
| Multi-agent pipeline (Liaison → Strategist → Auditor) | ✅ `v1.0.0` |
| Whisper-Hinglish NLP pipeline | ✅ `v1.0.0` |
| Multi-tenancy with isolated schemas | ✅ `v1.0.0` |
| GST-compliant PDF invoicing | ✅ `v1.0.0` |
| Docker + systemd deployment | ✅ `v1.0.0` |
| CI/CD + Monitoring stack | ✅ `v1.0.0` |
| Security audit (SOC 2 framework) | ✅ `v1.0.0` |
| Owner analytics dashboard | 🔄 In progress |
| Image-based order parsing (photo → SKU) | 📋 Planned `v1.1` |
| UPI payment link injection | 📋 Planned `v1.1` |
| Fine-tuned Whisper for 8 regional accents | 📋 Planned `v1.2` |

---

## 💰 Pricing Model

| Plan | Price | For |
|------|-------|-----|
| **Starter** | ₹499/month | 1 WhatsApp number, 500 orders/mo |
| **Growth** | ₹1,499/month | 3 numbers, 2K orders/mo, 3 users |
| **Business** | ₹4,999/month | Unlimited, dedicated support, custom integrations |

Self-hosted is **MIT licensed and free**. Paid plans include managed hosting, SLA, and priority support.

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Deployment Guide](docs/PRODUCTION_DEPLOYMENT_EXECUTION_GUIDE.md) | Step-by-step production setup |
| [Security Hardening](docs/PRODUCTION_SECURITY_HARDENING.md) | Production security measures |
| [Monitoring Setup](docs/PRODUCTION_MONITORING_SETUP.md) | Prometheus + Grafana guide |
| [Backup Procedures](docs/PRODUCTION_BACKUP_PROCEDURES.md) | Backup & disaster recovery |
| [Runbooks](docs/PRODUCTION_RUNBOOKS.md) | Operational runbooks |
| [Executive Summary](docs/EXECUTIVE_SUMMARY.md) | Business overview |

---

## 🤝 Contributing

We actively welcome contributions in these high-impact areas:

- **Dialect Maps** — Hinglish vocabulary, regional terms, unit aliases
- **Industry Presets** — New business-type configs (electronics, furniture, etc.)
- **Test Audio Fixtures** — Real Hinglish voice note transcriptions
- **Query Optimizations** — PostgreSQL performance with EXPLAIN ANALYZE

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

MIT — see [LICENSE](LICENSE).

Built for the bazaar. Runs in the background. Never misses a bill.

---

<p align="center">
  <img src="https://api.star-history.com/svg?repos=ravikumarve/sutra-core&type=Date" width="600" alt="Star History" />
</p>
