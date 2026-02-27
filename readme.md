# FRAML — User & Transaction Relationship Visualization System

A graph-based system for visualizing relationships between user accounts using transaction data and shared attributes. Users and transactions are stored as nodes in a Neo4j graph database, relationships are detected automatically, and everything is explored through an interactive browser-based UI.

---

## Live Demo

| Service | URL |
|---|---|
| **Frontend Application** | https://framl-graph-35e3.vercel.app |
| **Backend API + Swagger Docs** | https://framl-graph-2l3l.onrender.com/docs |


---

## Tech Stack

| Layer | Technology |
|---|---|
| Graph Database | Neo4j Aura (cloud) |
| Backend | Python 3.10, FastAPI |
| Frontend | React 18, Vite, Vis.js |
| Containerization | Docker, Docker Compose |
| Hosting | Vercel (frontend), Render (backend) |
| Data Generation | Python, Faker (Indian locale) |

---

## Project Structure

```
framl-graph/
├── backend/
│   ├── database.py        # Neo4j driver + connection management
│   ├── Dockerfile
│   ├── main.py            # All REST API endpoints
│   ├── models.py          # Pydantic models for User and Transaction
│   ├── relationships.py   # Automatic relationship detection logic
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Complete React frontend
│   │   └── main.jsx       # Entry point
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── eslint.config.js
├── scripts/
│   └── seed_data.py       # Generates 510 users + 100,000 transactions
├── .gitignore
├── docker-compose.yml
└── readme.md
```

---

## Architecture

```
  User's Browser
       │
       ▼
  Vercel — React + Vite (Frontend)
       │  HTTPS REST calls
       ▼
  Render — FastAPI Backend (Python)
       │  Bolt over TLS (neo4j+s://)
       ▼
  Neo4j Aura — Graph Database (Cloud)
```

---

## Features

**Graph Visualization**
- Interactive Vis.js network graph with all node and relationship types
- Color-coded edges by relationship type
- Click any node to inspect its properties and connections

**Fraud Detection Patterns**
- Automatic detection of shared emails, phones, addresses, and payment methods across accounts
- Transaction clustering by shared IP address and device fingerprint
- Risk scoring on every transaction (0.0 – 1.0) with auto-flagging

**Transaction Intelligence**
- 100,000 synthetic INR transactions with realistic risk distribution
- Filter by status (clear / review / flagged), amount range, and date
- Sort by risk score, amount, or timestamp

**Relationship Explorer**
- Look up any user ID to see their full connection graph
- Look up any transaction to see linked users and related transactions
- Shortest path finder between any two users in the network

**Analytics & Export**
- Live dashboard stats — total users, transactions, flagged count
- Export users and transactions as CSV or JSON

---

## Graph Database Structure

### Node Types
- **User** — id, name, email, phone, address, payment_method
- **Transaction** — id, sender_id, receiver_id, amount, currency, timestamp, ip_address, device_id, status, risk_score

### Relationship Types

| Relationship | Between | Trigger |
|---|---|---|
| `INITIATED` | User → Transaction | User is the sender |
| `RECEIVED` | User → Transaction | User is the receiver |
| `SENT` | User → User | Direct money transfer |
| `SHARED_EMAIL` | User → User | Same email address |
| `SHARED_PHONE` | User → User | Same phone number |
| `SHARED_ADDRESS` | User → User | Same physical address |
| `SHARED_PAYMENT` | User → User | Same payment method |
| `SAME_IP` | Transaction → Transaction | Same IP address |
| `SAME_DEVICE` | Transaction → Transaction | Same device ID |

---

## API Reference

