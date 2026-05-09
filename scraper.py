from playwright.async_api import async_playwright
from students import STUDENTS

LOGIN_URL = "https://online.udvash-unmesh.com/Account/Login"
DATA_URL  = "https://online.udvash-unmesh.com/Performance/Report?programId=66&sessionId=66&t=0&d=0"

SUBJECT_MAP = {
    "bangla": "Bangla",
    "eng":    "English",
    "chem":   "Chemistry",
    "bio":    "Biology",
    "phys":   "Physics",
    "hmath":  "Higher Math",
    "ict":    "ICT",
}

# How each subject appears in the booster exam name
BOOSTER_SUBJECT_MAP = {
    "bangla": "bangla",
    "chem":   "chemistry",
    "bio":    "biology",
    "phys":   "physics",
    "hmath":  "higher math",
    "ict":    "ict",
}

PAPER_MAP = {
    "1": "1st",
    "2": "2nd",
    "3": "3rd",
    "4": "4th",
}

NO_PAPER_SUBJECTS = ["ict"]

BOOSTER_VALID_SUBJECTS = ["bangla", "chem", "bio", "phys", "hmath", "ict"]
BOOSTER_DIV_TEXT = "HSC/Alim MCQ Booster Course (for Science)"


async def _login_and_goto_report(page, student):
    await page.goto(LOGIN_URL, wait_until="domcontentloaded")
    await page.wait_for_selector("input[name='RegistrationNumber']", timeout=15000)
    await page.fill("input[name='RegistrationNumber']", student["reg"])
    await page.click("#btnSubmit")
    await page.wait_for_load_state("domcontentloaded")

    await page.wait_for_selector("input[name='Password']", timeout=15000)
    await page.fill("input[name='Password']", student["password"])
    await page.click("button[type='submit']")
    await page.wait_for_load_state("domcontentloaded")

    await page.goto(DATA_URL, wait_until="domcontentloaded")

    try:
        await page.wait_for_selector("table tr td", timeout=20000)
    except:
        return False

    await page.wait_for_timeout(2000)
    return True


async def fetch_result(nickname, subject_code, paper_no, exam_serial, show_cq, show_mcq, show_marks, show_branch, show_central):
    nickname = nickname.lower()

    if nickname not in STUDENTS:
        return f"No student found with nickname '{nickname}'. Check the spelling."

    student = STUDENTS[nickname]

    subject_full = SUBJECT_MAP.get(subject_code)
    if not subject_full:
        return f"Unknown subject code '{subject_code}'."

    exam_serial_formatted = f"Exam-{exam_serial.zfill(2)}"

    if subject_code in NO_PAPER_SUBJECTS:
        search_subject = subject_full.lower()
        paper_word = None
    else:
        paper_word = PAPER_MAP.get(paper_no, paper_no + "th")
        search_subject = f"{subject_full} {paper_word} Paper".lower()

    search_serial = exam_serial_formatted.lower()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(60000)

        loaded = await _login_and_goto_report(page, student)
        if not loaded:
            await browser.close()
            return "Results table did not load in time. Try again."

        rows = await page.query_selector_all("table tr")

        matched_cells = None
        for row in rows:
            cells = [await cell.inner_text() for cell in await row.query_selector_all("td, th")]
            cells = [c.strip() for c in cells]
            if len(cells) >= 10:
                exam_name = cells[2].lower()
                if search_subject in exam_name and search_serial in exam_name:
                    matched_cells = cells
                    break

        await browser.close()

    if not matched_cells:
        if subject_code in NO_PAPER_SUBJECTS:
            label = f"{subject_full} {exam_serial_formatted}"
        else:
            label = f"{subject_full} {paper_word} Paper {exam_serial_formatted}"
        return f"No result found for {label}. Check the subject, paper, and exam number."

    mcq_marks     = matched_cells[4]
    cq_marks      = matched_cells[5]
    total_marks   = matched_cells[7]
    highest       = matched_cells[8]
    branch_merit  = matched_cells[9]
    central_merit = matched_cells[10]

    if subject_code in NO_PAPER_SUBJECTS:
        exam_label = f"{subject_full} — {exam_serial_formatted}"
    else:
        exam_label = f"{subject_full} {paper_word} Paper — {exam_serial_formatted}"

    show_all = not any([show_cq, show_mcq, show_marks, show_branch, show_central])

    lines = [f"📋 *{nickname.upper()} — {exam_label}*"]

    if show_all or show_mcq or show_marks:
        lines.append(f"MCQ Marks: {mcq_marks}")
    if show_all or show_cq or show_marks:
        lines.append(f"Written/CQ Marks: {cq_marks}")
    if show_all:
        lines.append(f"Total Marks: {total_marks}")
        lines.append(f"Highest Marks: {highest}")
    if show_all or show_branch:
        lines.append(f"Branch Merit: {branch_merit}")
    if show_all or show_central:
        lines.append(f"Central Merit: {central_merit}")

    return "\n".join(lines)


