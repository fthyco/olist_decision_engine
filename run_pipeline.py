import subprocess
import sys
import time
import os
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
PIPELINE_FOLDER = "pipeline" 

PIPELINE = [
    "01_setup_infrastructure.py",
    "02_build_dwh_schema.py",
    "03_market_engine.py",
    "04_attribution_bridge.py",
    "05_unified_financials.py"
]

def run_script(script_name):
    print(f"\n{'='*70}")
    print(f"▶️  EXECUTING: {script_name}")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_path, PIPELINE_FOLDER, script_name)
    
    if not os.path.exists(script_path):
        print(f"❌ ERROR: File not found: {script_path}")
        return False

    try:

        result = subprocess.run(
            [sys.executable, "-u", script_path], 
            check=True,
        )
        
        elapsed = time.time() - start_time
        print(f"\n✅ SUCCESS: {script_name} finished in {elapsed:.2f} seconds.")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n⛔ FAILED: {script_name} crashed with exit code {e.returncode}.")
        return False
    except Exception as e:
        print(f"\n⛔ ERROR: System error: {e}")
        return False
    
def run_notebook(notebook_rel_path):
    print(f"\n{'='*70}")
    print(f"▶️  EXECUTING NOTEBOOK: {notebook_rel_path}")
    print(f"{'='*70}")

    start_time = time.time()

    base_path = Path(__file__).resolve().parent
    notebook_path = (base_path / notebook_rel_path).resolve()

    if not notebook_path.exists():
        print(f"❌ ERROR: Notebook not found: {notebook_path}")
        return False

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                "--inplace",
                "--ExecutePreprocessor.iopub_timeout=600", 
                "--allow-errors",
                str(notebook_path)
            ],
            check=True,
            cwd=base_path
        )

        elapsed = time.time() - start_time
        print(f"\n✅ SUCCESS: Notebook finished in {elapsed:.2f} seconds.")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n⛔ FAILED: Notebook crashed with exit code {e.returncode}.")
        return False

def main():
    
    print("="*70)
    print("OLIST DECISION ENGINE")
    print("STEP 1 / INITIAL SETUP")
    print("- This will build the full data environment")
    print("- This is required ONCE before using the GUI")
    print("="*70)

    total_start = time.time()
    print(" STARTING OLIST DECISION ENGINE PIPELINE (LOCAL)...\n")

    # Phase 1: Python ETL Scripts
    for script in PIPELINE:
        if not run_script(script):
            print("\n⛔ PIPELINE HALTED.")
            sys.exit(1)

    # Phase 2: Post-ETL Notebook
    notebook_path = "notebooks/01_Preprocess_Static_Dimensions.ipynb"
    
    if os.path.exists(os.path.join(os.path.dirname(__file__), notebook_path)):
        if not run_notebook(notebook_path):
            print("\n⛔ PIPELINE HALTED AT NOTEBOOK STAGE.")
            sys.exit(1)
    else:
        print(f"\n⚠️  WARNING: Notebook path '{notebook_path}' not found. Skipping.")

    print(f"\n PIPELINE COMPLETED SUCCESSFULLY.")
    print(f"  Total Time: {time.time() - total_start:.2f}s")
    print("\nNEXT STEP:")
    print("→ Run the GUI executable to start analysis.")


if __name__ == "__main__":
    main()