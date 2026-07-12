import sys
from pathlib import Path


# pytest 有时会从 tests/ 目录或外部解释器启动，导致项目根目录不在 sys.path。
# 这里把 jobmatch-crew 根目录加入导入路径，保证测试里可以稳定 import app。
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
