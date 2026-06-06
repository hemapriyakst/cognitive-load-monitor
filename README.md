# 🧠 Cognitive Load Monitor for Developers

> A passive background tool that detects developer mental fatigue in real-time using keystroke dynamics and ML anomaly detection — and nudges you to take a break before burnout hits.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![ML](https://img.shields.io/badge/ML-Isolation%20Forest-green)
![Privacy](https://img.shields.io/badge/Privacy-No%20keys%20logged-red)
![Status](https://img.shields.io/badge/Status-Active%20Development-yellow)

---

## 🎯 Problem It Solves

Developers burn out silently. By the time you *feel* fatigued, your code quality has already degraded. This tool detects cognitive overload **before you notice it** — using only typing behavior metadata, never actual keystrokes.

---

## ⚙️ How It Works

```
Keystroke timing → Feature extraction (5-min windows) → Isolation Forest → Fatigue score → Alert
```

**Signals tracked (timing only — no keys stored):**
- Inter-key interval (IKI) mean & variance
- Words per minute (WPM)
- Backspace frequency ratio
- Typing burst patterns
- Idle gap frequency

---

## 🔐 Privacy First

- ❌ No actual keys are ever recorded
- ✅ Only timing metadata (milliseconds between keypresses)
- ✅ All data stays local on your machine (SQLite)
- ✅ Active app name only — no window titles or content

---

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/cognitive-load-monitor
cd cognitive-load-monitor

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py

# 5. Open dashboard
# Visit http://localhost:5000
```

---

## 📁 Project Structure

```
cognitive-load-monitor/
├── collector/          # Keystroke + system data capture
│   ├── keystroke_collector.py
│   └── database.py
├── features/           # Feature engineering (5-min windows)
│   └── extractor.py
├── model/              # Isolation Forest anomaly detection
│   └── detector.py
├── alerts/             # Desktop notification system
│   └── notifier.py
├── dashboard/          # Flask API + frontend
│   ├── backend/app.py
│   └── frontend/
├── data/               # SQLite DB (local, gitignored)
├── tests/
├── main.py             # Entry point
└── requirements.txt
```

---

## 📊 Dashboard Preview

*(Screenshot coming in Week 3)*

---

## 🗺️ Roadmap

- [x] Week 1 — Data collection engine + DB schema
- [ ] Week 2 — Feature extraction + Isolation Forest model
- [ ] Week 3 — Alert system + live dashboard
- [ ] Week 4 — Polish, packaging, demo video

---

## 🧪 Tech Stack

| Layer | Technology |
|---|---|
| Data capture | `pynput` |
| Storage | SQLite (local) |
| ML | `scikit-learn` Isolation Forest |
| Backend | Flask |
| Notifications | `plyer` |
| Scheduling | `schedule` |

---

## 👤 Author

Built during semester break as a portfolio project.
Reach me at: hemapriya.nkss@gmail.com
