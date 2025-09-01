import os
from app.load_env import load_environment

load_environment()

def get_env_var(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value

CLIENT_URL = get_env_var("CLIENT_URL")