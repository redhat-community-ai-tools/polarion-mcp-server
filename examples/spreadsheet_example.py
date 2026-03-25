#!/usr/bin/env python3
"""
Example: Export/Import Test Cases via Spreadsheet
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from polarion_client import PolarionClient
from integrations.spreadsheet import SpreadsheetIntegration

# Initialize client
client = PolarionClient(
    url=os.getenv("POLARION_URL"),
    token=os.getenv("POLARION_TOKEN"),
    verify_ssl=False
)

# Initialize spreadsheet integration
spreadsheet = SpreadsheetIntegration(client)

# EXPORT EXAMPLE
print("Exporting test cases...")
export_result = spreadsheet.export_test_cases(
    query="title:Windows AND status:approved",
    output_file="/tmp/windows-test-cases.xlsx",
    project_id=os.getenv("POLARION_PROJECT", "OSE"),
    include_test_steps=True,
    format="xlsx"
)

print(f"Export result: {export_result}")

# IMPORT EXAMPLE
print("\nImporting test cases from spreadsheet...")
import_result = spreadsheet.import_test_cases(
    spreadsheet_file="/tmp/new-test-cases.xlsx",
    project_id=os.getenv("POLARION_PROJECT", "OSE"),
    update_existing=False
)

print(f"Import result: {import_result}")