Full interactive docs: **https://framl-graph-2l3l.onrender.com/docs**

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/users` | Add or update a user |
| `GET` | `/users` | List users with search and pagination |
| `POST` | `/transactions` | Add or update a transaction |
| `GET` | `/transactions` | List transactions with filters and sorting |
| `GET` | `/relationships/user/:id` | All graph connections of a user |
| `GET` | `/relationships/transaction/:id` | All graph connections of a transaction |
| `GET` | `/analytics/stats` | Dashboard counts |
| `GET` | `/analytics/shortest-path` | Shortest path between two users |
| `GET` | `/export/users/csv` | Export all users as CSV |
| `GET` | `/export/transactions/csv` | Export all transactions as CSV |

---

## Graph Edge Color Legend

| Color | Relationship |
|---|---|
| Cyan | User ↔ Transaction (Initiated / Received) |
| Red | Shared Email |
| Pink | Shared Phone |
| Orange | Shared Address |
| Amber | Shared Payment Method |
| Purple | Same IP Address (TX → TX) |
| Violet | Same Device ID (TX → TX) |

---

## Seed Data

The `scripts/seed_data.py` script generates synthetic Indian financial data with intentional suspicious patterns for demonstration.

**510 Users** — Indian names, +91 phone numbers, city addresses, UPI/card payment methods. 30% share an email, 25% share a phone, 20% share an address or payment method.

**100,000 Transactions** — INR amounts from ₹500 to ₹50,00,000 over a 12-month window. 15% share an IP, 10% share a device. Risk score is computed automatically and status is set to `flagged` (>0.7), `review` (>0.4), or `clear`.

### Running the seed script

**Option A — Via Docker:**
```bash
docker cp scripts/seed_data.py framl-backend:/app/seed_data.py
docker exec -it framl-backend python seed_data.py
```

**Option B — Directly (any Neo4j instance):**

Edit credentials at the top of `scripts/seed_data.py`, then:
```bash
pip install faker neo4j
python scripts/seed_data.py
```

The script uses `MERGE` so it is safe to run multiple times without creating duplicates.

---

## Running Locally

### Prerequisites
- Docker Desktop (6 GB RAM minimum)
- Node.js LTS
- Python 3.10+

### Start all services

```bash
git clone https://github.com/prachijindall/Framl-graph
cd framl-graph
docker compose up --build -d
```

This starts:
- `framl-neo4j` — Neo4j on ports 7474 and 7687
- `framl-backend` — FastAPI on port 8000
- `framl-frontend` — Nginx on port 3000

Neo4j takes ~60 seconds to become healthy. The backend waits automatically.

### Frontend dev server

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Local URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend Swagger | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |

Neo4j browser credentials: `neo4j` / `password123`

---

## Deployment

The live app runs across three cloud services.

**Neo4j Aura** — Create a free instance at https://console.neo4j.io and note your `neo4j+s://` URI, username, and password.

**Render (Backend)** — Connect your GitHub repo, set root directory to `backend/`, and add these environment variables:

| Key | Value |
|---|---|
| `NEO4J_URI` | `neo4j+s://your-instance.databases.neo4j.io` |
| `NEO4J_USER` | your Aura username |
| `NEO4J_PASSWORD` | your Aura password |

**Vercel (Frontend)** — Connect your GitHub repo, set root directory to `frontend/`, and ensure `API_BASE` in `src/App.jsx` points to your Render URL.

---

## Quick API Test

```bash
# Check stats
curl https://framl-graph-2l3l.onrender.com/analytics/stats

# Get first 10 users
curl "https://framl-graph-2l3l.onrender.com/users?limit=10"

# Get flagged transactions sorted by risk
curl "https://framl-graph-2l3l.onrender.com/transactions?status=flagged&sort_by=risk_score&order=desc&limit=10"

# Get all connections of a user
curl https://framl-graph-2l3l.onrender.com/relationships/user/U-00001

# Shortest path between two users
curl "https://framl-graph-2l3l.onrender.com/analytics/shortest-path?user1_id=U-00001&user2_id=U-00050"
```

---

## Author

**Prachi Jindal**
GitHub: https://github.com/prachijindall/Framl-graph