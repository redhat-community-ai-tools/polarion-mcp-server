#!/usr/bin/env python3
"""
Example: Add test steps to a Polarion test case

This example shows how to add test steps to a test case using the
Polarion MCP Server client.
"""

import os
from polarion_client import PolarionClient

# Configuration from environment
POLARION_URL = os.getenv('POLARION_URL', 'https://polarion.example.com')
POLARION_TOKEN = os.getenv('POLARION_TOKEN')
POLARION_PROJECT = os.getenv('POLARION_PROJECT', 'PROJECT')

# Example test case ID - replace with your actual test case
TEST_CASE_ID = "YOUR-TEST-CASE-ID"  # e.g., "OCP-12345"

# Example test steps
test_steps = [
    {
        "step": "Step 1: Setup test environment",
        "expectedResult": "Environment is ready"
    },
    {
        "step": "Step 2: Execute test action",
        "expectedResult": "Action completes successfully"
    },
    {
        "step": "Step 3: Verify results",
        "expectedResult": "Results match expected output"
    }
]

def main():
    # Initialize client
    client = PolarionClient(
        url=POLARION_URL,
        token=POLARION_TOKEN,
        verify_ssl=False  # Set to True for production
    )
    
    # Add test steps
    result = client.add_test_steps(
        test_case_id=TEST_CASE_ID,
        test_steps=test_steps,
        project_id=POLARION_PROJECT
    )
    
    if result["status"] == "success":
        print(f"Successfully added {result['steps_added']} test steps")
        print(f"View at: {result['url']}")
    else:
        print(f"Failed: {result.get('error')}")

if __name__ == "__main__":
    main()