async def fetch_booster(nickname, subject_code):
    nickname = nickname.lower()

    if nickname not in STUDENTS:
        return f"No student found with nickname '{nickname}'. Check the spelling."

    if subject_code not in BOOSTER_VALID_SUBJECTS:
        return f"'{subject_code}' is not available in the booster course. Valid subjects: {', '.join(BOOSTER_VALID_SUBJECTS)}"

    student = STUDENTS[nickname]
    subject_full = SUBJECT_MAP[subject_code]
    search_keyword = BOOSTER_SUBJECT_MAP[subject_code]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(60000)

        loaded = await _login_and_goto_report(page, student)
        if not loaded:
            await browser.close()
            return "Results table did not load in time. Try again."

        booster_div = await page.query_selector(f"div.course-title:has-text('{BOOSTER_DIV_TEXT}')")
        if not booster_div:
            await browser.close()
            return "Could not find the MCQ Booster course section on the page."

        booster_table = await page.evaluate_handle("""
            (div) => {
                let el = div.nextElementSibling;
                while (el) {
                    if (el.tagName === 'TABLE') return el;
                    let t = el.querySelector('table');
                    if (t) return t;
                    el = el.nextElementSibling;
                }
                return null;
            }
        """, booster_div)

        if not booster_table:
            await browser.close()
            return "Could not find the booster results table."

        rows = await booster_table.query_selector_all("tr")

        matched_cells = None
        for row in rows:
            cells = [await cell.inner_text() for cell in await row.query_selector_all("td, th")]
            cells = [c.strip() for c in cells]
            if len(cells) >= 10:
                exam_name = cells[2].lower()
                if search_keyword in exam_name:
                    matched_cells = cells
                    break

        await browser.close()

    if not matched_cells:
        return f"No booster result found for {subject_full}."

    # Columns: [0] Serial, [1] Date, [2] Exam Name, [3] Platform,
    #          [4] MCQ Marks, [5] Written Marks, [6] Deduction,
    #          [7] Total Marks, [8] Highest Marks, [9] Branch Merit, [10] Central Merit
    exam_name     = matched_cells[2]
    mcq_marks     = matched_cells[4]
    total_marks   = matched_cells[7]
    highest       = matched_cells[8]
    branch_merit  = matched_cells[9]
    central_merit = matched_cells[10]

    lines = [
        f"🚀 *{nickname.upper()} — {exam_name}*",
        f"MCQ Marks: {mcq_marks}",
        f"Highest Marks: {highest}",
        f"Branch Merit: {branch_merit}",
        f"Central Merit: {central_merit}",
    ]

    return "\n".join(lines)


async def fetch_total(nickname, booster=False):
    nickname = nickname.lower()

    if nickname not in STUDENTS:
        return f"No student found with nickname '{nickname}'. Check the spelling."

    student = STUDENTS[nickname]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(60000)

        loaded = await _login_and_goto_report(page, student)
        if not loaded:
            await browser.close()
            return "Results table did not load in time. Try again."

        tables = await page.query_selector_all("table")

        merit_table = None
        for table in tables:
            html = await table.inner_text()
            if "Course Name" in html and "Course Branch Merit" in html:
                merit_table = table
                break

        if not merit_table:
            await browser.close()
            return "Could not find the course merit table."

        rows = await merit_table.query_selector_all("tr")

        # Collect all valid data rows (cells[0] is a digit = a real data row)
        data_rows = []
        for row in rows:
            cells = [await cell.inner_text() for cell in await row.query_selector_all("td, th")]
            cells = [c.strip() for c in cells]
            if len(cells) >= 9 and cells[0].isdigit():
                data_rows.append(cells)

        await browser.close()

    # booster=False → first row (index 0); booster=True → second row (index 1)
    target_index = 1 if booster else 0
    if target_index >= len(data_rows):
        return "Could not find course merit data." if not booster else "Could not find booster course merit data."

    data_row = data_rows[target_index]

    course_name    = data_row[1]
    mcq_marks      = data_row[2]
    written_marks  = data_row[3]
    obtained_marks = data_row[4]
    deduction      = data_row[5]
    highest_marks  = data_row[6]
    branch_merit   = data_row[7]
    central_merit  = data_row[8]

    label = "Booster Course Merit" if booster else "Course Merit"
    lines = [
        f"📊 *{nickname.upper()} — {label}*",
        f"Course: {course_name}",
        f"Total MCQ Marks: {mcq_marks}",
        f"Total Written Marks: {written_marks}",
        f"Total Obtained Marks: {obtained_marks}",
        f"Deduction: {deduction}",
        f"Highest Marks: {highest_marks}",
        f"Branch Merit: {branch_merit}",
        f"Central Merit: {central_merit}",
    ]

    return "\n".join(lines)
