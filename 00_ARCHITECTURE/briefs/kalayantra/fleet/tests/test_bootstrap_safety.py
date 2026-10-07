"""B-3b executable safety cases for the campaign finalizer and executor."""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent

def test_finalizer_failure_and_acceptance_cases():
    subprocess.run([sys.executable, str(HERE / 'finalizer_cases.py')], check=True, timeout=30)

def test_executor_lock_process_group_and_fence_cases():
    subprocess.run([sys.executable, str(HERE / 'executor_cases.py')], check=True, timeout=30)
