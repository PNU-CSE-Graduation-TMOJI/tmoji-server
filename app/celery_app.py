# pyright: reportUnknownMemberType=false

import os
from celery import Celery

BROKER = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

celery = Celery(
  __name__, 
  broker=BROKER, 
  backend=BACKEND,
  include=[
    "app.tasks.ocr",
    "app.tasks.translate",
    "app.tasks.compose",
  ]
)