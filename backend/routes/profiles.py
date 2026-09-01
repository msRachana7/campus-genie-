from fastapi import APIRouter, HTTPException
from database import get_connection
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/profile",
    tags=["Profile"]
)


@router.get("/{usn}")
def get_profile(usn: str):
    conn = None

    try:
        conn = get_connection()

        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    p.user_id,
                    p.student_id,
                    p.name,
                    p.department,
                    p.year_of_study,
                    p.skills,
                    p.interests,
                    p.looking_for
                FROM student_public p
                JOIN student_private pr
                    ON p.user_id = pr.user_id
                WHERE pr.usn = %s;
            """, (usn,))

            profile = cur.fetchone()

        if profile is None:
            raise HTTPException(
                status_code=404,
                detail="Student profile not found"
            )

        return {
            "user_id": str(profile[0]),
            "student_id": profile[1],
            "name": profile[2],
            "department": profile[3],
            "year_of_study": profile[4],
            "skills": profile[5],
            "interests": profile[6],
            "looking_for": profile[7]
        }

    except HTTPException:
        raise

    except Exception as e:
        print("PROFILE ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Database error"
        )

    finally:
        if conn:
            conn.close()
class ProfileUpdate(BaseModel):
    name: str | None = None
    department: str | None = None
    year_of_study: int | None = None
    skills: list[str] | None = None
    interests: list[str] | None = None
    looking_for: list[str] | None = None


@router.put("/{student_id}")
def update_profile(student_id: str, profile: ProfileUpdate):
    conn = None

    try:
        conn = get_connection()

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE student_public
                SET
                    name = COALESCE(%s, name),
                    department = COALESCE(%s, department),
                    year_of_study = COALESCE(%s, year_of_study),
                    skills = COALESCE(%s, skills),
                    interests = COALESCE(%s, interests),
                    looking_for = COALESCE(%s, looking_for),
                    updated_at = CURRENT_TIMESTAMP
                WHERE student_id = %s
                RETURNING
                    user_id,
                    student_id,
                    name,
                    department,
                    year_of_study,
                    skills,
                    interests,
                    looking_for;
                """,
                (
                    profile.name,
                    profile.department,
                    profile.year_of_study,
                    profile.skills,
                    profile.interests,
                    profile.looking_for,
                    student_id,
                )
            )

            updated_profile = cur.fetchone()

        if updated_profile is None:
            raise HTTPException(
                status_code=404,
                detail="Student profile not found"
            )

        conn.commit()

        return {
            "message": "Profile updated successfully",
            "profile": {
                "user_id": str(updated_profile[0]),
                "student_id": updated_profile[1],
                "name": updated_profile[2],
                "department": updated_profile[3],
                "year_of_study": updated_profile[4],
                "skills": updated_profile[5],
                "interests": updated_profile[6],
                "looking_for": updated_profile[7]
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        if conn:
            conn.rollback()

        print("Database error:", e)

        raise HTTPException(
            status_code=500,
            detail="Database error"
        )

    finally:
        if conn:
            conn.close()

"""Own-profile routes: both reads and writes use the authenticated user_id."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from psycopg.rows import dict_row
from psycopg import sql
from database import get_connection
from auth_security import require_user
from auth_schema import columns, adapt_list

router = APIRouter(prefix="/api/profile", tags=["Profile"])
FIELDS = "user_id, student_id, name, department, year_of_study, skills, interests, looking_for"


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    department: str | None = Field(default=None, min_length=1, max_length=120)
    year_of_study: int | None = Field(default=None, ge=1, le=4)
    skills: list[Annotated[str, Field(min_length=1, max_length=120)]] | None = Field(default=None, max_length=100)
    interests: list[Annotated[str, Field(min_length=1, max_length=120)]] | None = Field(default=None, max_length=100)
    looking_for: list[Annotated[str, Field(min_length=1, max_length=120)]] | None = Field(default=None, max_length=100)


def profile_dict(row):
    if not row:
        raise HTTPException(404, "Student profile not found.")
    row["user_id"] = str(row["user_id"])
    return row


@router.get("/me")
def get_profile(user: Annotated[dict, Depends(require_user)]):
    with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(f"SELECT {FIELDS} FROM student_public WHERE user_id=%s", (user["user_id"],))
        return profile_dict(cur.fetchone())


@router.put("/me")
def update_profile(data: ProfileUpdate, user: Annotated[dict, Depends(require_user)]):
    values = data.model_dump(exclude_none=True)
    with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        if values:
            schema = columns(conn, "student_public")
            for field in ("skills", "interests", "looking_for"):
                if field in values:
                    values[field] = adapt_list(values[field], schema[field])
            assignments = [sql.SQL("{}=%s").format(sql.Identifier(field)) for field in values]
            if "updated_at" in schema:
                assignments.append(sql.SQL("updated_at=CURRENT_TIMESTAMP"))
            cur.execute(sql.SQL("UPDATE student_public SET {} WHERE user_id=%s").format(sql.SQL(",").join(assignments)), tuple(values.values()) + (user["user_id"],))
        cur.execute(f"SELECT {FIELDS} FROM student_public WHERE user_id=%s", (user["user_id"],))
        result = profile_dict(cur.fetchone())
    return {"message": "Profile updated successfully", "profile": result}


# Compatibility for older callers, without permitting access to another student.
@router.get("/{identifier}")
def get_legacy(identifier: str, user: Annotated[dict, Depends(require_user)]):
    result = get_profile(user)
    if identifier.lower() not in {str(user["usn"]).lower(), str(user["email"]).lower(), str(result["student_id"]).lower()}:
        raise HTTPException(403, "You can only access your own profile.")
    return result


@router.put("/{identifier}")
def put_legacy(identifier: str, data: ProfileUpdate, user: Annotated[dict, Depends(require_user)]):
    get_legacy(identifier, user)
    return update_profile(data, user)