import json
from database import get_connection


with open("students_40.json", "r") as f:
    students = json.load(f)


conn = get_connection()

try:
    with conn.cursor() as cur:

        for student in students:

            # Find existing user_id from student_public
            cur.execute(
                """
                SELECT user_id
                FROM student_public
                WHERE student_id = %s
                """,
                (student["student_id"],)
            )

            result = cur.fetchone()

            if result is None:
                print(
                    f"Skipping {student['student_id']}: "
                    "student not found in student_public"
                )
                continue

            user_id = result[0]

            # Insert private USN
            cur.execute(
                """
                INSERT INTO student_private
                    (user_id, usn, email, password_hash)
                VALUES
                    (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
                """,
                (
                    user_id,
                    student["usn"],
                    f"{student['usn'].lower()}@bmsce.ac.in",
                    "NOT_REGISTERED"
                )
            )

    conn.commit()

    print("Private student records loaded successfully.")

finally:
    conn.close()