"""
文件管理API路由
包括上传附件、下载附件等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO
from urllib.parse import quote

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.services.file_service import FileService


def _build_content_disposition(file_name: str) -> str:
    """
    构造兼容中文文件名的 Content-Disposition (RFC 5987)
    HTTP header 需 latin-1 编码，中文文件名必须走 filename*=UTF-8''<urlencode>
    """
    quoted = quote(file_name, safe='')
    # ASCII fallback (过滤不可表达为 latin-1 的字符)
    fallback = file_name.encode('ascii', errors='ignore').decode('ascii') or 'download'
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quoted}"


router = APIRouter(prefix="/api", tags=["文件"])
file_service = FileService()


@router.post("/contracts/{contract_id}/attachments")
async def upload_attachment(
    contract_id: str,
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    上传附件
    
    Args:
        contract_id: 合同ID
        request: FastAPI请求对象
        file: 上传的文件
        db: 数据库会话
        
    Returns:
        附件信息
    """
    try:
        # 获取当前用户
        current_user = get_current_user(request)
        
        # 上传文件
        attachment = await file_service.upload_file(
            contract_id=contract_id,
            uploader_id=current_user["user_id"],
            file=file,
            db=db
        )
        
        return {
            "success": True,
            "data": {
                "attachment": {
                    "id": attachment.id,
                    "file_name": attachment.file_name,
                    "version": attachment.version,
                    "file_size": attachment.file_size,
                    "mime_type": attachment.mime_type,
                    "created_at": attachment.created_at.isoformat()
                }
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"上传附件失败: {str(e)}"
        )


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    下载附件 (重定向到MinIO预签名URL)
    
    Args:
        attachment_id: 附件ID
        request: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        重定向到MinIO预签名URL
    """
    try:
        # 获取当前用户
        current_user = get_current_user(request)
        
        # 验证权限
        has_permission = await file_service.verify_access_permission(
            attachment_id=attachment_id,
            user_id=current_user["user_id"],
            db=db
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail="您没有权限下载此文件"
            )
        
        # 获取附件信息
        attachment = await file_service.get_attachment(attachment_id, db)
        
        if not attachment:
            raise HTTPException(
                status_code=404,
                detail="附件不存在"
            )
        
        # 生成下载URL
        download_url = file_service.generate_download_url(
            storage_key=attachment.storage_key,
            expires=3600  # 1小时有效期
        )
        
        # 重定向到MinIO预签名URL
        return RedirectResponse(url=download_url)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"下载附件失败: {str(e)}"
        )


@router.get("/attachments/{attachment_id}/stream")
async def stream_attachment(
    attachment_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    以文件流方式下载附件 (直接通过后端返回文件流)
    
    Args:
        attachment_id: 附件ID
        request: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        文件流响应
    """
    try:
        # 获取当前用户
        current_user = get_current_user(request)
        
        # 验证权限
        has_permission = await file_service.verify_access_permission(
            attachment_id=attachment_id,
            user_id=current_user["user_id"],
            db=db
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail="您没有权限下载此文件"
            )
        
        # 获取附件信息
        attachment = await file_service.get_attachment(attachment_id, db)
        
        if not attachment:
            raise HTTPException(
                status_code=404,
                detail="附件不存在"
            )
        
        # 下载文件流
        file_data = file_service.download_file_stream(
            storage_key=attachment.storage_key
        )
        
        # 返回文件流
        return StreamingResponse(
            BytesIO(file_data),
            media_type=attachment.mime_type,
            headers={
                "Content-Disposition": _build_content_disposition(attachment.file_name),
                "Content-Length": str(attachment.file_size)
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"下载附件失败: {str(e)}"
        )


@router.get("/attachments/{attachment_id}")
async def get_attachment_info(
    attachment_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    获取附件信息
    
    Args:
        attachment_id: 附件ID
        request: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        附件详细信息
    """
    try:
        # 获取当前用户
        current_user = get_current_user(request)
        
        # 验证权限
        has_permission = await file_service.verify_access_permission(
            attachment_id=attachment_id,
            user_id=current_user["user_id"],
            db=db
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail="您没有权限访问此文件"
            )
        
        # 获取附件信息
        attachment = await file_service.get_attachment(attachment_id, db)
        
        if not attachment:
            raise HTTPException(
                status_code=404,
                detail="附件不存在"
            )
        
        return {
            "success": True,
            "data": {
                "attachment": {
                    "id": attachment.id,
                    "file_name": attachment.file_name,
                    "version": attachment.version,
                    "file_size": attachment.file_size,
                    "mime_type": attachment.mime_type,
                    "storage_key": attachment.storage_key,
                    "uploader_id": attachment.uploader_id,
                    "created_at": attachment.created_at.isoformat()
                }
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取附件信息失败: {str(e)}"
        )
