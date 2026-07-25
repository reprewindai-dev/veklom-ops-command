# Runbook - devex-chief

## SOP-001: Update README for Changed Repository
1. Read the current README.md
2. Compare to actual deployed behavior
3. Update all outdated sections
4. Verify all links work
5. Commit and push

## SOP-002: Generate API Documentation
# For Python APIs:
cd <repo> && python -c "import app; print(app.openapi())" > docs/openapi.json

## SOP-003: Update SDK for API Changes
1. Read the new API schema
2. Update TypeScript/Python types to match
3. Update SDK methods
4. Update code examples
5. npm run build (SDK), verify zero TypeScript errors
6. Commit and push with clear changelog entry

## SOP-004: Validate Documentation Accuracy
# Follow the README from scratch on a clean machine/environment
# If any step fails: fix the documentation before declaring done
