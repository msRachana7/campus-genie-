import os
from uuid import uuid4
import hashlib
import requests
from dotenv import load_dotenv
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from database import get_connection
from services.gemini_validator import check_resource_relevance

load_dotenv()

router = APIRouter(
    prefix="/api/resources",
    tags=["Resources"]
)

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
VOLUME_PATH = os.getenv(
    "DATABRICKS_VOLUME_PATH",
    "/Volumes/workspace/default/campus_genie_data"
)


@router.post("/upload")
def upload_resource(
    student_id: str = Form(...),
    title: str = Form(...),
    resource_type: str = Form(...),
    subject: str = Form(...),
    semester: int = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    file: UploadFile = File(...)
):
    conn = None
    volume_file_path = None

    try:
        # -----------------------------------------
        # 1. Validate Databricks configuration
        # -----------------------------------------
        if not DATABRICKS_HOST:
            raise HTTPException(
                status_code=500,
                detail="DATABRICKS_HOST is missing"
            )

        if not DATABRICKS_TOKEN:
            raise HTTPException(
                status_code=500,
                detail="DATABRICKS_TOKEN is missing"
            )

        if not VOLUME_PATH:
            raise HTTPException(
                status_code=500,
                detail="DATABRICKS_VOLUME_PATH is missing"
            )

        # -----------------------------------------
        # 2. Connect to Lakebase
        # -----------------------------------------
        conn = get_connection()

        with conn.cursor() as cur:

            # -----------------------------------------
            # 3. Find student's user_id
            # -----------------------------------------
            cur.execute(
                """
                SELECT user_id
                FROM student_public
                WHERE student_id = %s
                """,
                (student_id,)
            )

            student = cur.fetchone()

            if student is None:
                raise HTTPException(
                    status_code=404,
                    detail="Student not found"
                )

            user_id = student[0]

            # -----------------------------------------
            # 4. Clean filename
            # -----------------------------------------
            safe_filename = os.path.basename(
                file.filename or ""
            )

            if not safe_filename:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid filename"
                )

            # -----------------------------------------
            # 5. Read uploaded file
            # -----------------------------------------
            file_content = file.file.read()

            if not file_content:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded file is empty"
                )

            # -----------------------------------------
            # 6. Generate SHA-256 hash
            # -----------------------------------------
            file_hash = hashlib.sha256(
                file_content
            ).hexdigest()

            # -----------------------------------------
            # 7. Check for exact duplicate
            # -----------------------------------------
            cur.execute(
                """
                SELECT resource_id, title, filename
                FROM resources
                WHERE file_hash = %s
                LIMIT 1
                """,
                (file_hash,)
            )

            existing = cur.fetchone()

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "This file has already been uploaded.",
                        "existing_resource_id": str(existing[0]),
                        "existing_title": existing[1],
                        "existing_filename": existing[2]
                    }
                )

            # -----------------------------------------
            # 8. Gemini relevance validation
            # -----------------------------------------
            try:
                validation = check_resource_relevance(
                    file_content=file_content,
                    title=title,
                    subject=subject,
                    resource_type=resource_type,
                    description=description,
                    tags=tags
                )

            except Exception as e:
                print(
                    "GEMINI VALIDATION ERROR:",
                    repr(e)
                )

                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Unable to validate the resource right now. "
                        "Please try again."
                    )
                )

            # -----------------------------------------
            # 9. Reject irrelevant resource
            # -----------------------------------------
            if not validation["relevant"]:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "message": (
                            "The uploaded file does not appear "
                            "to match the provided resource information."
                        ),
                        "reason": validation["reason"],
                        "confidence": validation["confidence"]
                    }
                )

            # -----------------------------------------
            # 10. Generate resource ID
            # -----------------------------------------
            resource_id = uuid4()

            # -----------------------------------------
            # 11. Create Volume directory path
            # -----------------------------------------
            volume_directory = (
                f"{VOLUME_PATH.rstrip('/')}/resources"
            )

            volume_file_path = (
                f"{volume_directory}/"
                f"{resource_id}_{safe_filename}"
            )

            # -----------------------------------------
            # 12. Upload actual file to Volume
            # -----------------------------------------
            upload_url = (
                f"{DATABRICKS_HOST.rstrip('/')}"
                f"/api/2.0/fs/files"
                f"{volume_file_path}"
            )

            print(
                "Uploading resource to Volume:",
                volume_file_path
            )

            response = requests.put(
                upload_url,
                headers={
                    "Authorization": (
                        f"Bearer {DATABRICKS_TOKEN}"
                    ),
                    "Content-Type": (
                        "application/octet-stream"
                    )
                },
                data=file_content,
                timeout=120
            )

            # Databricks Files API returns 204 on success
            if response.status_code != 204:
                print(
                    "DATABRICKS UPLOAD FAILED:",
                    response.status_code,
                    response.text
                )

                raise Exception(
                    "Databricks Volume upload failed: "
                    f"{response.status_code} "
                    f"{response.text}"
                )

            print(
                "FILE SUCCESSFULLY UPLOADED TO VOLUME:",
                volume_file_path
            )

            # -----------------------------------------
            # 13. Save ONLY metadata in Lakebase
            # -----------------------------------------
            cur.execute(
                """
                INSERT INTO resources
                (
                    resource_id,
                    user_id,
                    title,
                    filename,
                    resource_type,
                    subject,
                    semester,
                    file_path,
                    file_hash
                )
                VALUES
                (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                """,
                (
                    resource_id,
                    user_id,
                    title,
                    safe_filename,
                    resource_type,
                    subject,
                    semester,
                    volume_file_path,
                    file_hash
                )
            )

        # -----------------------------------------
        # 14. Commit Lakebase transaction
        # -----------------------------------------
        conn.commit()

        # -----------------------------------------
        # 15. Return response
        # -----------------------------------------
        return {
            "message": "Resource uploaded successfully",
            "resource_id": str(resource_id),
            "filename": safe_filename,
            "file_path": volume_file_path,
            "storage": "Databricks Volume",
            "metadata_storage": "Lakebase",
            "validation": {
                "relevant": validation["relevant"],
                "confidence": validation["confidence"],
                "reason": validation["reason"]
            }
        }

    except HTTPException:
        if conn:
            conn.rollback()
        raise

    except Exception as e:

        if conn:
            conn.rollback()

        # -----------------------------------------
        # Cleanup Volume file if Lakebase insertion fails
        # -----------------------------------------
        if (
            volume_file_path
            and DATABRICKS_HOST
            and DATABRICKS_TOKEN
        ):
            try:
                delete_url = (
                    f"{DATABRICKS_HOST.rstrip('/')}"
                    f"/api/2.0/fs/files"
                    f"{volume_file_path}"
                )

                delete_response = requests.delete(
                    delete_url,
                    headers={
                        "Authorization": (
                            f"Bearer {DATABRICKS_TOKEN}"
                        )
                    },
                    timeout=30
                )

                print(
                    "VOLUME CLEANUP STATUS:",
                    delete_response.status_code
                )

            except Exception as cleanup_error:
                print(
                    "DATABRICKS CLEANUP ERROR:",
                    repr(cleanup_error)
                )

        print(
            "RESOURCE UPLOAD ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if conn:
            conn.close()