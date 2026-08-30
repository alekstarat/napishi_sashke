from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app.container import security_service
from app.services.file import FileService

router = APIRouter(
    prefix="/files",
    tags=["files"],
)

file_service = FileService()

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MiB


@router.post("/")
async def upload_file(request: Request) -> dict[str, str]:
    ip = security_service.client_ip_from_request(request)

    if security_service.is_banned(ip):
        raise HTTPException(status_code=404)

    allowed, reason = await security_service.check_can_connect(ip)
    if not allowed and "banned" in reason:
        raise HTTPException(status_code=404)

    body = await request.body()
    if len(body) > MAX_UPLOAD_BYTES:
        await security_service.report_failure(ip, reason="oversized upload")
        raise HTTPException(status_code=404)

    if not body:
        raise HTTPException(status_code=404)

    file_id = file_service.save(body)
    return {"file_id": file_id}


@router.get("/{file_id}")
async def download_file(file_id: str, request: Request) -> Response:
    ip = security_service.client_ip_from_request(request)

    if security_service.is_banned(ip):
        raise HTTPException(status_code=404)

    if not file_id or len(file_id) > 128 or "/" in file_id or "\\" in file_id or ".." in file_id:
        raise HTTPException(status_code=404)

    try:
        data = file_service.load(file_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404)

    return Response(
        content=data,
        media_type="application/octet-stream",
    )
