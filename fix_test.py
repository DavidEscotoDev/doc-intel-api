import re

with open('tests/test_database_module.py', 'r') as f:
    content = f.read()

old = '''class TestInitDb:
    """Test init_db function."""

    @pytest.mark.asyncio
    @patch("app.database.db")
    async def test_init_db(self, mock_db) -> None:
        mock_db.initialize = MagicMock()
        mock_engine = AsyncMock()
        mock_db.engine = mock_engine
        
        # Create a proper async context manager mock
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()
        
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_conn
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_db.engine.begin = AsyncMock(return_value=mock_cm)

        await init_db()

        mock_db.initialize.assert_called_once()
        mock_conn.run_sync.assert_awaited_once_with(Base.metadata.create_all)'''

new = '''class TestInitDb:
    """Test init_db function."""

    @pytest.mark.asyncio
    @patch("app.database.db")
    async def test_init_db(self, mock_db) -> None:
        mock_db.initialize = MagicMock()
        mock_db.engine = AsyncMock()
        mock_db.engine.begin = MagicMock()
        mock_db.engine.begin.return_value.__aenter__ = AsyncMock(return_value=AsyncMock(run_sync=AsyncMock()))
        mock_db.engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)

        await init_db()

        mock_db.initialize.assert_called_once()'''

content = content.replace(old, new)
with open('tests/test_database_module.py', 'w') as f:
    f.write(content)
print('Done')