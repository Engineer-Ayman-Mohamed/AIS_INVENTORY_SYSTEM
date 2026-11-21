# Module Documentation: `app/config.py`

## 1. Executive Summary & Purpose
The [config.py](file:///E:/Enexabit/AIS_Inventory_system/app/config.py) module serves as the centralized configuration management component for the AIS Inventory Management & Valuation System. It utilizes `pydantic-settings` to parse, validate, and provide application-wide settings and environment variables, ensuring uniform configuration across development, offline demonstration, and cloud deployments.

---

## 2. AIS Cycle Phase: **Foundation & Control**
Within the Accounting Information System (AIS) framework, system parameters dictate access controls, environment segregation, and audit ownership:
- **Default Operator Stamping:** Configures default user identity (`Ayman Mohamed (Team Leader)`) to ensure all ledger and audit actions are attributed to a responsible entity.
- **Connection Uniformity:** Enforces strict database URI formatting before connection attempts to prevent runtime state loss.

---

## 3. Core Classes & Methods

### `Settings(BaseSettings)`
Defines configuration properties and manages automated environment parsing (`.env`).

| Property / Method | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `APP_NAME` | `str` | `"AIS Inventory Management & Valuation System"` | Human-readable system title displayed across OpenAPI metadata and dashboard headers. |
| `APP_VERSION` | `str` | `"1.0.0"` | Current operational build version. |
| `DEBUG` | `bool` | `True` | Debug mode toggle for verbose error logging during development. |
| `DATABASE_URL` | `str` | `"sqlite:///./ais_inventory.db"` | Primary connection URI. Defaults to local SQLite fallback if Neon PostgreSQL credentials are not provided. |
| `DEFAULT_OPERATOR` | `str` | `"Ayman Mohamed (Team Leader)"` | Default user identifier for single-user audit trail stamping. |
| `normalized_database_url` | `@property -> str` | Dynamic | Normalizes legacy database prefixes (e.g., converts `postgres://` from cloud providers like Neon/Heroku into `postgresql://` required by SQLAlchemy 2.0). |

---

## 4. Key Internal Controls & Architecture Decisions
- **Zero-Config Offline Fallback:** If cloud infrastructure (Neon Serverless PostgreSQL) is unreachable or `DATABASE_URL` is omitted, the system falls back safely to a local SQLite database (`ais_inventory.db`) without throwing unhandled startup crashes.
- **SQLAlchemy 2.0 URL Normalization:** Prevents dialect incompatibility exceptions during cloud container deployments by normalizing the database dialect string dynamically.
- **Immutable Instance:** Exports a singleton `settings = Settings()` instance imported throughout the application.

---

## 5. Module Dependencies & Interconnections
- **Upstream:** Loads variables from `.env` via `python-dotenv` and OS environment variables.
- **Downstream Consumers:**
  - [database.py](file:///E:/Enexabit/AIS_Inventory_system/app/database.py): Consumes `settings.normalized_database_url` to initialize SQLAlchemy engines and connection pooling.
  - [main.py](file:///E:/Enexabit/AIS_Inventory_system/app/main.py): Consumes `settings.APP_NAME`, `settings.APP_VERSION`, and operator configuration for health checks.
  - [routers/items.py](file:///E:/Enexabit/AIS_Inventory_system/app/routers/items.py), [routers/goods_in.py](file:///E:/Enexabit/AIS_Inventory_system/app/routers/goods_in.py), [routers/goods_out.py](file:///E:/Enexabit/AIS_Inventory_system/app/routers/goods_out.py), [routers/controls.py](file:///E:/Enexabit/AIS_Inventory_system/app/routers/controls.py): Consume `settings.DEFAULT_OPERATOR` to stamp audit trail records.
