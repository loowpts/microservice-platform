import requests
from .models import UserProxy

USER_SERVICE_URL = "http://localhost:8000/api/profile/"

def get_user(user_id):
    response = requests.get(f"{USER_SERVICE_URL}{user_id}/")
    if response.status_code == 200:
        return UserProxy.from_api(response.json())
    return None
