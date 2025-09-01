# pyright: reportUnknownMemberType=false, reportAttributeAccessIssue=false, reportUnknownVariableType=false

import asyncio
from app.celery_app import celery
from typing import TypedDict
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.constants.database_url import DATABASE_URL
from app.crud.area import read_areas_bulk_by_service_id
from app.crud.image import create_image, read_image_by_id
from app.crud.service import read_service_by_id, update_service
from app.models.enums.service import ServiceMode, ServiceStatus, ServiceStep
from app.schemas.image import ImageCreate
from app.schemas.service import ServiceRead, ServiceUpdate

from PIL import ImageDraw, ImageFont

from app.utils.storage import build_storage
##### --- for ssh connect --- #####
import os
import time
import json
import shlex
import tempfile
from dataclasses import dataclass
import secrets  # NEW

import paramiko
from PIL import Image

from app.utils.ssh_keys import ensure_ed25519_key
###################################

##### --- SSH/FastAPI 설정 --- #####
# 무조건 무조건 반드시 env로 옮긴 후, commit할 것 -> 완료
@dataclass
class SSHConfig:
    host: str = os.getenv("GPU_HOST")
    port: int = int(os.getenv("GPU_PORT"))
    user: str = os.getenv("GPU_USER")
    key_path, pub_path = ensure_ed25519_key(os.getenv("GPU_KEY_PATH")) # ssh 키없을시 생성, 하지만 한 번 생성하면 굳이긴 한데 일단 코드 바뀔수도 있으니 유지
    # 원격 입출력 폴더 (GPU 서버의 실제 파일시스템 경로) 여기부터
    remote_in_dir: str = os.getenv("GPU_REMOTE_IN")
    remote_out_dir: str = os.getenv("GPU_REMOTE_OUT")
    # GPU 서버에서 돌아가는 FastAPI의 로컬 주소(원격 호스트 기준)
    fastapi_infer_url: str = os.getenv("GPU_FASTAPI_URL")

    # NEW: 스크립트 경로 & 환경 준비 커맨드
    remote_script: str = os.getenv("GPU_REMOTE_SCRIPT")
    remote_preamble: str = os.getenv("GPU_REMOTE_PREAMBLE")

CFG = SSHConfig()

def _open_ssh_client(cfg: SSHConfig) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 내부망/테스트용
    client.connect(
        hostname=cfg.host,
        port=cfg.port,
        username=cfg.user,
        key_filename=os.path.expanduser(cfg.key_path),
        allow_agent=True,
        look_for_keys=True,
        timeout=30,
    )
    return client

def _sftp_mkdir_p(sftp: paramiko.SFTPClient, path: str) -> None:
    # SFTP에는 -p가 없어서 재귀 생성
    parts = [p for p in path.split("/") if p]
    cur = "/"
    for p in parts:
        cur = os.path.join(cur, p)
        try:
            sftp.stat(cur)
        except IOError:
            sftp.mkdir(cur)

###################################

# --- 워커 전용 세션팩토리 ---
_engine = create_async_engine(DATABASE_URL, future=True)
SessionLocal = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)

storage = build_storage()

def get_resized_font(
  text: str,
  max_width: int,
  max_height: int,
  font_path: str,
  min_font_size: int = 5,
  max_font_size: int = 100
) -> ImageFont.FreeTypeFont:
  """
  텍스트가 max_width와 max_height 안에 최대한 꽉 차도록 폰트 크기를 조절.
  """
  best_font = ImageFont.truetype(font_path, min_font_size)
  for font_size in range(min_font_size, max_font_size + 1):
      font = ImageFont.truetype(font_path, font_size)
      bbox = font.getbbox(text)
      text_width = bbox[2] - bbox[0]
      text_height = bbox[3] - bbox[1]

      if text_width > max_width or text_height > max_height:
          # 넘었으면 이전 크기로 반환
          return best_font
      best_font = font

  return best_font

async def compose_image_machine_mode(db: AsyncSession, service: ServiceRead) -> None:
  origin_image_read = await read_image_by_id(db, service.origin_image_id)

  if not origin_image_read:
    raise Exception("id와 일치하는 image를 찾을 수 없습니다.")
  
  imageFile = storage.load_image(origin_image_read.filename, "upload")
  draw = ImageDraw.Draw(imageFile)
  
  areas = await read_areas_bulk_by_service_id(db, service.id)
  
  for area in areas:
    draw.rectangle([(area.x1, area.y1), (area.x2, area.y2)], fill="white")
    text = area.translated_text or "error"

    box_width = area.x2 - area.x1
    box_height = area.y2 - area.y1
    font = get_resized_font(text, box_width - 10, box_height - 10, './font/PretendardJP-Regular.ttf')

    text_position = (area.x1 + 5, area.y1 + 5)
    draw.text(text_position, text, fill="black", font=font)
  
  composed_filename = f"composed_{origin_image_read.filename}"
  storage.save_png(imageFile, composed_filename, target="compose")

  created_image = await create_image(db, image_in=ImageCreate(filename=composed_filename))
  service_in = ServiceUpdate(composed_image_id=created_image.id)
  await update_service(db, service.id, service_in=service_in)


