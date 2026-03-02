from datetime import datetime, timezone, timedelta
from routine import ROUTINE

SUBJECT_MAP = {
    "bangla": "Bangla",
    "eng":    "English",
    "chem":   "Chemistry",
    "bio":    "Biology",
    "phys":   "Physics",
    "hmath":  "Higher Math",
    "ict":    "ICT",
}

# Bangladesh is UTC+6
BD_TIMEZONE = timezone(timedelta(hours=6))

def today_bd():
    return datetime.now(BD_TIMEZONE).date()

def format_exam(exam):
    return (
        f"📅 *{exam['name']}*\n"
        f"Date: {exam['date']}\n"
        f"Duration: {exam['duration']} hrs\n"
        f"Syllabus: {exam['syllabus']}\n"
        f"Marks: {exam['marks']}"
    )

def get_upcoming_all():
    today = today_bd()
    upcoming = [e for e in ROUTINE if datetime.fromisoformat(e["date"]).date() > today]
    if not upcoming:
        return "No such exam left :D"
    return format_exam(upcoming[0])

def get_upcoming_subject(subject_code, paper_no):
    today = today_bd()
    upcoming = [
        e for e in ROUTINE
        if e["subject"] == subject_code
        and e["paper"] == paper_no
        and datetime.fromisoformat(e["date"]).date() > today
    ]
    if not upcoming:
        return "No such exam left :D"
    return format_exam(upcoming[0])