AI App Builder — OpenAI integration patch

Apply on a NEW BRANCH first.

1. backend/requirements.txt
2. backend/app/ai_engine.py
3. backend/app/validation_pipeline.py
4. .github/workflows/openai-test.yml

Do not add an API key to these files. Keep OPENAI_API_KEY only in GitHub Secrets.

After applying:
  pip install -r backend/requirements.txt
  pytest -q

Then run GitHub Actions: Test OpenAI API.
