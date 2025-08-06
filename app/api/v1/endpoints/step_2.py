import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image as PILImage

from app.api.v1.responses.step_2 import delete_area_response, get_service_status_response, make_areas_response, patch_area_origin_text_response
from app.constants.image_path import CROP_DIR, UPLOAD_DIR
from app.crud.area import create_areas_bulk, delete_area_by_id, read_area_by_id, read_areas_bulk_by_service_id, update_area
from app.crud.image import create_image, read_image_by_id
from app.crud.service import read_service_by_id, update_service
from app.db import get_db
from app.models.enums.service import ServiceStep, ServiceStatus
from app.schemas.area import AreaCreate, AreaReadAfterDetecting, AreaUpdate, PatchAreaOriginTextRequest, PostAreaRequest
from app.schemas.image import ImageCreate, ImageRead
from app.schemas.service import GetServiceStatusResponse, ServiceUpdate
from app.tasks.ocr import AreaPayload, extract_areas

router = APIRouter()

@router.post(
  "/areas", 
  summary="텍스트 영역 지정", 
  description=
    f"""
      ID와 일치하는 서비스에 바운딩 박스(영역)을 생성합니다.
    """,
  status_code=status.HTTP_202_ACCEPTED,
  responses=make_areas_response()
)
async def make_areas(request: PostAreaRequest, db: AsyncSession = Depends(get_db)):
  # 0. 유효성 검사
  if len(request.areas) == 0 :
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="area가 비어 있습니다.")
  
  # 1. 서비스 조회
  service = await read_service_by_id(db, request.service_id)
  if not service:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 서비스입니다.")
  if service.step != ServiceStep.BOUNDING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"이미 영역을 생성한 서비스입니다.")
  
  # 2. 잘라낸 이미지 저장
  originImage = await read_image_by_id(db, service.origin_image_id)
  if not originImage:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="서버 오류가 발생하였습니다.")
  
  cropped_images: List[ImageRead] = []
  originImageFile = PILImage.open(os.path.join(UPLOAD_DIR, originImage.filename))

  os.makedirs(CROP_DIR, exist_ok=True)
  for i, area in enumerate(request.areas):
    cropped = originImageFile.crop((area.x1, area.y1, area.x2, area.y2))

    cropped_filename = f'{originImage.filename[:-4]}_{i+1}.png'
    cropped_save_path = os.path.join(CROP_DIR, cropped_filename)
    cropped.save(cropped_save_path, format="PNG")

    image_db = await create_image(db, image_in=ImageCreate(filename=cropped_filename))
    cropped_images.append(image_db)

  # 3. 영역(바운딩 박스) DB 기록
  areas_in = [AreaCreate(
    x1=area.x1,
    x2=area.x2,
    y1=area.y1,
    y2=area.y2,
    service_id=request.service_id,
    area_image_id=cropped_images[i].id,
  ) for i, area in enumerate(request.areas)]

  areas = await create_areas_bulk(db, areas_in)

  # 4. 서비스 step 전환
  service_in = ServiceUpdate(
    step=ServiceStep.DETECTING,
    status=ServiceStatus.PROCESSING,
  )
  service = await update_service(db=db, id=service.id, service_in=service_in)

  # 5. OCR 진행
  payloads: List[AreaPayload] = []
  for i, area in enumerate(areas):
    area_pay_load = AreaPayload(
      area_id=area.id,
      image_path=os.path.join(CROP_DIR, cropped_images[i].filename),
      lang=service.origin_language.value,
    )
    payloads.append(area_pay_load)

  extract_areas.delay(payloads, service.id) # pyright: ignore[reportFunctionMemberAccess]

  return service
  
