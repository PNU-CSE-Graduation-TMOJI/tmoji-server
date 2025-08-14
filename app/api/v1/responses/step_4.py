from typing import Any, Dict
from fastapi import status

def get_service_composing_status_response() -> Dict[int | str, Dict[str, Any]]:
  return {
    status.HTTP_200_OK: {
      "description": "Service 정보",
      "content": {
        "application/json": {
          "example": {
            "isCompleted": True,
            "id": 10,
            "status": "PENDING",
            "composedImageFilename": "composed_e61272c0-36f4-4453-b699-24907e049199.png"
          }
        }
      }
    },
    status.HTTP_400_BAD_REQUEST: {
      "description": "잘못된 요청",
      "content": {
        "application/json": {
          "example": {
            "detail": "COMPOSING 단계가 아닌 서비스입니다."
          }
        }
      }
    },
    status.HTTP_404_NOT_FOUND: {
      "description": "존재하지 않는 서비스",
      "content": {
        "application/json": {
          "example": {
            "detail": "존재하지 않는 서비스입니다."
          }
        }
      }
    }
  }
