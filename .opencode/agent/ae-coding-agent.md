# Analytics Engineering Case Study Rules

## Environment & Tooling

**Package Manager:** Always run Python, dbt, and Marimo commands via `uv run` (e.g., `uv run dbt build --profiles-dir .`) so commands execture inside the project `.venv`.

**dbt Execution & Testing:**
Validate setup: `uv run dbt debug --profiles-dir .`
Build models and run all tests: `uv run dbt build --profiles-dir .`
Run specific model(s): `uv run dbt run --select <model_name> --profiles-dir .`
Run tests only: `uv run dbt test --profiles-dir .
**Warehouse:** Local DuckDB (`data/warehouse/stingray.duckdb`).

**Raw Data:** Located in `data/raw/` (CSV, Parquet, or JSON). Do not modify raw files in place.

**Python & Linting (Ruff):**
Run helper scripts: `uv run python <script.py>`
Lint and format Python/Marimo files: `uv run ruff check --fix . && uv run ruff format .`

**Marimo Notebooks:**
Edit/validate notebooks: `uv run marimo check notebooks/`

## Architecture & Layering Rules

**Staging (`models/staging/`):**
Strictly 1-to-1 with raw source tables.
Naming: `stg_<source>__.sql`.
Allowed operations: Renaming columns (`snake_case`), explicit data type casting, standardizing timestamps to `_utc`, basic trimming/lowercasing, and deduplication.
**Forbidden:** Joins, aggregations, or business logic.

**Intermediate (`models/intermediate/`):**
Naming: `int__<verb>.sql`.
Use for complex joins, sessionization, date-spine gap filling, and SCD Type 2 logic.

**Marts (`models/marts/`):**
Design a strict **Star Schema** optimized for **Power BI**: `dim_.sql` and `fct_<event_or_metric>.sql`.
Every mart model must explicitly state its **grain** in a top-of-file comment and in `_mart_models.yml`.
Avoid wide, denormalized flat tables unless explicitly justified for performance.



## SQL Style & Conventions

Use CTEs (`with ... as`) rather than subqueries.
Place `select` statements at the bottom of the file (`final as (...) select * from final`).
Name all booleans with `is_` or `has_` prefixes.
Name all timestamps with `_at_utc` and dates with `_date`.
Always use explicit column lists—never `select *` in intermediate or mart models.

# Python Coding & Linting Rules

## Verification Commands
- Run `ruff check --fix . && ruff format .` after every edit.
- Never use `# noqa` or `# type: ignore` without an explanatory comment.

## Python Conventions
- Target Python 3.12+. Use native generics (`list[str]`, `dict[str, int]`) and `X | Y` unions.
- Use `pathlib.Path` instead of `os.path` for all filesystem operations.
- Write Pydantic v2 models or frozen `@dataclass(slots=True)` for structured data.
- Never swallow exceptions with bare `except:` or broad `except Exception:`. Let errors surface.
- Require keyword-only arguments (`*`) for functions taking 4+ parameters.
- Keep functions small and declare variables close to their first use.

## Data Quality, Testing & Documentation

**Never silently drop anomalies.** Log duplicate IDs, orphaned foreign keys, negative sensor values, or time-series gaps in `README.md` under "Data Quality Findings" and explain how they were handled.
Every model must have a corresponding YAML entry with descriptions, `unique`, and `not_null` tests on primary keys, and `relationships` tests on foreign keys.
Run `uv run dbt build --profiles-dir .` after creating or modifying models to verify compilation and tests pass.


## Workflow Behavior

When new raw files are placed in `data/raw/`, first inspect schemas, row counts, date ranges, primary keys, and anomalies.
Propose the Star Schema design and metric definitions for user approval before building mart models.
