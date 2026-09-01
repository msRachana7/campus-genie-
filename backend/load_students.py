import json
from database import get_connection


with open("students_40.json", "r") as file:
    students = json.load(file)

print(f"Found {len(students)} students")


conn = get_connection()

try:
    with conn.cursor() as cur:

        for student in students:
            cur.execute(
                """
                INSERT INTO student_public
                (
                    name,
                    department,
                    year_of_study,
                    skills,
                    interests,
                    student_id,
                    looking_for
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    student["name"],
                    student["department"],
                    student["year"],
                    student["skills"],
                    student["interests"],
                    student["student_id"],
                    student["looking_for"],
                )
            )

    conn.commit()

    print("Successfully inserted students into student_public")

except Exception as e:
    conn.rollback()
    print("Insert failed:")
    print(e)

finally:
    conn.close()