import traceback
import os, sys
# Ensure project root is on sys.path so `src` package is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.pipeline import process_file

if __name__ == '__main__':
    src = r'storage/uploads/shinde.pdf'
    try:
        print(f"Running E2E translation for: {src}")
        result = process_file(src, 'Hindi')
        print('Result:', result)
    except Exception as e:
        print('E2E run failed:', e)
        traceback.print_exc()
