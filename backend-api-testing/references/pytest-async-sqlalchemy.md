# pytest + async SQLAlchemy Patterns

## Database Setup

### URL Encoding
Passwords with special characters (`@`, `:`, `/`, `?`, `#`, `[`, `]`) must be URL-encoded:

```python
from urllib.parse import quote_plus

TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{USER}:{quote_plus(PASSWORD)}"
    f"@{HOST}:{PORT}/{DB}"
)
```

### Engine Configuration
Use `NullPool` for test isolation to avoid "another operation is in progress" errors:

```python
from sqlalchemy.pool import NullPool

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)
```

### Session Factory
```python
TestSessionFactory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

## Fixtures

### Database Session
```python
@pytest_asyncio.fixture
async def db_session():
    async with TestSessionFactory() as session:
        yield session
```

### Per-Test Cleanup
```python
@pytest_asyncio.fixture(autouse=True)
async def clean_db(db_session):
    for table in reversed(Base.metadata.sorted_tables):
        await db_session.execute(text(f"TRUNCATE {table.name} CASCADE"))
    await db_session.commit()
```

### Dependency Override
```python
@pytest_asyncio.fixture
async def override_get_db():
    async def _get_db():
        async with TestSessionFactory() as session:
            yield session
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)
```

## DDL Migration Execution
Multi-statement DDL cannot be executed via `conn.execute(text(ddl))`. Use raw asyncpg:

```python
async with test_engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
    raw_conn = await conn.get_raw_connection()
    await raw_conn.driver_connection.execute(ddl)
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `cannot perform operation: another operation is in progress` | Concurrent ops on same connection | Use `NullPool` |
| `functions in index predicate must be marked IMMUTABLE` | Non-immutable functions in index | Use `Base.metadata.create_all()` or mark functions immutable |
| `Don't know how to join to X` | Multiple FK paths between tables | Add explicit `foreign_keys` to relationship |
| `ChunkedIteratorResult has no rowcount` | `.returning()` changes result type | Remove `.returning()` or use separate query |
