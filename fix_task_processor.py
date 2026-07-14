import re

with open('tests/test_tasks_processor.py', 'r') as f:
    c = f.read()

# Fix 1: Change get_file to get_file_path in all mocks
c = c.replace('mock_storage.get_file.return_value', 'mock_storage.get_file_path.return_value')
c = c.replace('mock_storage.get_file.side_effect', 'mock_storage.get_file_path.side_effect')

# Fix 2: Fix LLM mock to return object with attributes instead of dict
c = re.sub(
    r'mock_llm\.analyze\.return_value = \{[^}]+\}',
    '''mock_llm.analyze.return_value = MagicMock(
                summary="Test document summary",
                key_points=["Point 1", "Point 2"],
                entities=["Entity 1", "Entity 2"],
                sentiment="positive",
                topics=["Topic 1", "Topic 2"],
                tokens_used=150,
                raw="Raw LLM response",
            )''',
    c
)

c = re.sub(
    r'mock_llm\.analyze\.return_value = \{[^}]+\}',
    '''mock_llm.analyze.return_value = MagicMock(
                summary="Test",
                key_points=[],
                entities=[],
                sentiment="neutral",
                topics=[],
                tokens_used=50,
                raw="Raw",
            )''',
    c
)

# Fix 3: Add patch for init_db and close_db at the top of each test
# We need to wrap each test's patch blocks with init_db/close_db mocks
# This is complex, let's add the mocks to the existing patch blocks

# Fix 4: Fix the storage mock to use get_file_path
c = c.replace(
    'with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:',
    '''with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
            with patch("app.tasks.processor.init_db") as mock_init_db:
                with patch("app.tasks.processor.close_db") as mock_close_db:'''
)

# Fix the closing braces
c = c.replace(
    '''mock_storage_factory.return_value = mock_storage

                    # Run the background task
                    await process_document_task(str(test_document.id))''',
    '''mock_storage_factory.return_value = mock_storage

                    # Run the background task
                    await process_document_task(str(test_document.id))'''
)

# Fix the second test
c = c.replace(
    '''with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
                mock_storage = AsyncMock()
                mock_storage.get_file.return_value = b"%PDF-1.4\n%Test"
                mock_storage_factory.return_value = mock_storage

                await process_document_task(str(test_document.id))''',
    '''with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
            with patch("app.tasks.processor.init_db") as mock_init_db:
                with patch("app.tasks.processor.close_db") as mock_close_db:
                    mock_storage = AsyncMock()
                    mock_storage.get_file_path.return_value = b"%PDF-1.4\n%Test"
                    mock_storage_factory.return_value = mock_storage

                    await process_document_task(str(test_document.id))'''
)

# Fix the third test (llm failure)
c = c.replace(
    '''with patch("app.tasks.processor.get_llm_service") as mock_llm_factory:
                mock_llm = AsyncMock()
                mock_llm.analyze.side_effect = Exception("LLM API error")
                mock_llm_factory.return_value = mock_llm

                with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
                    mock_storage = AsyncMock()
                    mock_storage.get_file.return_value = b"%PDF-1.4\n%Test"
                    mock_storage_factory.return_value = mock_storage

                    await process_document_task(str(test_document.id))''',
    '''with patch("app.tasks.processor.get_llm_service") as mock_llm_factory:
            with patch("app.tasks.processor.init_db") as mock_init_db:
                with patch("app.tasks.processor.close_db") as mock_close_db:
                    mock_llm = AsyncMock()
                    mock_llm.analyze.side_effect = Exception("LLM API error")
                    mock_llm_factory.return_value = mock_llm

                    with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
                        mock_storage = AsyncMock()
                        mock_storage.get_file_path.return_value = b"%PDF-1.4\n%Test"
                        mock_storage_factory.return_value = mock_storage

                        await process_document_task(str(test_document.id))'''
)

# Fix the fourth test (storage failure)
c = c.replace(
    '''with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
            mock_storage = AsyncMock()
            mock_storage.get_file.side_effect = Exception("Storage unavailable")
            mock_storage_factory.return_value = mock_storage

            await process_document_task(str(test_document.id))''',
    '''with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
            with patch("app.tasks.processor.init_db") as mock_init_db:
                with patch("app.tasks.processor.close_db") as mock_close_db:
                    mock_storage = AsyncMock()
                    mock_storage.get_file_path.side_effect = Exception("Storage unavailable")
                    mock_storage_factory.return_value = mock_storage

                    await process_document_task(str(test_document.id))'''
)

# Fix the fifth test (database error)
c = c.replace(
    '''with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
                    mock_storage = AsyncMock()
                    mock_storage.get_file.return_value = b"%PDF-1.4\n%Test"
                    mock_storage_factory.return_value = mock_storage

                    # Make db commit fail
                    with patch.object(db_session, "commit", side_effect=Exception("DB error")):
                        await process_document_task(str(test_document.id))''',
    '''with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
            with patch("app.tasks.processor.init_db") as mock_init_db:
                with patch("app.tasks.processor.close_db") as mock_close_db:
                    mock_storage = AsyncMock()
                    mock_storage.get_file_path.return_value = b"%PDF-1.4\n%Test"
                    mock_storage_factory.return_value = mock_storage

                    # Make db commit fail
                    with patch.object(db_session, "commit", side_effect=Exception("DB error")):
                        await process_document_task(str(test_document.id))'''
)

# Fix the sixth test (processing status)
c = c.replace(
    '''with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
                    mock_storage = AsyncMock()
                    mock_storage.get_file.return_value = b"%PDF-1.4\n%Test"
                    mock_storage_factory.return_value = mock_storage

                    await process_document_task(str(test_document.id))''',
    '''with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
            with patch("app.tasks.processor.init_db") as mock_init_db:
                with patch("app.tasks.processor.close_db") as mock_close_db:
                    mock_storage = AsyncMock()
                    mock_storage.get_file_path.return_value = b"%PDF-1.4\n%Test"
                    mock_storage_factory.return_value = mock_storage

                    await process_document_task(str(test_document.id))'''
)

# Fix imports - add MagicMock
c = c.replace(
    'from unittest.mock import AsyncMock, MagicMock, patch',
    'from unittest.mock import AsyncMock, MagicMock, patch, MagicMock'
)

with open('tests/test_tasks_processor.py', 'w') as f:
    f.write(c)
print('Done')