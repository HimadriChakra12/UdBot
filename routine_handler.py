from datetime import date
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

def format_exam(exam):
    return (
        f"📅 *{exam['name']}*\n"
        f"Date: {exam['date']}\n"
        f"Duration: {exam['duration']} hrs\n"
        f"Syllabus: {exam['syllabus']}\n"
        f"Marks: {exam['marks']}"
    )

def get_upcoming_all():
    today = date.today()
    upcoming = [e for e in ROUTINE if date.fromisoformat(e["date"]) >= today]
    if not upcoming:
        return "No such exam left :D"
    return format_exam(upcoming[0])

def get_upcoming_subject(subject_code, paper_no):
    today = date.today()
    upcoming = [
        e for e in ROUTINE
        if e["subject"] == subject_code
        and e["paper"] == paper_no
        and date.fromisoformat(e["date"]) >= today
    ]
    if not upcoming:
        return "No such exam left :D"
    return format_exam(upcoming[0])