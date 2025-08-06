from typing import Any, Dict
from fastapi import status

def make_areas_response() -> Dict[int | str, Dict[str, Any]]:
  return {
    status.HTTP_202_ACCEPTED: {
      "description": "OCR 접수 및 Area 생성이 요청된 Service 정보",
      "content": {
        "application/json": {
          "example": {
            "id": 10,
            "originImageId": 33,
            "mode": "AI",
            "step": "DETECTING",
            "status": "PROCESSING",
            "originLanguage": "JP",
            "targetLanguage": None,
            "createdAt": "2025-08-05T18:37:06.468436Z"
          }
        }
      }
    },
    status.HTTP_400_BAD_REQUEST: {
      "description": "잘못된 요청",
      "content": {
        "application/json": {
          "example": {
            "detail": "이미 영역을 생성한 서비스입니다."
          }
        }
      }
    },
    status.HTTP_404_NOT_FOUND: {
      "description": "존재하지 않는 Service",
      "content": {
        "application/json": {
          "example": {
            "detail": "존재하지 않는 서비스입니다."
          }
        }
      }
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
      "description": "예상치못한 서버 오류",
      "content": {
        "application/json": {
          "example": {
            "detail": "서버 오류가 발생하였습니다."
          }
        }
      }
    }
  }

def get_service_status_response() -> Dict[int | str, Dict[str, Any]]:
  return {
    status.HTTP_200_OK: {
      "description": "Service 정보",
      "content": {
        "application/json": {
          "example": {
            "isCompleted": True,
            "id": 10,
            "status": "PENDING",
            "areas": [
                {
                    "x1": 119,
                    "x2": 755,
                    "y1": 732,
                    "y2": 874,
                    "id": 70,
                    "createdAt": "2025-08-06T14:03:57.798231Z",
                    "serviceId": 10,
                    "originText": "中島公园"
                },
                {
                    "x1": 137,
                    "x2": 270,
                    "y1": 669,
                    "y2": 731,
                    "id": 71,
                    "createdAt": "2025-08-06T14:03:57.798231Z",
                    "serviceId": 10,
                    "originText": "出入口"
                },
                {
                    "x1": 272,
                    "x2": 405,
                    "y1": 678,
                    "y2": 731,
                    "id": 72,
                    "createdAt": "2025-08-06T14:03:57.798231Z",
                    "serviceId": 10,
                    "originText": "南北線"
                }
            ]
        } 
        }
      }
    },
    status.HTTP_400_BAD_REQUEST: {
      "description": "잘못된 요청",
      "content": {
        "application/json": {
          "example": {
            "detail": "DETECTING(OCR) 단계가 아닌 서비스입니다."
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

def patch_area_origin_text_response() -> Dict[int | str, Dict[str, Any]]:
  return {
    status.HTTP_201_CREATED: {
      "description": "Area 정보",
      "content": {
        "application/json": {
          "example": {
              "x1": 119,
              "x2": 755,
              "y1": 732,
              "y2": 874,
              "id": 70,
              "createdAt": "2025-08-06T14:03:57.798231Z",
              "serviceId": 10,
              "originText": "中島公園駅"
          }
        }
      }
    },
    status.HTTP_400_BAD_REQUEST: {
      "description": "잘못된 요청",
      "content": {
        "application/json": {
          "example": {
            "detail": "DETECTING(OCR) 단계가 아닌 서비스입니다."
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