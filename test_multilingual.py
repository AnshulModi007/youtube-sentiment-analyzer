import requests
import json

payload = {
    'comments': [
        'este video es increíble',          # Spanish: Positive
        'बकवास वीडियो है समय बर्बाद किया',     # Hindi: Negative
        "c'est une bonne chose",            # French: Positive
        '이건 정말 실망스럽네요',                 # Korean: Negative
        'ganz ok, nichts besonderes'        # German: Neutral
    ]
}

try:
    r = requests.post('http://localhost:8000/analyze', json=payload)
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
