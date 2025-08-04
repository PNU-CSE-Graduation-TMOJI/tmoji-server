import os
from dotenv import load_dotenv

def load_environment():
    env_mode = os.getenv("ENV_MODE", "local")

    if env_mode == "docker":
        load_dotenv(dotenv_path=".env.docker")
    else:
        load_dotenv(dotenv_path=".env.local")