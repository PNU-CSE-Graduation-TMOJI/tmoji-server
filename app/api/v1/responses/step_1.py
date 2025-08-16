from typing import Any, Dict
from fastapi import status

def start_service_response() -> Dict[int | str, Dict[str, Any]]:
  return {
    status.HTTP_201_CREATED: {
      "description": "성공적으로 업로드된 이미지 정보",
      "content": {
        "application/json": {
          "example": {
              "id": 6,
              "originImageId": 12,
              "mode": "AI",
              "step": "BOUNDING",
              "status": "PENDING",
              "originLanguage": "JP",
              "targetLanguage": None,
              "createdAt": "2025-08-04T18:16:55.001359Z"
          }
        }
      }
    },
    status.HTTP_404_NOT_FOUND: {
      "description": "이미지 처리 실패",
      "content": {
        "application/json": {
          "example": {
            "detail": "존재하지 않는 이미지입니다."
          }
        }
      }
    }
  }