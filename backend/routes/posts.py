from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_connection
from typing import Optional

router = APIRouter(
    prefix="/api/posts",
    tags=["Forum"]
)


class PostCreate(BaseModel):
    student_id: str
    title: str
    description: str
    post_type: str
    skills_required: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    deadline: Optional[str] = None
    team_slots: Optional[int] = None


@router.post("/")
def create_post(post: PostCreate):

    conn = None

    try:
        conn = get_connection()

        with conn.cursor() as cur:

            # Find student
            cur.execute(
                """
                SELECT user_id
                FROM student_public
                WHERE student_id = %s
                """,
                (post.student_id,)
            )

            student = cur.fetchone()

            if student is None:
                raise HTTPException(
                    status_code=404,
                    detail="Student not found"
                )

            user_id = student[0]

            cur.execute(
                """
                INSERT INTO posts
                (
                    user_id,
                    title,
                    description,
                    post_type,
                    skills_required,
                    tags,
                    deadline,
                    team_slots
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING post_id, created_at
                """,
                (
                    user_id,
                    post.title,
                    post.description,
                    post.post_type,
                    post.skills_required,
                    post.tags,
                    post.deadline,
                    post.team_slots
                )
            )

            result = cur.fetchone()

        conn.commit()

        return {
            "message": "Post created successfully",
            "post_id": str(result[0]),
            "created_at": result[1]
        }

    except HTTPException:
        raise

    except Exception as e:

        if conn:
            conn.rollback()

        print("POST ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        if conn:
            conn.close()


@router.get("/")
def get_posts():

    conn = None

    try:
        conn = get_connection()

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    p.post_id,
                    p.title,
                    p.description,
                    p.post_type,
                    p.skills_required,
                    p.tags,
                    p.deadline,
                    p.team_slots,
                    p.created_at,
                    s.student_id,
                    s.name
                FROM posts p
                JOIN student_public s
                    ON p.user_id = s.user_id
                ORDER BY p.created_at DESC
                """
            )

            rows = cur.fetchall()

        return [
            {
                "post_id": str(row[0]),
                "title": row[1],
                "description": row[2],
                "post_type": row[3],
                "skills_required": row[4],
                "tags": row[5],
                "deadline": row[6],
                "team_slots": row[7],
                "created_at": row[8],
                "student_id": row[9],
                "student_name": row[10]
            }
            for row in rows
        ]

    except Exception as e:

        print("GET POSTS ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        if conn:
            conn.close()
class JoinRequest(BaseModel):
    student_id: str


@router.post("/{post_id}/join")
def join_post(post_id: str, request: JoinRequest):

    conn = None

    try:
        conn = get_connection()

        with conn.cursor() as cur:

            # Find the student's existing user_id
            cur.execute(
                """
                SELECT user_id
                FROM student_public
                WHERE student_id = %s
                """,
                (request.student_id,)
            )

            student = cur.fetchone()

            if student is None:
                raise HTTPException(
                    status_code=404,
                    detail="Student not found"
                )

            user_id = student[0]

            # Check that the post exists
            cur.execute(
                """
                SELECT post_id
                FROM posts
                WHERE post_id = %s
                """,
                (post_id,)
            )

            if cur.fetchone() is None:
                raise HTTPException(
                    status_code=404,
                    detail="Post not found"
                )

            # Create join request
            cur.execute(
                """
                INSERT INTO join_requests
                (post_id, user_id)
                VALUES (%s, %s)
                RETURNING join_request_id, status, created_at
                """,
                (post_id, user_id)
            )

            result = cur.fetchone()

        conn.commit()

        return {
            "message": "Interest submitted successfully",
            "join_request_id": str(result[0]),
            "status": result[1],
            "created_at": result[2]
        }

    except HTTPException:
        raise

    except Exception as e:

        if conn:
            conn.rollback()

        print("JOIN ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        if conn:
            conn.close()