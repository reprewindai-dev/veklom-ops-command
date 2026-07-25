# Deployment - qa-chief

## qa-chief does not deploy production services
Tests are deployed as part of the CI/CD pipeline (GitHub Actions).
qa-chief writes the .github/workflows/test.yml files.
After tests pass, qa-chief issues a test-pass certificate to release-chief.

## Test Environment
All truth tests run against live production endpoints.
No mocked endpoints are acceptable for Production Truth certification.
