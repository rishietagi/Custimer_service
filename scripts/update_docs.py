import os
import re
from datetime import datetime

DOCS_DIR = "docs"
BACKEND_ROUTERS_DIR = "backend/app/routers"
BACKEND_MODELS_DIR = "backend/app/models"
FRONTEND_PAGES_DIR = "frontend/src/pages"

REQUIRED_DOCS = [
    "PROJECT_REPORT.md",
    "TECH_STACK.md",
    "API_DOCUMENTATION.md",
    "DATABASE_SCHEMA.md",
    "CHANGELOG.md",
    "ARCHITECTURE.md"
]

def check_files_exist():
    print("Checking if all required documentation files exist...")
    missing = []
    for doc in REQUIRED_DOCS:
        path = os.path.join(DOCS_DIR, doc)
        if not os.path.exists(path):
            missing.append(doc)
    if missing:
        print(f"[MISSING] Missing documentation files: {missing}")
        return False
    print("[OK] All required documentation files are present.")
    return True

def sync_changelog_date():
    print("Syncing CHANGELOG.md date to current date...")
    changelog_path = os.path.join(DOCS_DIR, "CHANGELOG.md")
    if not os.path.exists(changelog_path):
        return
        
    with open(changelog_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Replace date placeholder or date in header like ## [1.0.0] - YYYY-MM-DD
    current_date = datetime.now().strftime("%Y-%m-%d")
    pattern = r"## \[1\.0\.0\] - \d{4}-\d{2}-\d{2}"
    replacement = f"## [1.0.0] - {current_date}"
    
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        with open(changelog_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"[OK] CHANGELOG.md date updated to {current_date}.")
    else:
        print("[INFO] CHANGELOG.md version header already up to date or not found.")

def validate_consistency():
    print("Validating codebase consistency with documentation...")
    
    # 1. Gather all API endpoint files
    api_routers = []
    if os.path.exists(BACKEND_ROUTERS_DIR):
        api_routers = [f.replace(".py", "") for f in os.listdir(BACKEND_ROUTERS_DIR) if f.endswith(".py") and f != "__init__.py"]
    
    # Check if they are documented in API_DOCUMENTATION.md
    api_doc_path = os.path.join(DOCS_DIR, "API_DOCUMENTATION.md")
    if os.path.exists(api_doc_path):
        with open(api_doc_path, "r", encoding="utf-8") as f:
            api_doc_content = f.read().lower()
        for router in api_routers:
            # Check if mentioned
            if router.replace("_", "") not in api_doc_content.replace("-", "").replace(" ", ""):
                print(f"[WARN] Backend router '{router}' might not be documented in API_DOCUMENTATION.md.")
            else:
                print(f"  - Router '{router}' is documented.")
                
    # 2. Gather database models
    db_models = []
    if os.path.exists(BACKEND_MODELS_DIR):
        db_models = [f.replace(".py", "") for f in os.listdir(BACKEND_MODELS_DIR) if f.endswith(".py") and f != "__init__.py"]
        
    db_doc_path = os.path.join(DOCS_DIR, "DATABASE_SCHEMA.md")
    if os.path.exists(db_doc_path):
        with open(db_doc_path, "r", encoding="utf-8") as f:
            db_doc_content = f.read().lower()
        for model in db_models:
            if model.replace("_", "") not in db_doc_content.replace("-", "").replace(" ", ""):
                print(f"[WARN] Database model '{model}' might not be documented in DATABASE_SCHEMA.md.")
            else:
                print(f"  - Model '{model}' is documented.")
                
    # 3. Gather frontend pages
    frontend_pages = []
    if os.path.exists(FRONTEND_PAGES_DIR):
        frontend_pages = [f.replace(".tsx", "").replace(".ts", "") for f in os.listdir(FRONTEND_PAGES_DIR) if (f.endswith(".tsx") or f.endswith(".ts"))]
        
    proj_doc_path = os.path.join(DOCS_DIR, "PROJECT_REPORT.md")
    if os.path.exists(proj_doc_path):
        with open(proj_doc_path, "r", encoding="utf-8") as f:
            proj_doc_content = f.read().lower()
        for page in frontend_pages:
            if page.lower() not in proj_doc_content:
                print(f"[WARN] Frontend page '{page}' might not be referenced in PROJECT_REPORT.md.")
            else:
                print(f"  - Frontend page '{page}' is documented.")
                
    print("[SUCCESS] Consistency validation completed.")

if __name__ == "__main__":
    print("--- Starting Auto-Documentation Utility ---")
    if check_files_exist():
        sync_changelog_date()
        validate_consistency()
    print("--- Documentation Sync Complete ---")
