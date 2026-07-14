with open('tests/test_tasks_processor.py', 'r') as f:
    c = f.read()

c = c.replace('assert "Extraction failed" in test', 'assert "Extraction failed" in test_document.error_message')

with open('tests/test_tasks_processor.py', 'w') as f:
    f.write(c)
print('Fixed')