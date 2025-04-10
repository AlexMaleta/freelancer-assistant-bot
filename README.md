# 🤖 Freelancer Assistant Bot

A personal Telegram assistant for freelancers — manage your projects, clients, deadlines, and tasks right from Telegram.

---

## 🚀 Features

- Create and manage freelance orders
- Link and track clients
- Break work into stages and checklists
- Receive reminders via Telegram and Email
- Inline buttons for quick interactions
- Multilingual interface (i18n-ready)

---

## 🧰 Tech Stack

- **Python 3.11+**
- [aiogram 3.x](https://docs.aiogram.dev/)
- SQLite (optional: PostgreSQL)
- Pydantic models
- FSM (finite state machine)
- APScheduler for reminders
- Layered architecture: `bot/`, `core/`, `database/`, `scheduler/`

---

## 📦 Installation

1. **Clone the repository**
```bash
git https://github.com/AlexMaleta/freelancer-assistant-bot.git 
cd freelancer-assistant-bot
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
Create `.env` file based on `.env.example`

```
BOT_TOKEN=your_telegram_token
ADMIN_ID=your_id
```

---

## ▶️ Run the bot

```bash
python main.py
```

Scheduler, database setup, and bot interface will start automatically.

---

## 📄 Bot Commands

- `/start` — Show main menu
- `/new_order` — Create a new order
- `/my_orders` — View your orders
- `/clients` — Manage your clients
- `/order <id>` — View specific order
- `/checklist <id>` — View checklist

---

## 🔧 Folder Structure

```
├── bot/            # Telegram interface
├── core/           # Business logic
├── database/       # DB models & queries
├── scheduler/      # Notifications logic
├── models/         # Pydantic data models
├── config/         # App settings
├── utils/          # Reusable helpers
├── main.py         # Entry point
```

---

## 📌 Roadmap Ideas

- Web dashboard (FastAPI + React)
- Finance tracking & analytics
- Google Calendar sync
- Team collaboration mode

---

## 📃 License

MIT — use freely, with love ❤️
