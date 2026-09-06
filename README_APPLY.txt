AI App Builder Beta Patch Bundle

HOW TO APPLY
1. Extract this ZIP at the AI App Builder project root.
2. Allow overwrite for the listed files.
3. Run:
   cd backend
   pip install -r requirements.txt
   cd ..
   pytest -q

FILES INCLUDED
- backend/app/patch_engine.py
- backend/app/transaction_manager.py
- backend/app/change_analyzer.py
- backend/app/dependency_analyzer.py
- backend/app/project_scanner.py
- backend/app/code_generation_engine.py
- backend/app/workflow_engine.py
- tests/test_patch_engine.py
- tests/test_transaction_manager.py
- tests/test_project_scanner.py

IMPORTANT
This bundle is an overlay patch based on the inspected project source.
It does not replace unrelated files.
After applying, run the complete test suite before deployment.
