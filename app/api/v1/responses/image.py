from typing import Any, Dict
from fastapi import status

def upload_image_response() -> Dict[int | str, Dict[str, Any]]:
  return {
    status.HTTP_200_OK: {
      "description": "성공적으로 업로드된 이미지 정보",
      "content": {
        "application/json": {
          "example": {
            "id": 3,
            "filename": "8520476a-df2a-4494-a3f2-8850aa269992.png",
            "createdAt": "2025-07-31T17:44:30.569252Z"
          }
        }
      }
    },
    status.HTTP_400_BAD_REQUEST: {
      "description": "이미지 처리 실패",
      "content": {
        "application/json": {
          "example": {
            "detail": "이미지 처리 실패: Unsupported image format"
          }
        }
      }
    }
  }