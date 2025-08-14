from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.responses.step_3 import get_service_translating_status_response, patch_area_translated_text_response
from app.crud.area import read_area_by_id, read_areas_bulk_by_service_id, update_area
from app.crud.service import read_service_by_id, update_service
from app.db import get_db
from app.models.enums.service import Language, ServiceStep, ServiceStatus
from app.schemas.area import AreaReadAfterTranslating, AreaUpdate, PatchAreaTranslatedTextRequest
from app.schemas.service import GetServiceTranslatingStatusResponse, PostServiceTranslateRequest, ServiceUpdate
from app.tasks.translate import TranslatePayload, translate_areas
from app.utils.enum_to_html import enum_to_html

router = APIRouter()

@router.post(
  "/service/{service_id}/translate",
  summary="텍스트 번역 진행 (비동기)", 
  description=
    f"""
      ID와 일치하는 서비스의 번역을 진행합니다.<br>
      (비동기) 영역별로 텍스트의 번역 모델을 가동합니다. <br>
      {enum_to_html(Language)}
    """,
  status_code=status.HTTP_202_ACCEPTED,
)
async def make_service_to_translating_mode(request: PostServiceTranslateRequest, service_id: str, db: AsyncSession = Depends(get_db)):
  service_id_num = int(service_id)

  # 1. 서비스 조회
  service = await read_service_by_id(db, service_id_num)
  if not service:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 서비스입니다.")
  if service.step != ServiceStep.DETECTING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"DETECTING step이 아닙니다.")
  if service.status != ServiceStatus.PENDING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"OCR 진행 중이거나 오류로 인해 진행할 수 없는 서비스입니다.")

  # 2. 서비스 step 전환
  service_in = ServiceUpdate(
    step=ServiceStep.TRANSLATING,
    status=ServiceStatus.PROCESSING,
    target_language=request.target_language,
  )
  updated_service = await update_service(db=db, id=service.id, service_in=service_in)

  # 3. 번역 진행
  payload = TranslatePayload(
    service_id=service_id_num, 
    origin_language=service.origin_language,
    target_language=request.target_language
  )

  translate_areas.delay(payload, service.id)

  return updated_service

@router.get(
  "/service/{service_id}/status", 
  summary="번역 완료 여부 확인 및 결과 반환",
  description=
    f"""
      ID와 일치하는 서비스의 번역 완료 여부 및 영역 정보와 감지된 텍스트 & 번역된 텍스트를 반환합니다.<br>
      <h3>Response 중 Optional 항목</h3>
      <ui>
        <li><strong>areas</strong>: PENDING(완료 후 대기) 상태가 아니라면 null</li>
      </ui>
    """,
  status_code=status.HTTP_200_OK,
  response_model=GetServiceTranslatingStatusResponse,
  responses=get_service_translating_status_response()
)
async def get_service_status(service_id: str, db: AsyncSession = Depends(get_db)):
  service_id_num = int(service_id)

  # 1. 서비스 조회 & 유효성 검사
  service = await read_service_by_id(db, service_id_num)
  if not service:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 서비스입니다.")
  if service.step != ServiceStep.TRANSLATING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"TRANSLATING 단계가 아닌 서비스입니다.")

  # 2. 서비스 완료 여부 검사 및 반환
  if service.status == ServiceStatus.PENDING: # OCR이 완료되고 다음 입력을 기다리는 상태
    areas = await read_areas_bulk_by_service_id(db, service_id_num)
    areas_after_detecting = [
      AreaReadAfterTranslating(
        id=area.id,
        created_at=area.created_at,
        service_id=area.service_id,
        x1=area.x1,
        x2=area.x2,
        y1=area.y1,
        y2=area.y2,
        origin_text=area.origin_text or "error",
        translated_text=area.translated_text or "error",
      ) for area in areas
    ]

    return GetServiceTranslatingStatusResponse(
      isCompleted=True,
      id=service_id_num,
      status=service.status,
      areas=areas_after_detecting
    )
  else:
    return GetServiceTranslatingStatusResponse(
      isCompleted=True,
      id=service_id_num,
      status=service.status,
      areas=None
    )

@router.patch(
  "/area/{service_id}/{area_id}", 
  summary="텍스트 영역의 번역 텍스트 수정", 
  description=
    f"""
      ID와 일치하는 영역의 번역 텍스트를 수정합니다.
    """,
  status_code=status.HTTP_201_CREATED,
  responses=patch_area_translated_text_response(),
  response_model=AreaReadAfterTranslating
)
async def patch_area_translated_text(service_id: str, area_id: str, request: PatchAreaTranslatedTextRequest, db: AsyncSession = Depends(get_db)):
  service_id_num = int(service_id)
  area_id_num = int(area_id)

  # 0. 유효성 검사
  if len(request.new_translated_text) == 0 :
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="newTranslatedText가 비어 있습니다.")
  
  # 1. 영역 및 서비스 조회
  service = await read_service_by_id(db, service_id_num)
  if not service:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 서비스입니다.")
  if service.step != ServiceStep.TRANSLATING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"TRANSLATING 단계가 아닌 서비스입니다.")
  if service.status != ServiceStatus.PENDING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"번역이 진행 중인 서비스입니다.")

  area = await read_area_by_id(db, area_id_num)
  if not area:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 영역입니다.")
  if area.service_id != service_id_num:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"해당 서비스에 할당된 영역이 아닙니다.")
  
  # 2. 영역의 원본 텍스트 수정
  patched_area = await update_area(db, AreaUpdate(
    id=area_id_num,
    translated_text=request.new_translated_text
  ))

  return AreaReadAfterTranslating(
    id=patched_area.id,
    created_at=patched_area.created_at,
    service_id=patched_area.service_id,
    x1=patched_area.x1,
    x2=patched_area.x2,
    y1=patched_area.y1,
    y2=patched_area.y2,
    origin_text=patched_area.origin_text or "error",
    translated_text=patched_area.translated_text or "error",
  )
