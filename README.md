# AI App Builder
Backend foundation for an AI application builder.

Workflow:
USER COMMAND -> AI ANALYSIS -> PLAN -> APPROVAL -> MINIMAL PATCH -> VALIDATION -> TESTS -> ERROR ANALYSIS -> DEPLOY

Safety:
- Never rewrite the whole project for a local problem.
- Change only the smallest affected file/function/section.
- Backup before significant changes.
- Destructive/high-impact changes require approval.
- Never claim success without passing validation/tests.
