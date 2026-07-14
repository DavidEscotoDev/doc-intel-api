with open('tests/test_routes_process.py', 'r') as f:
    c = f.read()

# Fix the syntax errors in the test_analyze_document_wrong_owner test
c = c.replace(
    'pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto APIKey(',
    'from passlib.context import CryptContext\n        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")\n        other_key = APIKey('
)

with open('tests/test_routes_process.py', 'w') as f:
    f.write(c)
print('Fixed')