@router.get(
  "/service/{service_id}/status", 
  summary="OCR(DETECTING) 완료 여부 확인 및 결과 반환",
  description=
    f"""
      ID와 일치하는 서비스의 OCR 완료 여부 및 영역 정보와 감지된 텍스트를 반환합니다.<br>
      <h3>Response 중 Optional 항목</h3>
      <ui>
        <li><strong>areas</strong>: PENDING(완료 후 대기) 상태가 아니라면 null</li>
      </ui>
    """,
  status_code=status.HTTP_200_OK,
  response_model=GetServiceStatusResponse,
  responses=get_service_status_response()
)
async def get_service_status(service_id: str, db: AsyncSession = Depends(get_db)):
  service_id_num = int(service_id)

  # 1. 서비스 조회 & 유효성 검사
  service = await read_service_by_id(db, service_id_num)
  if not service:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 서비스입니다.")
  if service.step != ServiceStep.DETECTING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"DETECTING(OCR) 단계가 아닌 서비스입니다.")

  # 2. 서비스 완료 여부 검사 및 반환
  if service.status == ServiceStatus.PENDING: # OCR이 완료되고 다음 입력을 기다리는 상태
    areas = await read_areas_bulk_by_service_id(db, service_id_num)
    areas_after_detecting = [
      AreaReadAfterDetecting(
        id=area.id,
        created_at=area.created_at,
        service_id=area.service_id,
        x1=area.x1,
        x2=area.x2,
        y1=area.y1,
        y2=area.y2,
        origin_text=area.origin_text or "error",
      ) for area in areas
    ]

    return GetServiceStatusResponse(
      isCompleted=True,
      id=service_id_num,
      status=service.status,
      areas=areas_after_detecting
    )
  else:
    return GetServiceStatusResponse(
      isCompleted=True,
      id=service_id_num,
      status=service.status,
      areas=None
    )
  
@router.patch(
  "/area/{service_id}/{area_id}", 
  summary="텍스트 영역의 원본 텍스트 수정", 
  description=
    f"""
      ID와 일치하는 영역의 원본 텍스트를 수정합니다.
    """,
  status_code=status.HTTP_201_CREATED,
  responses=patch_area_origin_text_response(),
  response_model=AreaReadAfterDetecting
)
async def patch_area_origin_text(service_id: str, area_id: str, request: PatchAreaOriginTextRequest, db: AsyncSession = Depends(get_db)):
  service_id_num = int(service_id)
  area_id_num = int(area_id)

  # 0. 유효성 검사
  if len(request.newOriginText) == 0 :
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="newOriginText가 비어 있습니다.")
  
  # 1. 영역 및 서비스 조회
  service = await read_service_by_id(db, service_id_num)
  if not service:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 서비스입니다.")
  if service.step != ServiceStep.DETECTING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"DETECTING(OCR) 단계가 아닌 서비스입니다.")
  if service.status != ServiceStatus.PENDING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"OCR 동작이 진행 중인 서비스입니다.")

  area = await read_area_by_id(db, area_id_num)
  if not area:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 영역입니다.")
  if area.service_id != service_id_num:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"해당 서비스에 할당된 영역이 아닙니다.")
  
  # 2. 영역의 원본 텍스트 수정
  patched_area = await update_area(db, AreaUpdate(
    id=area_id_num,
    origin_text=request.newOriginText
  ))

  return AreaReadAfterDetecting(
    id=patched_area.id,
    created_at=patched_area.created_at,
    service_id=patched_area.service_id,
    x1=patched_area.x1,
    x2=patched_area.x2,
    y1=patched_area.y1,
    y2=patched_area.y2,
    origin_text=patched_area.origin_text or "error"
  )

@router.delete(
  "/area/{service_id}/{area_id}", 
  summary="텍스트 영역 삭제", 
  description=
    f"""
      ID와 일치하는 영역을 삭제합니다.
    """,
  status_code=status.HTTP_204_NO_CONTENT,
  responses=delete_area_response()
)
async def delete_area(service_id: str, area_id: str, db: AsyncSession = Depends(get_db)):
  service_id_num = int(service_id)
  area_id_num = int(area_id)
  
  # 1. 영역 및 서비스 조회
  service = await read_service_by_id(db, service_id_num)
  if not service:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 서비스입니다.")
  if service.step != ServiceStep.DETECTING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"DETECTING(OCR) 단계가 아닌 서비스입니다.")
  if service.status != ServiceStatus.PENDING:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"OCR 동작이 진행 중인 서비스입니다.")

  area = await read_area_by_id(db, area_id_num)
  if not area:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 영역입니다.")
  if area.service_id != service_id_num:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"해당 서비스에 할당된 영역이 아닙니다.")
  

  await delete_area_by_id(db, area_id_num)

  return