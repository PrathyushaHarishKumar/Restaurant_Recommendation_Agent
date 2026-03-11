# 🍽️ Restaurant AI Agent
### SENG 691 — AI Agent Computing | HW3 | UMBC

> A **Goal-Based + Utility-Based AI Agent** that takes natural language restaurant queries, applies NLP parsing, constraint filtering (CSP), utility scoring, and returns ranked recommendations with explanations — served through a REST API and a web UI.

---

## 📁 Project Structure

```
restaurant_agent/
├── agent/
│   ├── restaurant_agent.py   ← Core AI agent (NLP + filter + rank + explain)
│   └── server.py             ← Flask web server (REST API)
├── data/
│   └── restaurants.csv       ← 50-restaurant database
├── static/
│   └── index.html            ← Web UI (no build step needed)
├── docs/
│   └── SENG691_HW3_Documentation.docx
├── requirements.txt
└── README.md
```

---

## ⚡ Quickstart (5 Minutes)

### Step 1 — Check Python is installed
Open your terminal (Mac/Linux) or Command Prompt (Windows) and run:
```bash
python --version
```
You should see `Python 3.9` or higher. If not, download it from https://python.org/downloads

---

### Step 2 — Navigate to the project folder
```bash
cd path/to/restaurant_agent
```
> **Example on Mac/Linux:** `cd ~/Downloads/restaurant_agent`  
> **Example on Windows:** `cd C:\Users\YourName\Downloads\restaurant_agent`

---

### Step 3 — Install dependencies
```bash
pip install flask flask-cors pandas
```
This installs the 3 packages needed. Should take under 30 seconds.

> If `pip` doesn't work, try `pip3` instead.

---

### Step 4 — Choose how to run it

#### Option A: Web UI (Recommended — best for demos)
```bash
python agent/server.py
```
Then open your browser and go to:
```
http://localhost:5000
```
You'll see the full web interface. Type any query in the box and click **Run Agent**.

---

#### Option B: Command Line (Best for showing output in terminal)
```bash
python agent/restaurant_agent.py
```
This runs the **exact HW3 scenario** by default:
> *"Find a Turkish restaurant in Downtown Baltimore for two under $65 on Thursday at 7:30pm with a window view of the garden or street."*

To run a custom query:
```bash
python agent/restaurant_agent.py "Find a seafood restaurant in Harbor East with waterfront views for two under $120"
```

---

## 🗣️ Example Queries to Try

These all work out of the box with the 50-restaurant database:

| Query | What it tests |
|-------|--------------|
| `Find a Turkish restaurant in Downtown Baltimore for two under $65 on Thursday at 7:30pm with a window view` | HW3 exact scenario |
| `Seafood restaurant in Harbor East with waterfront views under $120` | Cuisine + location + views |
| `Italian restaurant in Fells Point with garden view under $100` | Neighborhood + seating |
| `Best rated restaurant in downtown Baltimore with harbor view` | Rating-focused |
| `Afghan restaurant in Mt Vernon Baltimore` | Niche cuisine search |
| `Japanese sushi restaurant for date night under $150 with reservations` | Time + reservations |
| `Vegetarian friendly restaurant in Hampden Baltimore` | Diet preference |
| `Greek restaurant in Greektown Baltimore` | Ethnic neighborhood match |

---

## 🧠 How the Agent Works

The agent follows a **5-phase deterministic pipeline**:

```
User Query (text)
       ↓
  [1] PERCEIVE   — NLP extracts: cuisine, location, price, day, time, seating, views
       ↓
  [2] GOAL SET   — Structured AgentGoal object created (like a search state)
       ↓
  [3] SEARCH     — All 50 restaurants loaded as candidate set
       ↓
  [4] FILTER     — Hard constraints applied (CSP): cuisine → location → price → day → time
       ↓
  [5] RANK       — Utility score computed (0–100): rating + reviews + price match + view + reservations
       ↓
  Ranked Results + Natural Language Explanations + Reasoning Log
```

### Utility Score Breakdown (100 pts total)
| Dimension | Max Points | How |
|-----------|-----------|-----|
| Rating | 40 | (rating / 5.0) × 40 |
| Review Volume | 15 | log scale credibility |
| Price Efficiency | 20 | how far under budget |
| View Match | 15 | matched preferred views |
| Reservations | 10 | bonus if reservations available |

---

## 🌐 Web API Endpoints

Once the Flask server is running (`python agent/server.py`):

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/query` | Run a natural language query |
| `GET` | `/api/restaurants` | List all 50 restaurants |
| `GET` | `/api/health` | Health check |

### Example API call (curl):
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Turkish restaurant in Downtown Baltimore under $65", "top_n": 3}'
```

### Example API call (Python):
```python
import requests

response = requests.post("http://localhost:5000/api/query", json={
    "query": "Find a Turkish restaurant in Downtown Baltimore for two under $65 on Thursday",
    "top_n": 5
})
data = response.json()

for r in data["results"]:
    print(f"#{r['rank']} {r['name']} — Score: {r['utility_score']}/100")
```

---

## 📊 Restaurant Database

The CSV at `data/restaurants.csv` has **50 restaurants** with these fields:

```
id, name, cuisine, location, neighborhood, city, state, address,
price_per_person, total_for_two, rating, reviews,
open_thursday, thursday_open_time, thursday_close_time,
seating_options, views_available, accepts_reservations, reservation_required,
description, phone, website
```

### Neighborhoods covered:
Downtown Baltimore · Harbor East · Fells Point · Canton · Mt Vernon  
Little Italy · Hampden · Federal Hill · Remington · Inner Harbor  
Greektown · Clipper Mill · Annapolis · Eastport · Eastern Shore

### Cuisines covered:
Turkish · Greek · Italian · Japanese · Mexican · Thai · Mediterranean  
Lebanese · Afghan · Spanish · American · Seafood · Steakhouse  
Latin American · Vegetarian/Vegan · Brunch · French

### To add more restaurants:
Just open `data/restaurants.csv` in Excel or any text editor and add rows following the same format. The agent will automatically pick them up next time you run it.

---

## 🔧 Troubleshooting

**"pip not found"**
```bash
python -m pip install flask flask-cors pandas
```

**"Port 5000 already in use"**
```bash
# Change the port in server.py, last line:
app.run(debug=True, port=5001)
# Then visit http://localhost:5001
```

**"No restaurants found" for a query**
- Check spelling of cuisine/neighborhood
- Try removing the price constraint
- Try a broader location (e.g., "Baltimore" instead of "Mt Vernon")

**Web UI shows "Agent Error"**
- Make sure the Flask server is running first: `python agent/server.py`
- Check the terminal for error messages

---



## 📚 Architecture 

| Term | This Project |
|------|-------------|
| Agent Type | Goal-Based + Utility-Based |
| PEAS: Performance | Constraint satisfaction precision + utility score |
| PEAS: Environment | 50-restaurant CSV database — static, fully observable |
| PEAS: Actuators | Ranked results with NL explanations |
| PEAS: Sensors | Natural language text query |
| State Representation | `AgentGoal` + `AgentState` dataclasses |
| Search Strategy | Sequential CSP filtering + utility ranking |
| NLP Approach | Regex-based rule entity extraction |
| Graceful Degradation | Auto-relaxes location if no results found |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Core | Python 3.9+ (stdlib only) |
| NLP | Regex + keyword dictionaries |
| Database | CSV + `csv.DictReader` |
| Web Server | Flask 3.0 + flask-cors |
| Web UI | HTML5 / CSS3 / Vanilla JS |

---


