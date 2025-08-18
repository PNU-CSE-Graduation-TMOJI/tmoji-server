from __future__ import annotations
import os
from io import BytesIO
from pathlib import Path
from typing import Literal, Optional, Protocol

from fastapi.responses import FileResponse, RedirectResponse, Response
from PIL import Image as PILImage

from app.constants.image_path import COMPOSE_DIR, CROP_DIR, IMAGE_BASE_DIR, UPLOAD_DIR

Target = Literal["upload", "compose", "crop"]

class BaseStorage(Protocol):
    def save_png(self, img: PILImage.Image, filename: str, target: Target = "upload") -> None: ...
    def get_image_response(self, filename: str, target: Target) -> Response: ...
    def load_image(self, filename: str, target: Target = "upload") -> PILImage.Image: ...

# ---------------- Local ----------------
class LocalStorage:
    def __init__(self, image_base_dir: str, upload_dir: str, compose_dir: str, crop_dir: str):
        self.image_base_dir = Path(image_base_dir).resolve()
        self.image_base_dir.mkdir(parents=True, exist_ok=True)

        self.upload_folder = Path(upload_dir)
        self.compose_folder = Path(compose_dir)
        self.crop_folder = Path(crop_dir)

        self.upload_dir = self.image_base_dir / self.upload_folder
        self.compose_dir = self.image_base_dir / self.compose_folder
        self.crop_dir = self.image_base_dir / self.crop_folder

        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.compose_dir.mkdir(parents=True, exist_ok=True)
        self.crop_dir.mkdir(parents=True, exist_ok=True)
    
    def get_path(self, target: Target) -> Path:
        base = self.compose_dir
        if target == "upload": base = self.upload_dir
        if target == "crop": base = self.crop_dir
    
        return base

    def _safe_path(self, base: Path, filename: str) -> Path:
        name = Path(filename).name  # 경로 탐색 방지
        p = (base / name).resolve()
        if not str(p).startswith(str(base)):
            raise ValueError("잘못된 경로")
        return p

    def save_png(self, img: PILImage.Image, filename: str, target: Target = "upload") -> None:
        base = self.get_path(target)
        path = self._safe_path(base, filename)
        img.save(path, format="PNG")

    def get_image_response(self, filename: str, target: Target) -> Response:
        base = self.get_path(target)
        path = self._safe_path(base, filename)
        if not path.exists():
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        headers = {"Content-Disposition": f'inline; filename="{Path(filename).name}"'}
        return FileResponse(str(path), media_type="image/png", headers=headers)
    
    def load_image(self, filename: str, target: Target = "upload") -> PILImage.Image:
        """로컬 디스크에서 PIL 이미지 로드(RGBA로 변환)."""
        base = self.get_path(target)
        path = self._safe_path(base, filename)
        if not path.exists():
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        try:
            return PILImage.open(path).convert("RGBA")
        except Exception:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail="이미지 로드 실패")

# ---------------- S3 ----------------
class S3Storage:
    def __init__(
        self,
        bucket: str,
        region: str,
        upload_prefix: str = "upload",
        compose_prefix: str = "compose",
        crop_prefix: str = "crop",
        presign_expires: int = 3600,
        endpoint_url: Optional[str] = None,
    ):
        # boto3는 s3 모드에서만 필요하도록 지연 임포트
        import boto3 # pyright: ignore[reportMissingTypeStubs]
        from botocore.config import Config # pyright: ignore[reportMissingTypeStubs]

        self.bucket = bucket
        self.upload_prefix = upload_prefix.strip("/")
        self.compose_prefix = compose_prefix.strip("/")
        self.crop_prefix = crop_prefix.strip("/")
        self.expires = presign_expires
        self.s3 = boto3.client( # pyright: ignore[reportUnknownMemberType]
            "s3",
            region_name=region,
            endpoint_url=endpoint_url,
            config=Config(signature_version="s3v4"),
        )

    def _key(self, target: Target, filename: str) -> str:
        name = Path(filename).name
        prefix = self.compose_prefix
        if target == "upload": prefix = self.upload_prefix
        if target == "crop": prefix = self.crop_prefix
        return f"{prefix}/{name}"

    def save_png(self, img: PILImage.Image, filename: str, target: Target = "upload") -> None:
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        key = self._key(target, filename)
        self.s3.put_object( # pyright: ignore[reportUnknownMemberType]
            Bucket=self.bucket,
            Key=key,
            Body=buf.getvalue(),
            ContentType="image/png",
        )

    def get_image_response(self, filename: str, target: Target) -> Response:
        key = self._key(target, filename)
        # 존재 확인(선택)
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key) # pyright: ignore[reportUnknownMemberType]
        except Exception:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

        params = {
            "Bucket": self.bucket,
            "Key": key,
            "ResponseContentType": "image/png",
            "ResponseContentDisposition": f'inline; filename="{Path(filename).name}"',
        }
        url = self.s3.generate_presigned_url("get_object", Params=params, ExpiresIn=self.expires) # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        return RedirectResponse(url, status_code=307) # pyright: ignore[reportUnknownArgumentType]
    
    def load_image(self, filename: str, target: Target = "upload") -> PILImage.Image:
        """S3에서 객체를 받아 PIL 이미지 로드(RGBA로 변환)."""
        key = self._key(target, filename)
        try:
            obj = self.s3.get_object(Bucket=self.bucket, Key=key) # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
            body = obj["Body"].read() # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
            return PILImage.open(BytesIO(body)).convert("RGBA") # pyright: ignore[reportUnknownArgumentType]
        except self.s3.exceptions.NoSuchKey: # pyright: ignore[reportUnknownMemberType]
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        except Exception:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail="이미지 로드 실패")

# --------------- Factory ----------------
def build_storage() -> BaseStorage:
    backend = os.getenv("ENV_MODE", "local").lower()
    if backend == "prod":
        bucket = os.getenv("S3_BUCKET_NAME") or ""
        region = os.getenv("AWS_REGION") or ""
        expires = int(os.getenv("S3_PRESIGN_EXPIRES") or "3600")
        endpoint = os.getenv("S3_ENDPOINT_URL") or None
        if not bucket:
            raise RuntimeError("S3_BUCKET_NAME is required when STORAGE_BACKEND=s3")
        return S3Storage(
            bucket=bucket,
            region=region,
            presign_expires=expires,
            endpoint_url=endpoint,
        )
    else:
        return LocalStorage(
            image_base_dir=IMAGE_BASE_DIR, 
            upload_dir=UPLOAD_DIR, 
            compose_dir=COMPOSE_DIR, 
            crop_dir=CROP_DIR
        )
