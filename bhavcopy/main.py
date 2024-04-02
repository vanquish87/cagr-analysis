import os
import sys

# Get the absolute path of the current script
current_script_path = os.path.abspath(__file__)
# Move one folder above
project_root = os.path.dirname(os.path.dirname(current_script_path))

# Add the absolute path to the project root to sys.path
sys.path.append(project_root)

from scripts import bse_scripts_02_01_07
from cagr.utils import calculate_execution_time
from controller import process_company


@calculate_execution_time
def main():
    scripts = []
    len_scripts = len(bse_scripts_02_01_07)
    for index, code in enumerate(bse_scripts_02_01_07, start=1):
        print(f"AI analyzing {index} of {len_scripts}")
        code, company_name, script = process_company(code)
        if script:
            print(f"{code}: {company_name}: {script}")
            scripts.append(script)

    print(scripts)
