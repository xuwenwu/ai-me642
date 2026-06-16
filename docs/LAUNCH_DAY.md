# Launch Day Checklist

Use this checklist when starting the app for an actual class activity.

## Before Students Arrive

1. Pull the approved branch.
2. Start or restart the pilot stack:

```powershell
.\scripts\pilot-start.ps1 -Port 3000
```

3. Confirm service health:

```powershell
.\scripts\pilot-status.ps1 -Port 3000
.\scripts\pilot-smoke.ps1 -Port 3000 -InstructorEmail instructor@your.edu -InstructorPassword "temporary-password"
```

4. Sign in as instructor and open Instructor Overview.
5. Confirm **Pilot Launch Checklist** is `Ready for pilot` or review any yellow/red items.
6. Open Course Setup and confirm:
   - roster is present,
   - the active assignment is published,
   - required file types and validation profile are set,
   - AI policy and prompt templates match the class instructions,
   - live assistant mode is enabled only if approved for the activity.
7. Open Prompt Logs and verify the responsible-AI policy is visible.
8. Open the student login page in a separate browser/profile and confirm one test student can reach Dashboard.

## During Class

- Keep Instructor Overview open for launch status and attention counts.
- Use Instructor Review Queue for validation warnings, missing disclosure, and ungraded submitted work.
- Treat validation output as evidence, not a grade.
- If live AI guidance behaves unexpectedly, switch Course Setup -> AI Policy -> Provider to offline guidance.

## After Class

1. Run a backup:

```powershell
.\scripts\pilot-backup.ps1 -Port 3000
```

2. Download exports as needed:
   - gradebook CSV,
   - Canvas import CSV,
   - LMS submission detail CSV,
   - roster CSV.
3. Record incidents or confusing workflow points in `docs/course_pilot/PILOT_FEEDBACK.md`.
4. Stop the stack only if the pilot should be offline:

```powershell
.\scripts\pilot-stop.ps1 -Port 3000
```

Use `-RemoveContainers` only when you intentionally want to remove stopped containers. The named Docker data volume is preserved.
