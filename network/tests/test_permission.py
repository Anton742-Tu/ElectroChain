import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:8000/api"


def test_access(username, password, endpoint, method="GET", data=None):
    """Тестирует доступ к эндпоинту"""
    global response
    url = f"{BASE_URL}/{endpoint}"
    auth = HTTPBasicAuth(username, password)

    print(f"\nТестируем {username} -> {method} {url}")

    try:
        if method == "GET":
            response = requests.get(url, auth=auth)
        elif method == "POST":
            response = requests.post(url, auth=auth, json=data)
        elif method == "PUT":
            response = requests.put(url, auth=auth, json=data)
        elif method == "DELETE":
            response = requests.delete(url, auth=auth)

        print(f"Статус: {response.status_code}")
        if response.status_code != 200:
            print(f"Ответ: {response.text[:200]}")

        return response.status_code

    except Exception as e:
        print(f"Ошибка: {e}")
        return None


# Тестируем разных пользователей
users = [("admin", "admin123"), ("sales_manager", "sales123"), ("analyst", "analyst123"), ("inactive", "inactive123")]

# Тестируем разные эндпоинты
endpoints = [
    ("network-nodes/", "GET"),
    ("products/", "GET"),
    ("auth/me/", "GET"),
    ("network-nodes/suppliers_summary/", "GET"),
]

print("=" * 60)
print("ТЕСТИРОВАНИЕ СИСТЕМЫ ПРАВ ДОСТУПА")
print("=" * 60)

for username, password in users:
    print(f"\n{'=' * 40}")
    print(f"Пользователь: {username}")
    print(f"{'=' * 40}")

    for endpoint, method in endpoints:
        test_access(username, password, endpoint, method)
