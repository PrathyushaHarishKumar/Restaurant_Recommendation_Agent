# PROJECT STRUCTURE — Restaurant AI Agent
## SENG 691 HW3 | UMBC | Goal-Based + Utility-Based AI Agent

> This document is a complete map of every file in this project.

---

## 📁 Directory Tree

```
restaurant_agent/
│
├── README.md                          ← Start here. Quickstart + instructions
├── PROJECT_STRUCTURE.md               ← This file. Full context for AI agents
├── requirements.txt                   ← Python dependencies (3 packages)
├── .env.example                       ← Environment variable template
│
├── agent/
│   ├── restaurant_agent.py            ← CORE: Full AI agent logic
│   └── server.py                      ← Web server (Flask REST API)
│
├── data/
│   └── restaurants.csv                ← 50-restaurant database
│
├── static/
│   └── index.html                     ← Single-file web UI (HTML+CSS+JS)
│
└── docs/
    └── SENG691_HW3_Documentation.docx ← Architecture writeup for submission
```

---

## 📄 File-by-File Reference

---

### `/README.md`
- **Purpose:** Main entry point. Quickstart guide, example queries, troubleshooting, API docs.
- **When to use:** Send this to a human who wants to run the project.
- **AI prompt tip:** "Read README.md and tell me how to deploy this to Heroku."

---

### `/requirements.txt`
- **Purpose:** Lists all Python packages needed to run the project.
- **Contents:**
  ```
  flask==3.0.0
  flask-cors==4.0.0
  pandas==2.1.0
  ```
- **Install command:** `pip install -r requirements.txt`
- **AI prompt tip:** "Update requirements.txt to add SQLAlchemy and a PostgreSQL adapter."

---

### `/.env.example`
- **Purpose:** Template for environment variables. Copy to `.env` before running.
- **Contents:**
  ```
  FLASK_PORT=5000
  FLASK_DEBUG=true
  CSV_PATH=data/restaurants.csv
  TOP_N_RESULTS=5
  ```
- **AI prompt tip:** "Add a YELP_API_KEY variable and wire it into the agent."

---

### `/agent/restaurant_agent.py`
- **Purpose:** The entire AI agent logic. This is the brain of the project.
- **Language:** Python 3.9+
- **Classes inside:**

  | Class | Role |
  |-------|------|
  | `AgentGoal` | Dataclass — stores parsed user intent (cuisine, location, price, time, etc.) |
  | `AgentState` | Dataclass — tracks pipeline progress and reasoning log entries |
  | `NLPQueryParser` | Parses raw text query → structured `AgentGoal` using regex + keyword dicts |
  | `RestaurantDatabase` | Loads `restaurants.csv`, type-coerces all fields |
  | `FilterEngine` | Applies hard constraints sequentially (CSP): cuisine → location → price → day → time |
  | `RankingEngine` | Scores each candidate 0–100 using a 5-dimension utility function |
  | `Explainer` | Generates per-restaurant natural language justifications |
  | `RestaurantAgent` | Main orchestrator — runs the full 5-phase pipeline |

- **Entry point:** `RestaurantAgent.run(query: str, top_n: int) -> dict`
- **Returns:**
  ```json
  {
    "query": "...",
    "goal": { "cuisine": "Turkish", "location": "Downtown Baltimore", ... },
    "results": [
      {
        "rank": 1,
        "name": "Cazbar",
        "utility_score": 85.7,
        "score_breakdown": { "rating": 36.0, "review_volume": 8.7, ... },
        "explanation": "✓ Cuisine: Turkish matches...\n✓ Price: $56 for two...",
        ...
      }
    ],
    "total_candidates_after_filter": 2,
    "elapsed_seconds": 0.003,
    "reasoning_log": [
      { "timestamp": "14:19:28.041", "action": "PERCEIVE", "detail": "..." },
      ...
    ]
  }
  ```
- **CLI usage:**
  ```bash
  python agent/restaurant_agent.py
  python agent/restaurant_agent.py "Find seafood in Harbor East under $120"
  ```
- **AI prompt tip:** "Add a new filter to restaurant_agent.py that filters by seating_options containing 'outdoor'."

---

