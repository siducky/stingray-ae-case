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
Use `snake_case` for all files, folders, models, and columns. Prefix YAML files with an underscore (`_<domain>__models.yml`).

- **Staging (`stg_<source>__.sql`)**: 1:1 with raw source tables. Clean, rename, and cast columns only. Do not use joins or aggregations. Materialize as `view`.
- **Intermediate (`int_<domain>_<verb>.sql`)**: Modular business logic and complex joins between staging and marts. Materialize as `ephemeral` or `view`.
- **Marts - Facts (`fct_<business_process>.sql`)**: Immutable events, transactions, and metrics. Materialize as `table` or `incremental`.
- **Marts - Dimensions (`dim_.sql`)**: Descriptive business entities and attributes. Materialize as `table`.

### Column Naming Rules
- **Keys**: `_id`
- **Booleans**: `is_<condition>` or `has_<condition>`
- **Timestamps**: `<event>_at` (always cast to UTC)
- **Dates**: `<event>_date`

### SQL Structure & Style
- **CTE Pattern**: Structure every model into four sections:
  1. **Import CTEs**: Pull all upstream models at the top using `{{ source() }}` or `{{ ref() }}`. Never hardcode database or schema names.
  2. **Logical CTEs**: Isolate distinct transformations (filtering, joining, aggregating) into separate, descriptively named CTEs.
  3. **Final CTE**: Assemble output columns and aliases in a CTE named `final`.
  4. **Final Select**: Always end the file with `select * from final`.
- **Formatting**: Use lowercase for all SQL keywords (`select`, `from`, `where`) and functions. Avoid deeply nested subqueries.
- **Joins**: Always specify `inner join` or `left join` (never bare `join`). Qualify every column with its CTE/table name when joining multiple relations.
- **Grouping**: Use explicit column names in `group by` and `order by` clauses instead of positional numbers (`group by 1`).

### Dialect: DuckDB
- Write **DuckDB SQL** (PostgreSQL-compatible). Do not use Snowflake, BigQuery, or T-SQL syntax (e.g., avoid `QUALIFY` with Snowflake-specific functions unless valid in DuckDB, `SAFE_DIVIDE`, or `DATEADD`).
- Use `::` for type casting (e.g., `created_at::date`, `amount::decimal(18,2)`).
- Use `date_trunc('day', col)` and `date_diff('day', start_date, end_date)` for date math.
- Prefer explicit column lists over `SELECT * EXCLUDE (...)` in mart models to keep final schemas deterministic.

### Testing & Documentation
- Always apply `unique` and `not_null` tests to the primary key of every model.
- Add `relationships` tests to foreign keys and `accepted_values` tests to categorical status fields.

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
