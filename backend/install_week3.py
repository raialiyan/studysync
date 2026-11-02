"""Run once from backend/: python install_week3.py"""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parent
main = root / "main.py"
api = root / "week3_api.py"
if not main.is_file() or not api.is_file():
    raise SystemExit("Place install_week3.py and week3_api.py inside backend/ first.")
original = main.read_text()
addition = "\n\n# Week 3 feature routes\nfrom week3_api import router as week3_router\napp.include_router(week3_router)\n"
if "app.include_router(week3_router)" not in original:
    backup = root / "main.py.pre_week3_backup"
    shutil.copy2(main, backup)
    main.write_text(original + addition)
    print(f"Updated main.py (backup: {backup.name})")
else:
    print("Week 3 router is already registered")

from database import engine
from week3_api import Activity
Activity.__table__.create(bind=engine, checkfirst=True)
print("Created/verified activities table. Week 3 API installed.")
