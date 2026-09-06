# 🎯 GTD Web App

A full-stack **Getting Things Done (GTD)** task management application built with
**Python (Flask)** and **PostgreSQL**, faithfully implementing David Allen's
*Mastering Workflow* — from capturing "stuff" to the Weekly Review.

Multi-user with admin controls, dark mode, and a clean gradient UI.

> **Author & Developer:** [Moosa Raja](https://github.com/moosaraja)

---

## ✨ Features

### 🔄 The Complete GTD Workflow

| Phase | Feature | What it does |
|-------|---------|--------------|
| **Collect** | 📥 Inbox | Capture anything that has your attention — get it out of your head |
| **Process** | ⚙️ Decision wizard | One item at a time: *"What is it? Is it actionable?"* |
| **Organize** | 📋 Projects & Lists | Next Actions, Calendar, Waiting For, Someday/Maybe, Reference, Trash |
| **Do** | 📍 Context filters | *"I'm at @home with 30 min — what can I do right now?"* |
| **Review** | 🔍 Weekly dashboard | Inbox status, overdue items, stuck projects, loose ends, waiting-for follow-ups |

### ⚙️ The Process Decision Tree

Every inbox item is processed one-at-a-time, exactly per the GTD flowchart:

                   ┌─ NO ──→ 🗑 Eliminate (Trash)
Is it actionable? ─────┤        ├─ ☁ Incubate (Someday/Maybe)
                       │        └─ 📁 Reference
                       │
                       └─ YES ─→ ⚡ Do it (< 2 min) ──→ Done
                                ├─ 🤝 Delegate it ──→ Waiting For (who?)
                                ├─ 📅 Defer it (specific day) ──→ Calendar
                                ├─ ➡ Defer it (anytime) ──→ Next Action (+ context)
                                └─ 📋 Multi-step? ──→ Project (outcome + first action)

### 👤 Multi-User System

- **Open registration** — new users get 6 default contexts auto-seeded (@office, @home, @computer, @phone, @errands, @anywhere)
- **Password hashing** — never stored in plain text (Werkzeug / PBKDF2)
- **Full data isolation** — every query is scoped to the logged-in user; users can never see or touch each other's items (even by guessing URLs)
- **Admin panel** — admins can:
  - ⛔ Deactivate / ✅ Reactivate accounts (instant logout for disabled users)
  - ▲ Promote / ▼ Demote admins
  - 🗑 Delete a user **and** all their data (with confirmation)
  - 🛡 Self-protection: you cannot deactivate/demote/delete yourself

### 🎨 UI Extras

- 🌙 **Dark mode** toggle with persistent preference (localStorage)
- ✏️ **Edit & move** any item between lists, change context/project/dates
- 🔥 Empty Trash (permanently delete, per user)
- Active-page highlighting in the navigation bar
- Gradient design system: login, register, and all inner pages

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask |
| Database | PostgreSQL |
| Templating | Jinja2 |
| Frontend | HTML5, CSS3, vanilla JavaScript |
| Security | Werkzeug password hashing, signed Flask sessions |
| Auth | Session-based with `before_request` login wall |

---

## 📁 Project Structure

gtd-app/
├── app.py                  # Flask app — all routes & business logic
├── db.py                   # PostgreSQL helpers (fetch_all / fetch_one / execute)
├── schema.sql              # Core tables: items, projects, contexts
├── schema_users.sql        # Multi-user upgrade: users table + user_id columns
├── create_admin.py         # One-time script: create the first admin account
├── requirements.txt        # Python dependencies
└── templates/
    ├── base.html           # Shared layout, nav bar, dark theme
    ├── login.html          # Standalone login page
    ├── register.html       # Standalone registration page
    ├── inbox.html          # Collect phase
    ├── process.html        # Process phase (decision tree)
    ├── list.html           # Generic list page (all statuses + context filter)
    ├── projects.html       # Projects with outcomes & actions
    ├── review.html         # Weekly review dashboard
    ├── edit.html           # Edit & move item form
    └── admin.html          # Admin user management



---

## 🗄 Database Schema

### Tables

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `users` | Accounts | username, password_hash, is_admin, is_active |
| `items` | Every piece of "stuff" | title, notes, **status**, project_id, context_id, due_date, due_time, delegated_to, user_id |
| `projects` | Multi-step outcomes | name, outcome, status (active/completed), user_id |
| `contexts` | @where/@how labels | name, user_id (unique per user) |

### Item Status Flow


inbox ──→ next_action ──→ done
  │          │
  │          ├── scheduled (Calendar, due_date)
  │          ├── waiting_for (delegated_to)
  │          ├── someday_maybe
  │          ├── reference
  │          └── trash ──→ (Empty Trash = permanent)
  └──→ (processed one at a time, never back in)


  
---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ running locally

### 1. Clone & set up environment

bash
git clone https://github.com/moosaraja/GTD.git
cd GTD
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt


### 2. Create the database

bash
psql -U postgres

sql
CREATE DATABASE gtd_app;
\c gtd_app
\i 'schema_final.sql'

### 3. Configure credentials

Set the database password as an environment variable (recommended):

bash
setx GTD_DB_PASSWORD "your-postgres-password"


> Close and reopen the terminal after `setx`.

### 4. Create the first admin

bash
python create_admin.py


### 5. Run

bash
python app.py

Open **http://127.0.0.1:955** — log in with your admin account. 🎉

---

## 📖 Usage (the GTD way)

1. **Collect** — dump everything into the Inbox as it comes to mind
2. **Process** — open the Process page daily; decide each item top-down, never back into the inbox
3. **Organize** — keep Next Actions contextual (@phone, @office), track delegated work in Waiting For
4. **Do** — filter lists by context, time, and energy
5. **Review** — run the Weekly Review dashboard: process inbox, plan stuck projects, chase Waiting For, clear loose ends

---

## 🔒 Security Notes

- Passwords are hashed (PBKDF2 via Werkzeug) — never stored or logged in plain text
- All data queries enforce ownership (`user_id`) server-side — including updates, deletes, and URL-accessed items
- DB credentials live in environment variables, not in source code
- Session cookies are signed with a secret key to prevent tampering

---

## 🔮 Roadmap

- [ ] Recurring tasks (weekly reviews, bills)
- [ ] Global search across all lists
- [ ] "Today" view (calendar + due next actions)
- [ ] Email-to-inbox capture
- [ ] REST API for mobile clients
- [ ] Per-user theme preference in DB

---

## 🙏 Acknowledgments

- Workflow based on *Getting Things Done* by **David Allen** — [gettingthingsdone.com](https://gettingthingsdone.com)
- Built as a hands-on full-stack learning project

---

## 👤 Author

**Moosa Raja** — a.k.a. [@moosaraja](https://github.com/moosaraja)

Designed, developed, and maintained the full application:
Flask backend, PostgreSQL schema, GTD workflow engine,
multi-user auth with admin controls, and the UI.


## 📄 License

MIT — feel free to use, learn, and adapt.


MIT License

Copyright (c) 2025 Moosa Raja

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

