from database import get_connection

try:
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('student_public', 'student_private');
        """)

        tables = cur.fetchall()

    print("Lakebase connection successful!")
    print("Campus Genie tables:")

    for table in tables:
        print("-", table[0])

    conn.close()

except Exception as e:
    print("Database error:")
    print(e)