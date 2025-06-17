"""
File Routes - Complete Working Implementation for SyncAI
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
import shutil
import uuid

logger = logging.getLogger("file_routes")
router = APIRouter(prefix="/files", tags=["files"])

# Global upload directory
_upload_dir = "./uploads"
_max_file_size = 10 * 1024 * 1024  # 10MB
_allowed_extensions = {".txt", ".md", ".yaml", ".yml", ".json", ".py", ".pdf", ".docx"}

def set_upload_dir(upload_dir: str):
    """Set upload directory"""
    global _upload_dir
    _upload_dir = upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    logger.info(f"📁 Upload directory set to: {upload_dir}")

def get_upload_dir() -> str:
    """Get current upload directory"""
    return _upload_dir

def _format_file_size(size: int) -> str:
    """Formats bytes into human readable string"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

class FileInfo(BaseModel):
    filename: str
    size: int
    upload_time: str
    file_type: str
    file_id: str

class FileListResponse(BaseModel):
    files: List[FileInfo]
    total_count: int
    upload_dir: str
    timestamp: str

@router.get("/status")
async def get_files_status():
    """Get file service status"""
    try:
        upload_path = Path(_upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)
        total_files = 0
        total_size = 0
        if upload_path.exists():
            for file_path in upload_path.iterdir():
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size
        return {
            "status": "operational",
            "service": "SyncAI Files",
            "upload_dir": str(upload_path.absolute()),
            "upload_dir_exists": upload_path.exists(),
            "upload_dir_writable": os.access(upload_path, os.W_OK) if upload_path.exists() else False,
            "total_files": total_files,
            "total_size_bytes": total_size,
            "max_file_size_bytes": _max_file_size,
            "allowed_extensions": list(_allowed_extensions),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get file status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file status: {str(e)}"
        )

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file to the server"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in _allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_ext}' not allowed. Allowed types: {list(_allowed_extensions)}"
            )
        content = await file.read()
        if len(content) > _max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {_max_file_size / 1024 / 1024:.1f}MB"
            )
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{file.filename}"
        file_path = Path(_upload_dir) / safe_filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"📁 File uploaded: {file.filename} -> {safe_filename}")
        return {
            "success": True,
            "message": "File uploaded successfully",
            "file_info": {
                "original_filename": file.filename,
                "stored_filename": safe_filename,
                "file_id": file_id,
                "size_bytes": len(content),
                "file_type": file_ext,
                "upload_time": datetime.utcnow().isoformat(),
                "file_path": str(file_path)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"File upload failed: {str(e)}"
        )

@router.get("/list")
async def list_files(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
) -> FileListResponse:
    """List uploaded files"""
    try:
        upload_path = Path(_upload_dir)
        if not upload_path.exists():
            return FileListResponse(
                files=[],
                total_count=0,
                upload_dir=str(upload_path),
                timestamp=datetime.utcnow().isoformat()
            )
        all_files = []
        for file_path in upload_path.iterdir():
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    filename_parts = file_path.name.split('_', 1)
                    file_id = filename_parts[0] if len(filename_parts) > 1 else str(uuid.uuid4())
                    file_info = FileInfo(
                        filename=file_path.name,
                        size=stat.st_size,
                        upload_time=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        file_type=file_path.suffix.lower(),
                        file_id=file_id
                    )
                    all_files.append(file_info)
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
                    continue
        all_files.sort(key=lambda x: x.upload_time, reverse=True)
        paginated_files = all_files[offset:offset + limit]
        return FileListResponse(
            files=paginated_files,
            total_count=len(all_files),
            upload_dir=str(upload_path.absolute()),
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list files: {str(e)}"
        )

@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download a file"""
    try:
        file_path = Path(_upload_dir) / filename
        # Security check - ensure file is within upload directory
        if not str(file_path.resolve()).startswith(str(Path(_upload_dir).resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Not a file")
        display_name = filename
        if '_' in filename:
            parts = filename.split('_', 1)
            if len(parts) > 1:
                display_name = parts[1]
        return FileResponse(
            path=str(file_path),
            filename=display_name,
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download failed for {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"File download failed: {str(e)}"
        )

@router.delete("/delete/{filename}")
async def delete_file(filename: str):
    """Delete a file"""
    try:
        file_path = Path(_upload_dir) / filename
        if not str(file_path.resolve()).startswith(str(Path(_upload_dir).resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Not a file")
        stat = file_path.stat()
        file_size = stat.st_size
        file_path.unlink()
        logger.info(f"🗑️ File deleted: {filename}")
        return {
            "success": True,
            "message": "File deleted successfully",
            "deleted_file": {
                "filename": filename,
                "size_bytes": file_size,
                "deleted_at": datetime.utcnow().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion failed for {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"File deletion failed: {str(e)}"
        )

@router.get("/info/{filename}")
async def get_file_info(filename: str):
    """Get detailed information about a file"""
    try:
        file_path = Path(_upload_dir) / filename
        if not str(file_path.resolve()).startswith(str(Path(_upload_dir).resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Not a file")
        stat = file_path.stat()
        filename_parts = filename.split('_', 1)
        file_id = filename_parts[0] if len(filename_parts) > 1 else "unknown"
        original_name = filename_parts[1] if len(filename_parts) > 1 else filename
        return {
            "filename": filename,
            "original_filename": original_name,
            "file_id": file_id,
            "size_bytes": stat.st_size,
            "size_human": _format_file_size(stat.st_size),
            "file_type": file_path.suffix.lower(),
            "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed_time": datetime.fromtimestamp(stat.st_atime).isoformat(),
            "absolute_path": str(file_path.absolute()),
            "is_readable": os.access(file_path, os.R_OK),
            "is_writable": os.access(file_path, os.W_OK)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file info for {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file info: {str(e)}"
        )

@router.post("/cleanup")
async def cleanup_files(
    older_than_days: int = Query(default=30, ge=1, le=365),
    dry_run: bool = Query(default=True)
):
    """Cleanup old files"""
    try:
        upload_path = Path(_upload_dir)
        if not upload_path.exists():
            return {
                "message": "Upload directory does not exist",
                "files_processed": 0,
                "files_deleted": 0
            }
        import time
        cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
        files_to_delete = []
        total_size = 0
        for file_path in upload_path.iterdir():
            if file_path.is_file():
                if file_path.stat().st_mtime < cutoff_time:
                    file_size = file_path.stat().st_size
                    files_to_delete.append({
                        "filename": file_path.name,
                        "size_bytes": file_size,
                        "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
                    total_size += file_size
        files_deleted = 0
        if not dry_run:
            for f in files_to_delete:
                target_path = upload_path / f["filename"]
                try:
                    target_path.unlink()
                    files_deleted += 1
                except Exception as e:
                    logger.warning(f"Could not delete file {f['filename']}: {e}")
        return {
            "message": "Cleanup completed" if not dry_run else "Dry run completed",
            "files_processed": len(files_to_delete),
            "files_deleted": files_deleted if not dry_run else 0,
            "total_size_bytes": total_size,
            "dry_run": dry_run,
            "files": files_to_delete,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to cleanup files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup files: {str(e)}"
        )
