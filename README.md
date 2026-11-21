# AIS Inventory Management and Valuation System

> **Accounting Information Systems (AIS)**  
> **Architecture:** FastAPI Backend, Neon Serverless PostgreSQL, HTML5 Single-Page Interface, Docker Containerization

---

## 1. Executive Summary

The AIS Inventory Management and Valuation System is an application designed to operationalize the fundamental Accounting Information System (AIS) cycle:

$$\text{Input} \longrightarrow \text{Processing} \longrightarrow \text{Output} \longrightarrow \text{Control}$$

The system provides real-time perpetual inventory tracking, multi-method valuation (FIFO, Weighted Average Cost, and LIFO), automated replenishment triggers, and internal controls tailored for financial audit readiness.

---

## 2. Core Functional Modules

- **Item Master Management:** Central catalog for Stock Keeping Units (SKUs), maintaining reorder thresholds, units of measure, live stock quantities, and moving average unit costs. Prohibits deletion of records with historical ledger activity.
- **Goods In (Purchases):** Records inventory acquisitions, updates dynamic Weighted Average Cost (WAC) upon receipt, and instantiates distinct historical Cost Layers for perpetual allocation.
- **Goods Out (Sales):** Records inventory dispatches, calculates perpetual Cost of Goods Sold (COGS) across FIFO, WAC, and LIFO methods, depresses active cost layers, and strictly enforces the **No Negative Inventory** rule.
- **Valuation and Financial Reporting Engine:** Generates real-time financial statements with dynamic toggles between cost-flow assumptions (FIFO, WAC, LIFO) and tracking systems (Perpetual vs. Periodic), complete with IAS 2.1.9 regulatory compliance disclosures.
- **Internal Controls and Managerial Oversight:** Implements automated reorder alerts, Pareto ABC inventory classification (80/15/5 rule), physical count reconciliation with an automated **2.0% tolerance threshold**, and an immutable chronological audit trail.
- **Executive Dashboard:** Presents operational Key Performance Indicators (KPIs), financial margins, inventory turnover, Days Sales in Inventory (DSI), and comparative visual analytics.

---

## 3. Internal Controls Compliance Matrix

The system implements nine internal accounting controls aligned with standard AIS principles:

| Number | Control Rule | Technical Implementation |
| :---: | :--- | :--- |
| **1** | **Input Validation** | Rejects zero, negative, or malformed numeric inputs at the schema layer before transaction processing. |
| **2** | **No Negative Inventory** | Sales transactions exceeding physical on-hand stock are rejected with an explicit HTTP 400 error. |
| **3** | **Referential Integrity** | Prohibits deletion of Item Master records that have associated purchase, sale, or audit records. |
| **4** | **Unique Item Codes** | Enforces a case-insensitive unique database index across all product SKUs. |
| **5** | **Immutable Audit Trail** | Every master data change, acquisition, sale, and reconciliation is logged permanently with an operator stamp and UTC timestamp. |
| **6** | **2% Reconciliation Tolerance** | Flags physical count discrepancies exceeding 2.0% of book value for mandatory audit investigation. |
| **7** | **ABC Classification** | Automatically categorizes inventory into Classes A, B, and C based on cumulative usage value to guide control stringency. |
| **8** | **Automated Replenishment** | Triggers low-stock alerts immediately when current on-hand units fall to or below the reorder point. |
| **9** | **User Provenance Stamping** | All transaction and audit logs capture user provenance for end-to-end accountability. |

---

## 4. Technical Architecture

- **Backend Framework:** Python 3.12+, FastAPI, SQLAlchemy 2.0 ORM, Pydantic 2.
- **Database Engine:** Neon Serverless PostgreSQL with SSL connection pooling; automatic zero-configuration SQLite fallback for offline development.
- **Frontend Layer:** Responsive single-page interface built with HTML5, CSS3, JavaScript, and Chart.js.
- **Containerization:** Production-ready Docker container and Docker Compose orchestration.

---

## 5. Repository Structure

```text
AIS_INVENTORY_SYSTEM/
|-- docs/                          # Comprehensive technical and architectural documentation
|   |-- INDEX.md                   # Documentation index and architecture workflow diagram
|   |-- ARCHITECTURE.md            # System specification and entity-relationship diagrams
|   |-- config.md                  # Settings and database URL normalization
|   |-- database.md                # Connection pooling and session lifecycle
|   |-- models.md                  # SQLAlchemy ORM entity models
|   |-- schemas.md                 # Pydantic request and response schemas
|   |-- accounting.md              # Mathematical valuation engine and algorithms
|   |-- main.py                    # ASGI application root and lifecycles
|   |-- router_*.md                # Specialized documentation for each API router
|   |-- seed_data.md               # Seeder script specification
|   `-- AIS_PROJECT_BRIEF.pdf      # Project requirements brief
|-- app/
|   |-- __init__.py
|   |-- main.py                    # FastAPI root application
|   |-- config.py                  # Environment configuration
|   |-- database.py                # Database connection and session factory
|   |-- models.py                  # Relational database models
|   |-- schemas.py                 # Request and response models
|   |-- accounting.py              # Accounting calculation engine
|   `-- routers/
|       |-- dashboard.py           # Executive KPIs and chart endpoints
|       |-- items.py               # Item Master catalog operations
|       |-- goods_in.py            # Goods In purchases and cost layer creation
|       |-- goods_out.py           # Goods Out sales and perpetual COGS
|       |-- valuation.py           # Financial valuation reports and comparisons
|       `-- controls.py            # Reorder alerts, ABC analysis, reconciliations, audit trail
|-- static/                        # Client-side user interface
|   |-- index.html                 # Executive dashboard single-page application
|   |-- css/style.css              # Application styling
|   `-- js/                        # Application controllers and Chart.js integration
|-- Dockerfile                     # Multi-stage production container specification
|-- docker-compose.yml             # Container orchestration
|-- seed_data.py                   # Demonstration dataset initializer
|-- pyproject.toml                 # Project metadata and dependencies
|-- requirements.txt               # Pinned package requirements
`-- README.md                      # Primary project readme
```

For detailed technical analysis of individual core modules, refer to the [Documentation Index](docs/INDEX.md).

---

## 6. Installation and Execution

### Local Development

1. **Clone the repository and enter directory:**
   ```bash
   git clone https://github.com/Engineer-Ayman-Mohamed/AIS_INVENTORY_SYSTEM.git
   cd AIS_INVENTORY_SYSTEM
   ```

2. **Install dependencies:**
   Using `uv`:
   ```bash
   uv sync
   ```
   Or standard `pip`:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure database credentials (optional):**
   Copy `.env.example` to `.env` to configure Neon Serverless PostgreSQL:
   ```env
   DATABASE_URL=postgresql://[user]:[password]@[neon-host]/[database]?sslmode=require
   ```
   If omitted, the system operates on the local SQLite fallback database (`ais_inventory.db`).

4. **Seed sample demonstration data:**
   ```bash
   python seed_data.py
   ```

5. **Start the API service:**
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

6. **Access endpoints:**
   - User Interface: [http://localhost:8000](http://localhost:8000)
   - Interactive OpenAPI Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Docker Deployment

Run the system in a containerized environment using Docker Compose:

```bash
docker compose up --build
```

The application will be accessible at [http://localhost:8000](http://localhost:8000).
