# Module Documentation: `app/main.py`

## 1. Executive Summary & Purpose
The [main.py](file:///E:/Enexabit/AIS_Inventory_system/app/main.py) module serves as the primary ASGI application entrypoint for the FastAPI framework. It coordinates startup lifecycles, registers middleware (CORS), mounts all REST API routers, serves static assets for the client interface, and provides health-monitoring endpoints.

---

## 2. AIS Cycle Phase: **System Integration & Orchestration**
Within the AIS architecture, [main.py](file:///E:/Enexabit/AIS_Inventory_system/app/main.py) ties together all decoupled phases:
- **Input & Output Channeling:** Maps HTTP request routing to dedicated domain routers.
- **System Initialization:** Automatically runs database schema synchronization on bootstrap.
- **Diagnostic Controls:** Real-time health check verifies connectivity to the underlying storage engine (Neon Serverless PostgreSQL or local SQLite).

---

## 3. Core Architecture & Components

```mermaid
flowchart TD
    Client[Web Browser / API Client] --> FastAPI[FastAPI App Instance]
    FastAPI --> CORS[CORS Middleware]
    FastAPI --> Lifespan[Async Lifespan -> init_db]
    FastAPI --> Static[/static Mount]
    FastAPI --> Health["GET /api/health"]
    FastAPI --> R_Dash["/api/dashboard -> Dashboard Router"]
    FastAPI --> R_Items["/api/items -> Items Router"]
    FastAPI --> R_GI["/api/goods-in -> Goods In Router"]
    FastAPI --> R_GO["/api/goods-out -> Goods Out Router"]
    FastAPI --> R_Val["/api/valuation -> Valuation Router"]
    FastAPI --> R_Ctrl["/api/controls -> Controls Router"]
```

### Key Handlers & Endpoints

| Endpoint / Function | Method | Tag | Description |
| :--- | :--- | :--- | :--- |
| `lifespan(app: FastAPI)` | `@asynccontextmanager` | Core Lifecycle | Executes on application boot; invokes `init_db()` from [database.py](file:///E:/Enexabit/AIS_Inventory_system/app/database.py) to guarantee tables exist before requests arrive. |
| `/` | `GET` | Static Delivery | Serves the single-page application entrypoint (`static/index.html`) or informative JSON fallback. |
| `/api/health` | `GET` | System Health | Returns operational status, active database dialect (`Neon PostgreSQL` vs `Local SQLite`), database ping connectivity status, and default operator signature. |
| Static Files Mount | `app.mount("/static")` | Assets | Serves static assets (HTML, CSS, JavaScript, icons) under the `/static` prefix. |

### API Router Registration
Integrates the 6 specialized subsystem routers:
1. `dashboard.router` (`/api/dashboard`)
2. `items.router` (`/api/items`)
3. `goods_in.router` (`/api/goods-in`)
4. `goods_out.router` (`/api/goods-out`)
5. `valuation.router` (`/api/valuation`)
6. `controls.router` (`/api/controls`)

---

## 4. Key Security & Operational Controls
- **Cross-Origin Resource Sharing (CORS):** Fully configured with `allow_origins=["*"]`, enabling browser frontends, local development servers, and containerized clients to communicate with the REST API.
- **Health Verification Integrity:** The `/api/health` route issues a live SQL query (`SELECT 1`) against the active session to detect severed database pools immediately.
- **Graceful Lifecycle Management:** Employs FastAPI's modern `lifespan` context manager rather than deprecated `on_event("startup")` hooks.

---

## 5. Module Dependencies & Interconnections
- **Upstream:** Imports configuration from [config.py](file:///E:/Enexabit/AIS_Inventory_system/app/config.py) and database utilities from [database.py](file:///E:/Enexabit/AIS_Inventory_system/app/database.py).
- **Downstream Routers:** Imports and mounts all router modules in `app/routers/`.
- **Runtime Execution:** Can be executed directly via Python (`python -m app.main`) or launched via Uvicorn ASGI server (`uvicorn app.main:app --host 0.0.0.0 --port 8000`).
