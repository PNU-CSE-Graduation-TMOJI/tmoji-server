# pyright: reportUnknownMemberType=false, reportAttributeAccessIssue=false, reportUnknownVariableType=false

import asyncio
from enum import Enum
from functools import lru_cache
from typing import List, TypedDict

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from paddleocr import PaddleOCR # type: ignore

from app.constants.database_url import DATABASE_URL
from app.crud.area import update_area
from app.crud.service import update_service
from app.models.enums.service import ServiceStatus, ServiceStep
from app.schemas.area import AreaUpdate
from app.schemas.service import ServiceUpdate # pyright: ignore[reportMissingTypeStubs]
from app.celery_app import celery

# --- 워커 전용 세션팩토리 ---
_engine = create_async_engine(DATABASE_URL, future=True)
SessionLocal = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)

# --- OCR 초기화 (언어 매핑 필요시 변환) ---
_LANG_MAP = {"EN": "en", "KO": "korean", "JP": "japan"}
_DEFAULT = "en"

class AreaPayload(TypedDict):
    area_id: int
    image_path: str
    lang: str  # "EN" | "KO" | "JP"

@lru_cache(maxsize=8)
def _get_ocr(lang: str) -> PaddleOCR:
    try:
        print(f"[DEBUG] Initializing OCR with lang='{lang}'")
        return PaddleOCR(lang=lang, use_angle_cls=True)
    except Exception as e:
        print(f"[ERROR] Failed to initialize OCR for lang={lang}: {e}")
        print("[DEBUG] Falling back to English OCR")
        return PaddleOCR(lang="en", use_angle_cls=True)

def _extract_text(image_path: str, lang_code: str) -> str:
    # Enum 들어오면 문자열로 변환
    if isinstance(lang_code, Enum):
        lang_code = lang_code.value
    # 언어 스위치(필요 시 모델 여러 개 두는 대신 lang 바꿔 재생성도 가능)
    lang = _LANG_MAP.get(lang_code, _DEFAULT)
    ocr = _get_ocr(lang)  # 언어별 인스턴스 캐시
    result = ocr.ocr(image_path) # pyright: ignore[reportDeprecated]
    # 결과에서 텍스트만 이어붙이기 (필요 시 좌표/확신도 함께 저장)
    lines: List[str] = []
    if result and result[0]:
        ocr_result = result[0]
        print(f"[DEBUG] OCR Raw Result:\n------confidence: {ocr_result['rec_scores']}\n------text: {ocr_result['rec_texts']}") # type: ignore
        for txt in ocr_result['rec_texts']:
            lines.append(txt) # type: ignore
    return "\n".join(lines)

@celery.task
def extract_areas(payloads: List[AreaPayload], service_id: int) -> bool:
    """Celery 워커에서 실행되는 동기 엔트리. 내부에서 async 실행."""
    print(f"--------OCR TASK, Service: {service_id}")
    async def _run() -> bool:
        async with SessionLocal() as db:
            for p in payloads:
                text = _extract_text(p["image_path"], p["lang"])
                print(f"[DEBUG] Extracted Text: {text}")
                area_in = AreaUpdate(id=p["area_id"], origin_text=text)
                await update_area(db, area_in)

            print(f"--------OCR 완료, Service Update")
            service_in = ServiceUpdate(step=ServiceStep.DETECTING, status=ServiceStatus.PENDING)
            await update_service(db, service_id, service_in)
        return True

    return asyncio.run(_run())
