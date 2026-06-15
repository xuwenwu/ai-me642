# Canvas Integration

The current stable LMS workflow is CSV export. Canvas API integration is scaffolded but disabled by default.

## Server Settings

Set these only on the backend host:

```text
CANVAS_ENABLED=true
CANVAS_BASE_URL=https://canvas.example.edu
CANVAS_COURSE_ID=12345
CANVAS_API_TOKEN=server-side-token
```

Never put the Canvas API token in frontend code or Git.

## Status Check

Instructors can check server configuration through:

```text
GET /api/instructor/canvas/status
```

The endpoint does not expose the token.

## Current Boundary

Live roster, assignment, and grade sync still require institutional approval, token ownership, and test-course verification. Until then, use:

- `canvas_gradebook_import.csv`
- `lms_submission_detail.csv`
- `roster_export.csv`
