from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.responses.step_4 import get_service_composing_status_response
from app.crud.image import read_image_by_id
from app.crud.service import read_service_by_id, update_service
from app.db import get_db
from app.models.enums.service import ServiceStep, ServiceStatus
from app.schemas.service import GetServiceComposingStatusResponse, ServiceUpdate
from app.tasks.compose import ComposePayload, compose_image

router = APIRouter()

@router.post(
  "/service/{service_id}/compose",
  summary="이미지 합성 진행 (비동기)", 
  description=
    f"""
      (비동기) ID와 일치하는 서비스의 이미지 합성을 진행합니다.<br>
    """,
  status_code=status.HTTP_202_ACCEPTED,
)
async def make_service_to_composing_mode(service_id: str, db: AsyncSession = Depends(get_db)):
  service_id_num = int(service_id)

  # 1. 서비스 조회
  service = await read_service_by_id(db, service_id_num)
  if not service:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 서비스입니다.")
  if service.step != ServiceStep.TRANSLATING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"TRANSLATING 단계가 아닙니다.")
  if service.status != ServiceStatus.PENDING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"합성이 진행 중이거나 오류로 인해 진행할 수 없는 서비스입니다.")

  # 2. 서비스 step 전환
  service_in = ServiceUpdate(
    step=ServiceStep.COMPOSING,
    status=ServiceStatus.PROCESSING,
  )
  updated_service = await update_service(db=db, id=service.id, service_in=service_in)

  # 3. 합성 진행
  payload = ComposePayload(
    service_id=service_id_num
  )

  compose_image.delay(payload)

  return updated_service

@router.get(
  "/service/{service_id}/status", 
  summary="합성 완료 여부 확인 및 결과 반환",
  description=
    f"""
      ID와 일치하는 서비스의 합성 완료 여부 및 완료된 이미지를 반환합니다.<br>
      <h3>Response 중 Optional 항목</h3>
      <ui>
        <li><strong>composed_image_filename</strong>: COMPLETED(완료) 상태가 아니라면 null</li>
      </ui>
    """,
  status_code=status.HTTP_200_OK,
  response_model=GetServiceComposingStatusResponse,
  responses=get_service_composing_status_response()
)
async def get_service_composing_status(service_id: str, db: AsyncSession = Depends(get_db)) -> GetServiceComposingStatusResponse:
  service_id_num = int(service_id)

  # 1. 서비스 조회 & 유효성 검사
  service = await read_service_by_id(db, service_id_num)
  if not service:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 서비스입니다.")
  if service.step != ServiceStep.COMPOSING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"COMPOSING 단계가 아닌 서비스입니다.")

  # 2. 서비스 완료 여부 검사 및 반환
  if service.status == ServiceStatus.COMPLETED: # 합성이 완료된 상태
    if not service.composed_image_id:
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"완성된 이미지를 찾을 수 없습니다.")
    
    composed_image = await read_image_by_id(db, service.composed_image_id)
    if not composed_image:
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"완성된 이미지를 찾을 수 없습니다.")

    return GetServiceComposingStatusResponse(
      isCompleted=True,
      id=service_id_num,
      status=service.status,
      composed_image_filename=composed_image.filename
    )
  else:
    return GetServiceComposingStatusResponse(
      isCompleted=False,
      id=service_id_num,
      status=service.status,
      composed_image_filename=None
    )