##### --------- SSH --------- #####
async def compose_image_ai_mode(db: AsyncSession, service: ServiceRead) -> None:
    """
    1) 원본 이미지를 임시파일로 저장
    2) Paramiko로 GPU 서버에 업로드
    3) SSH exec_command로 FastAPI /infer 호출(curl)
    4) 결과물 다운로드
    5) compose 스토리지에 저장 + DB 업데이트
    """
    origin_image = await read_image_by_id(db, service.origin_image_id)
    if not origin_image:
        raise Exception("id와 일치하는 image를 찾을 수 없습니다.")

    # 1-1) 원본 이미지를 임시 파일로 저장
    pil_img = storage.load_image(origin_image.filename, "upload")
    if pil_img.mode != "RGBA":
        pil_img = pil_img.convert("RGBA")

    # 1-2) 작업들 이름 충돌 방지용으로 랜덤 한스푼
    job_id = f"svc{service.id}_{int(time.time())}_{secrets.token_hex(4)}"
    local_in = os.path.join(tempfile.gettempdir(), f"{job_id}_in.png")
    pil_img.save(local_in, format="PNG")

    # 2-1) 원격 작업 전용 경로 세팅(지금 gpu서버엔 ssh_input, ssh_output으로 되어있음)
    remote_job_dir = f"{CFG.remote_in_dir}/{job_id}"
    remote_in = f"{remote_job_dir}/input.png"
    remote_job_json = f"{remote_job_dir}/job.json"
    remote_out_root = CFG.remote_out_dir  # 결과 루트 (스크립트가 out_root/<job_id>/... 생성)
    remote_script = "/home/undergrad/model_base/TextCtrl-Translate/infer.sh"

    # 2-2) DB의 areas도 세팅
    areas = await read_areas_bulk_by_service_id(db, service.id)

    # 2-3) 데이터 종합한 meta만들고, 보낼 준비 끗
    job_meta = {
        "job_id": job_id,
        "input_path": remote_in,
        "out_root": remote_out_root,
        "naming": {"digits": 5, "start": 0},
        "areas": [
            {
                "bbox": [a.x1, a.y1, a.x2, a.y2],
                # 예시 규칙: i_s.txt = source_text(원문), i_t.txt = target_text(번역)
                "source_text": (getattr(a, "text", None) or getattr(a, "origin_text", None) or ""),
                "target_text": (a.translated_text or ""),
            }
            for a in areas
        ],
    }
    job_meta_str = json.dumps(job_meta, ensure_ascii=False)

    # 3) ssh통신 함수 
    def _do_ssh_roundtrip() -> dict:
      client = _open_ssh_client(CFG)
      sftp = client.open_sftp()
      try:
          _sftp_mkdir_p(sftp, remote_job_dir)
          _sftp_mkdir_p(sftp, CFG.remote_out_dir)
          sftp.put(local_in, remote_in)
          with sftp.open(remote_job_json, "w", bufsize=32768) as f:
              f.write(job_meta_str)

          base_cmd = f"{shlex.quote(remote_script)} --job {shlex.quote(remote_job_json)}"
          gpu_sel  = "CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=7"  # <- 원하는 GPU 선택, 현재는 7번으로 해놓음
          full_cmd = f"{gpu_sel} {base_cmd}"
          cmd = f"bash -lc {shlex.quote(full_cmd)}"

          stdin, stdout, stderr = client.exec_command(cmd, timeout=3600, get_pty=True)
          out_txt = stdout.read().decode("utf-8", "ignore")
          err_txt = stderr.read().decode("utf-8", "ignore")
          rc = stdout.channel.recv_exit_status()
          if rc != 0:
              raise RuntimeError(f"Remote failed (rc={rc})\nSTDOUT:\n{out_txt}\nSTDERR:\n{err_txt}")

          # 결과물 다운로드
          remote_composed = f"{remote_out_root}/{job_id}/all_result/composed.png"
          local_composed  = os.path.join(tempfile.gettempdir(), f"{job_id}_composed.png")
          sftp.get(remote_composed, local_composed)

          return local_composed
      finally:
          try: sftp.close()
          except: pass
          client.close()

    # Paramiko는 블로킹[동기]이므로 따로 스레드로 빼서, 현재거 안막히게 해줬으나, 어짜피 selary에 들어가 있는거라면 상관없을 것 같아서 동기 그대로 실행
    # 동훈) 맞아유, 여긴 샐러리 태스크 안에 있기 때문에, 현재 태스크 자체가 메인(fastAPI) 프로세스랑 따로 분리되어서 실행중인 프로세스임니다
    local_composed = _do_ssh_roundtrip()

    # 4) compose 스토리지에 저장 + DB 업데이트
    result_img = Image.open(local_composed)
    composed_filename = f"composed_{origin_image.filename}"
    storage.save_png(result_img, composed_filename, target="compose")

    created_image = await create_image(db, image_in=ImageCreate(filename=composed_filename))
    service_in = ServiceUpdate(composed_image_id=created_image.id)
    await update_service(db, service.id, service_in=service_in)
###################################

class ComposePayload(TypedDict):
  service_id: int

@celery.task
def compose_image(payload: ComposePayload) -> bool:
    """Celery 워커에서 실행되는 동기 엔트리. 내부에서 async 실행."""
    async def _run() -> bool:
      async with SessionLocal() as db:
        service = await read_service_by_id(db, payload["service_id"])
        if not service:
          raise Exception("id와 일치하는 service를 찾을 수 없습니다.")
        
        if service.mode == ServiceMode.AI:
          await compose_image_ai_mode(db, service)
        else:
          await compose_image_machine_mode(db, service)
          
        service_in = ServiceUpdate(step=ServiceStep.COMPOSING, status=ServiceStatus.COMPLETED)
        await update_service(db, service.id, service_in)

      return True

    return asyncio.run(_run())