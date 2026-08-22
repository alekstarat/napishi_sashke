from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app.services.file import FileService

router = APIRouter(
    prefix="/files",
    tags=["files"],
)

file_service = FileService()


@router.post("/")
async def upload_file(
    request: Request,
) -> dict[str, str]:
    data = await request.body()

    file_id = file_service.save(data)

    return {
        "file_id": file_id,
    }


@router.get("/{file_id}")
async def download_file(
    file_id: str,
) -> Response:
    try:
        data = file_service.load(file_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return Response(
        content=data,
        media_type="application/octet-stream",
    )