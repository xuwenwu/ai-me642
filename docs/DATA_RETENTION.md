# Data Retention And Privacy

AI-ME642 stores course roster records, submitted files, validation reports, grades, and AI prompt-log disclosures. For a small pilot, the instructor should treat the deployment as course data infrastructure.

## Recommended Pilot Policy

- Keep active course data during the semester.
- Export a course archive after final grading.
- Keep archived records only as long as required by course, department, or institutional policy.
- Delete test accounts and test submissions before inviting real students.
- Keep external AI provider mode disabled unless approved.

## Archive

Create a course archive ZIP:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\archive_course_data.py
```

In Docker:

```powershell
docker compose -f docker-compose.pilot.yml exec backend python scripts/archive_course_data.py
```

The archive includes CSV summaries plus uploaded files.

## Backup

Backups are operational recovery artifacts. Archives are course-record artifacts. Keep both outside the host when the pilot matters.