### `/agent/server.py`
- **Purpose:** Flask REST API server. Wraps the agent as HTTP endpoints.
- **Language:** Python 3.9+, Flask 3.0
- **Endpoints:**

  | Method | Route | Body / Params | Response |
  |--------|-------|---------------|----------|
  | POST | `/api/query` | `{"query": "...", "top_n": 5}` | Full agent result JSON |
  | GET | `/api/restaurants` | — | All 50 restaurants as JSON |
  | GET | `/api/health` | — | `{"status": "ok", "restaurants_loaded": 50}` |
  | GET | `/` | — | Serves `static/index.html` |

- **Start command:** `python agent/server.py`
- **Default port:** 5000
- **CORS:** Enabled for all origins (development mode)
- **AI prompt tip:** "Add authentication to server.py using an API key header."
- **AI prompt tip:** "Dockerize server.py so it runs in a container."

---

### `/data/restaurants.csv`
- **Purpose:** The agent's knowledge base. 50 restaurants across Baltimore + region.
- **Format:** CSV with header row
- **Row count:** 50 restaurants + 1 header = 51 lines
- **Encoding:** UTF-8

- **Column schema:**

  | Column | Type | Example | Notes |
  |--------|------|---------|-------|
  | `id` | int | `1` | Unique row ID |
  | `name` | string | `Cazbar` | Restaurant name |
  | `cuisine` | string | `Turkish` | Cuisine type |
  | `location` | string | `Downtown Baltimore` | General area label |
  | `neighborhood` | string | `Downtown` | Fine-grained neighborhood |
  | `city` | string | `Baltimore` | City name |
  | `state` | string | `MD` | State abbreviation |
  | `address` | string | `316 N Charles St` | Street address |
  | `price_per_person` | float | `28` | Estimated per-person cost in USD |
  | `total_for_two` | float | `56` | Estimated cost for 2 people in USD |
  | `rating` | float | `4.5` | Star rating (0.0–5.0) |
  | `reviews` | int | `892` | Number of reviews |
  | `open_thursday` | bool | `true` | Open on Thursdays |
  | `thursday_open_time` | string | `11:00` | Opening time (24h HH:MM) |
  | `thursday_close_time` | string | `23:00` | Closing time (24h HH:MM) |
  | `seating_options` | string | `indoor/outdoor` | Semicolon-separated list |
  | `views_available` | string | `street view;bar view` | Semicolon-separated list |
  | `accepts_reservations` | bool | `true` | Accepts reservations |
  | `reservation_required` | bool | `false` | Reservation mandatory |
  | `description` | string | `Authentic Turkish...` | Short description |
  | `phone` | string | `(410) 528-1222` | Phone number |
  | `website` | string | `cazbar.com` | Website domain |

- **To add restaurants:** Append rows following the same schema. No code changes needed.
- **AI prompt tip:** "Add 20 more Washington DC restaurants to restaurants.csv with the same schema."
- **AI prompt tip:** "Connect restaurants.csv to a real Yelp API call to keep data fresh."

---

### `/static/index.html`
- **Purpose:** Complete single-file web UI. No build step, no npm, no framework.
- **Language:** HTML5 + CSS3 + Vanilla JavaScript (ES6)
- **What it does:**
  - Text area for entering natural language queries
  - 5 preset example queries (one-click)
  - Calls `POST /api/query` and renders results
  - Shows parsed goal state as colored chips
  - Restaurant cards with utility score, score bars, price, rating, views
  - Expandable "Why this matches" explanation per card
  - Collapsible agent reasoning log panel at the bottom
- **External dependencies:** Google Fonts only (Playfair Display, DM Sans, DM Mono)
- **API it calls:** `POST /api/query` on the same origin (Flask server must be running)
- **AI prompt tip:** "Add a results filter sidebar to index.html to filter by cuisine after results load."
- **AI prompt tip:** "Deploy index.html to GitHub Pages and point the API calls to a hosted Flask server."

---

### `/docs/SENG691_HW3_Documentation.docx`
- **Purpose:** Formal architecture writeup for SENG 691 HW3 submission.
- **Contents:** PEAS description, agent type, pipeline phases, component descriptions, states/actions/goals, installation instructions, sample output, resume bullet, tech stack table.
- **Format:** Microsoft Word (.docx)
- **AI prompt tip:** "Summarize the architecture section of this docx in 3 bullet points."

