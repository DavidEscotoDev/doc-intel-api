# Task 2 Review: Database Layer (SQLAlchemy 2.0 Async)

**Status: FAIL** — Critical issues block approval

---

## Critical Findings (Must Fix)

### 1. **Type Annotations Use Function Instead of Type** (mypy strict fails)
All models use `uuid4` (function) instead of `UUID` (type) for `Mapped[]` annotations.

**Files affected:**
- `app/models/document.py:28` — `Mapped[uuid4]` → `Mapped[UUID]`
- `app/models/document.py:45` — `Mapped[uuid4]` → `Mapped[UUID]`
- `app/models/api_key.py:26` — `Mapped[uuid4]` → `Mapped[UUID]`
- `app/models/analysis.py:27` — `Mapped[uuid4]` → `Mapped[UUID]`
- `app/models/analysis.py:32` — `Mapped[uuid4]` → `Mapped[UUID]`

**Fix:** Import `from uuid import UUID` and use `UUID` type.

### 2. **Missing Forward References in Relationships** (mypy strict fails)
Models reference each other without forward-ref strings.

**Files affected:**
- `app/models/document.py:69` — `Mapped["APIKey"]` (OK as string) but `APIKey` not imported
- `app/models/document.py:70` — `Mapped["Analysis | None"]` (OK as string) but `Analysis` not imported
- `app/models/api_key.py:61` — `Mapped[list["Document"]]` needs forward ref
- `app/models/analysis.py:62` — `Mapped["Document"]` needs forward ref

**Fix:** Use string annotations (already partially done) and ensure imports in `TYPE_CHECKING` block.

### 3. **Missing Type Parameter for `dict`** (mypy strict fails)
`app/models/analysis.py:52` — `Mapped[Optional[dict]]` → `Mapped[Optional[dict[str, Any]]]`

### 4. **`DocumentStatus` Not Exported from Models Module** (mypy strict fails)
`app/models/__init__.py:4` imports `DocumentStatus` from `app.models.document` but it's defined in `app.constants`.

**Fix:** Export from `app.constants` or move enum to models.

### 5. **Database Session Context Manager Type Error** (mypy strict fails)
`app/database.py:76` — `"None" not callable` on `async with self._session_factory()`.

**Fix:** Add proper type guard or assert `self._session_factory is not None`.

### 6. **Test Coverage Below Threshold** (68.84% < 85% required)
Coverage gap primarily in `app/database.py` (47%), `app/logging.py` (30%), `app/telemetry.py` (49%), `app/config.py` (76%).

---

## Important Findings

### 7. **Alembic Migration Uses PostgreSQL-Specific Types for SQLite Tests**
`alembic/versions/20260713_1228_c99ffe044aab_initial_schema.py` uses:
- `sa.Uuid()` — PG-specific
- `sa.Enum(..., name='documentstatus')` — PG enum type

Tests run on SQLite (`sqlite+aiosqlite:///:memory:`) which doesn't support these natively. SQLAlchemy can emulate some but migrations may diverge.

**Recommendation:** Ensure test DB matches production (PostgreSQL) or use alembic's `render_as_batch` for SQLite compatibility.

### 8. **Test Fixture Uses String Instead of Enum**
`tests/conftest.py:144` — `status="uploaded"` should be `status=DocumentStatus.UPLOADED`

Works because SQLAlchemy coerces but violates type safety.

### 9. **Analysis Model Changed `ARRAY(String)` to `JSON`**
Diff shows `key_points`, `entities`, `topics` changed from `ARRAY(String)` to `JSON`. This is a schema change from the original plan — verify it's intentional. JSON is more portable across DBs but less queryable.

### 10. **Bcrypt Hash Hardcoded in Tests**
`tests/conftest.py:115` and `tests/conftest.py:144` use hardcoded bcrypt hashes. Acceptable for tests but document the plaintext values.

---

## Minor Findings

### 11. **Missing `onupdate` for `updated_at` in APIKey Migration**
Alembic migration has `server_default=sa.text('(CURRENT_TIMESTAMP)')` for both `created_at` and `updated_at` but no `onupdate`. Model has `onupdate=func.now()` — migration will not auto-update on row change.

### 12. **Database Config Missing Type Hints**
`app/config.py` has mypy errors for missing named arguments in settings classes.

### 13. **Session Factory `autoflush=False`**
`app/database.py:50` — `autoflush=False` may cause stale reads in complex transactions. Document why or use default `True`.

---

## Testability Assessment

| Test Area | Status |
|-----------|--------|
| Model creation | ✅ Covered (7 tests pass) |
| Relationships (bidirectional) | ✅ Covered |
| Cascade deletes | ✅ Covered |
| Indexes/constraints | ❌ Not tested |
| Enum handling | ⚠️ String used in fixture |
| Migration round-trip | ❌ Not tested |
| Async session lifecycle | ⚠️ Partially tested |

---

## Security Review

- ✅ No hardcoded secrets in source
- ✅ API key stored as bcrypt hash (`key_hash`)
- ✅ Cascade deletes use `ondelete="CASCADE"` at DB level
- ✅ UUID primary keys (not sequential IDs)

---

## Recommendation: **NEEDS_FIXES**

### Required before approval:
1. Fix all mypy strict errors (Critical #1-5)
2. Raise test coverage to ≥85% (Critical #6)
3. Fix test fixture to use `DocumentStatus.UPLOADED` (Important #8)
4. Verify JSON vs ARRAY change is intentional (Important #9)

### Recommended improvements:
5. Align test DB with production (PostgreSQL) or fix migrations for SQLite (Important #7)
6. Add migration `onupdate` trigger for `updated_at` (Minor #11)
7. Add index/constraint tests (Testability)
8. Add migration upgrade/downgrade test

---

## Quick Fix Checklist

```bash
# 1. Fix type annotations in all 3 models
# 2. Add TYPE_CHECKING imports for forward refs
# 3. Fix DocumentStatus export
# 4. Fix database.py session factory type
# 5. Fix analysis.py dict type param
# 6. Update conftest.py DocumentStatus usage
# 7. Add tests for database.py, config.py, logging.py, telemetry.py to reach 85%
# 8. Run: python -m mypy app/ --strict && python -m pytest --cov=app --cov-fail-under=85
```