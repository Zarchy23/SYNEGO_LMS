import sqlite3

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

try:
    cursor.execute("SELECT COUNT(*) FROM lms_user")
    print(f"SQLite Users: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"Error querying users: {e}")

try:
    cursor.execute("SELECT COUNT(*) FROM lms_course")
    print(f"SQLite Courses: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"Error querying courses: {e}")

try:
    cursor.execute("SELECT COUNT(*) FROM lms_chapter")
    print(f"SQLite Chapters: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"Error querying chapters: {e}")

try:
    cursor.execute("SELECT title FROM lms_course LIMIT 5")
    print("\nCourses in SQLite:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")
except Exception as e:
    print(f"Error: {e}")

conn.close()