---

## 🔁 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        USER                                  │
│  "Find a Turkish restaurant in Downtown Baltimore..."        │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP POST /api/query
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  server.py  (Flask)                                          │
│  • Receives JSON body: { "query": "...", "top_n": 5 }       │
│  • Calls agent.run(query, top_n)                             │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  restaurant_agent.py  (RestaurantAgent.run)                  │
│                                                              │
│  [1] NLPQueryParser.parse(query)                             │
│       └─► AgentGoal { cuisine, location, price, time... }   │
│                                                              │
│  [2] RestaurantDatabase.all()                                │
│       └─► List of 50 restaurant dicts from CSV              │
│                                                              │
│  [3] FilterEngine.apply(restaurants, goal)                   │
│       └─► cuisine match → location → price → day → time     │
│       └─► If 0 results: relax location, retry               │
│                                                              │
│  [4] RankingEngine.score(candidates, goal)                   │
│       └─► utility = rating + reviews + price + view + res   │
│       └─► Sort descending by score                           │
│                                                              │
│  [5] Explainer.explain(restaurant, goal) × top_n            │
│       └─► Per-criterion natural language justification       │
│                                                              │
│  Returns: { results, goal, reasoning_log, elapsed_seconds } │
└────────────────────────────┬────────────────────────────────┘
                             │ JSON response
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  static/index.html  (Browser)                                │
│  • Renders ranked cards with scores + explanations          │
│  • Shows reasoning log panel                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Deployment Options

### Local (default)
```bash
pip install -r requirements.txt
python agent/server.py
# → http://localhost:5000
```

### Docker
```dockerfile
# Ask an AI: "Write a Dockerfile for this Flask project"
# Key info: Python 3.11, port 5000, entry point: python agent/server.py
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "agent/server.py"]
```
```bash
docker build -t restaurant-agent .
docker run -p 5000:5000 restaurant-agent
```

### Render / Railway / Fly.io (free hosting)
- Set start command: `python agent/server.py`
- Set port: `5000`
- No environment variables required (uses bundled CSV)

### Heroku
```bash
# Ask an AI: "Create a Procfile and runtime.txt for this Flask project"
# Procfile:      web: python agent/server.py
# runtime.txt:   python-3.11.0
```

---

## 🔌 Extension Points (ask an AI to build these)

| Feature | Prompt to give an AI |
|---------|---------------------|
| Real Yelp API | "Replace RestaurantDatabase in restaurant_agent.py with a live Yelp Fusion API call" |
| LangChain integration | "Wrap RestaurantAgent in a LangChain Tool so it can be called by a ReAct agent" |
| OpenAI NLP | "Replace NLPQueryParser with an OpenAI function-calling parse step" |
| PostgreSQL | "Replace restaurants.csv with a PostgreSQL table using SQLAlchemy" |
| Docker deploy | "Write a Dockerfile and docker-compose.yml for this project" |
| Auth | "Add API key authentication to server.py" |
| More cities | "Add 50 restaurants in Washington DC to restaurants.csv with the same schema" |
| Streamlit UI | "Rewrite static/index.html as a Streamlit app that calls the same /api/query endpoint" |

---

## ⚙️ Environment Variables (all optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_PORT` | `5000` | Port for Flask server |
| `FLASK_DEBUG` | `true` | Enable debug mode |
| `CSV_PATH` | `data/restaurants.csv` | Path to restaurant database |
| `TOP_N_RESULTS` | `5` | Default number of results to return |

---

## 🧪 Quick Sanity Tests

```bash
# Test 1: CLI runs without error
python agent/restaurant_agent.py
# Expected: 2 Turkish restaurants ranked, reasoning log printed

# Test 2: Server starts
python agent/server.py &
sleep 2

# Test 3: Health check
curl http://localhost:5000/api/health
# Expected: {"restaurants_loaded": 50, "status": "ok"}

# Test 4: Query API
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Turkish restaurant in Baltimore under $65", "top_n": 3}'
# Expected: JSON with results array, Cazbar ranked #1
```

---
