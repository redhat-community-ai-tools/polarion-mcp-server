#!/usr/bin/env python3
"""
Polarion MCP Server
Comprehensive Model Context Protocol server for Polarion ALM integration
"""

import os
import json
import requests
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP
import urllib3

# Suppress SSL warnings for internal servers
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import integration modules
from polarion_client import PolarionClient
from test_runs import TestRunManager
from integrations.junit_import import JUnitImporter
from integrations.spreadsheet import SpreadsheetIntegration

# Initialize FastMCP server
mcp = FastMCP("Polarion ALM Integration")

# Configuration
POLARION_URL = os.getenv("POLARION_URL", "https://polarion.engineering.redhat.com")
POLARION_TOKEN = os.getenv("POLARION_TOKEN")
DEFAULT_PROJECT = os.getenv("POLARION_PROJECT", "OSE")
VERIFY_SSL = os.getenv("POLARION_VERIFY_SSL", "true").lower() == "true"

if not POLARION_TOKEN:
    print("WARNING: POLARION_TOKEN environment variable not set")

# Initialize clients
polarion_client = PolarionClient(POLARION_URL, POLARION_TOKEN, VERIFY_SSL)
test_run_mgr = TestRunManager(polarion_client)
junit_importer = JUnitImporter(polarion_client)
spreadsheet_integration = SpreadsheetIntegration(polarion_client)


# =============================================================================
# TEST CASE MANAGEMENT TOOLS
# =============================================================================

@mcp.tool()
def test_polarion_connection() -> str:
    """
    Test connection to Polarion and verify authentication.
    Returns status of the connection and token validity.
    """
    try:
        result = polarion_client.test_connection(DEFAULT_PROJECT)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "error": str(e)
        }, indent=2)


@mcp.tool()
def create_polarion_test_case(
    title: str,
    description: str,
    project_id: str = DEFAULT_PROJECT,
    test_steps: Optional[str] = None,
    expected_results: Optional[str] = None,
    severity: str = "should_have",
    status: str = "draft"
) -> str:
    """
    Create a new test case in Polarion.

    Args:
        title: Test case title/summary
        description: Detailed description of what the test validates
        project_id: Polarion project ID (default: from env)
        test_steps: Step-by-step test instructions (newline-separated)
        expected_results: Expected outcomes (newline-separated)
        severity: Importance level (must_have, should_have, nice_to_have, will_not_have)
        status: Initial status (draft, approved, etc.)

    Returns:
        JSON string with created test case ID and details
    """
    try:
        result = polarion_client.create_test_case(
            title=title,
            description=description,
            project_id=project_id,
            test_steps=test_steps,
            expected_results=expected_results,
            severity=severity,
            status=status
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "error": str(e)
        }, indent=2)


@mcp.tool()
def add_test_steps_to_testcase(
    test_case_id: str,
    test_steps: List[Dict[str, str]],
    project_id: str = DEFAULT_PROJECT
) -> str:
    """
    Add or replace test steps for a test case.

    Args:
        test_case_id: The test case ID (e.g., "OCP-88278")
        test_steps: List of test steps with 'step' and 'expectedResult'
            Example: [
                {"step": "Step 1 description", "expectedResult": "Expected result 1"},
                {"step": "Step 2 description", "expectedResult": "Expected result 2"}
            ]
        project_id: Polarion project ID (default: from env)

    Returns:
        JSON string with update status
    """
    try:
        result = polarion_client.add_test_steps(
            test_case_id=test_case_id,
            test_steps=test_steps,
            project_id=project_id
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "error": str(e)
        }, indent=2)


@mcp.tool()
def get_polarion_test_case(
    test_case_id: str,
    project_id: str = DEFAULT_PROJECT,
    include_test_steps: bool = True
) -> str:
    """
    Retrieve details of a specific test case from Polarion.

    Args:
        test_case_id: The Polarion work item ID (e.g., "OCP-88278")
        project_id: Polarion project ID (default: from env)
        include_test_steps: Whether to include test steps

    Returns:
        JSON string with test case details
    """
    try:
        result = polarion_client.get_test_case(
            test_case_id=test_case_id,
            project_id=project_id,
            include_test_steps=include_test_steps
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "error": str(e)
        }, indent=2)


@mcp.tool()
def update_polarion_test_case(
    test_case_id: str,
    project_id: str = DEFAULT_PROJECT,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None
) -> str:
    """
    Update an existing test case in Polarion.

    Args:
        test_case_id: The Polarion work item ID
        project_id: Polarion project ID (default: from env)
        title: New title (optional)
        description: New description (optional)
        status: New status (optional)
        severity: New severity (optional)

    Returns:
        JSON string with update status
    """
    try:
        result = polarion_client.update_test_case(
            test_case_id=test_case_id,
            project_id=project_id,
            title=title,
            description=description,
            status=status,
            severity=severity
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "error": str(e)
        }, indent=2)


@mcp.tool()
def search_polarion_test_cases(
    query: str,
    project_id: str = DEFAULT_PROJECT,
    limit: int = 10
) -> str:
    """
    Search for test cases in Polarion using a query string.

    Args:
        query: Search query (e.g., "type:testcase AND title:Windows")
        project_id: Polarion project ID (default: from env)
        limit: Maximum number of results to return

    Returns:
        JSON string with matching test cases
    """
    try:
        result = polarion_client.search_test_cases(
            query=query,
            project_id=project_id,
            limit=limit
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "error": str(e)
        }, indent=2)


# =============================================================================
# TEST RUN MANAGEMENT TOOLS
# =============================================================================

@mcp.tool()
def create_test_run(
    title: str,
    template: str,
    project_id: str = DEFAULT_PROJECT,
    test_case_ids: Optional[List[str]] = None,
    query: Optional[str] = None
) -> str:
    """
    Create a new test run in Polarion.

    Args:
        title: Test run title (e.g., "Sprint 123 - Certificate Tests")
        template: Template name (e.g., "Release Test", "Manual")
        project_id: Polarion project ID (default: from env)
        test_case_ids: List of test case IDs to include (optional)
        query: Polarion query to select test cases (optional)

    Returns:
        JSON string with test run ID and URL
    """
    try:
        result = test_run_mgr.create_test_run(
            title=title,
            template=template,
            project_id=project_id,
            test_case_ids=test_case_ids,
            query=query
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "error": str(e)
        }, indent=2)


@mcp.tool()
def update_test_run_result(
    test_run_id: str,
    test_case_id: str,
    result: str,
    project_id: str = DEFAULT_PROJECT,
    comment: Optional[str] = None,
    executed_by: Optional[str] = None,
    duration: Optional[int] = None
) -> str:
    """
    Update the result of a test case within a test run.

    Args:
        test_run_id: Test run ID (e.g., "OSE-TR-12345")
        test_case_id: Test case ID (e.g., "OCP-88278")
        result: Test result (passed, failed, blocked)
        project_id: Polarion project ID (default: from env)
        comment: Comment about the result (optional)
        executed_by: Who executed the test (optional)
        duration: Duration in seconds (optional)

    Returns:
        JSON string with update status
    """
    try:
        result = test_run_mgr.update_test_result(
            test_run_id=test_run_id,
            test_case_id=test_case_id,
            result=result,
            project_id=project_id,
            comment=comment,
            executed_by=executed_by,
            duration=duration
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "error": str(e)
        }, indent=2)


@mcp.tool()
def get_test_run_status(
    test_run_id: str,
    project_id: str = DEFAULT_PROJECT
) -> str:
    """
    Get the status and summary of a test run.

    Args:
        test_run_id: Test run ID (e.g., "OSE-TR-12345")
        project_id: Polarion project ID (default: from env)

    Returns:
        JSON string with test run status and statistics
    """
    try:
        result = test_run_mgr.get_test_run_status(
            test_run_id=test_run_id,
            project_id=project_id
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "error": str(e)
        }, indent=2)


# =============================================================================
# INTEGRATION TOOLS
# =============================================================================

@mcp.tool()
def import_junit_results(
    junit_file: str,
    test_run_id: str,
    project_id: str = DEFAULT_PROJECT,
    map_test_ids: Optional[Dict[str, str]] = None,
    auto_create_test_run: bool = False
) -> str:
    """
    Import test results from JUnit XML file.

    Args:
        junit_file: Path to JUnit XML file
        test_run_id: Test run ID to update
        project_id: Polarion project ID (default: from env)
        map_test_ids: Mapping of JUnit test names to Polarion test case IDs
            Example: {"com.example.Test.testMethod": "OCP-88278"}
        auto_create_test_run: Create test run if it doesn't exist

    Returns:
        JSON string with import summary
    """
    try:
        result = junit_importer.import_junit_results(
            junit_file=junit_file,
            test_run_id=test_run_id,
            project_id=project_id,
            map_test_ids=map_test_ids or {},
            auto_create_test_run=auto_create_test_run
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "error": str(e)
        }, indent=2)


@mcp.tool()
def export_test_cases_to_spreadsheet(
    query: str,
    output_file: str,
    project_id: str = DEFAULT_PROJECT,
    include_test_steps: bool = True,
    format: str = "xlsx"
) -> str:
    """
    Export test cases to Excel or CSV spreadsheet.

    Args:
        query: Polarion query to select test cases
        output_file: Output file path (.xlsx or .csv)
        project_id: Polarion project ID (default: from env)
        include_test_steps: Include test steps in export
        format: Output format (xlsx or csv)

    Returns:
        JSON string with export summary
    """
    try:
        result = spreadsheet_integration.export_test_cases(
            query=query,
            output_file=output_file,
            project_id=project_id,
            include_test_steps=include_test_steps,
            format=format
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "error": str(e)
        }, indent=2)


@mcp.tool()
def import_test_cases_from_spreadsheet(
    spreadsheet_file: str,
    project_id: str = DEFAULT_PROJECT,
    update_existing: bool = False
) -> str:
    """
    Bulk import test cases from spreadsheet.

    Args:
        spreadsheet_file: Input spreadsheet path (.xlsx or .csv)
        project_id: Polarion project ID (default: from env)
        update_existing: Update existing test cases if they exist

    Returns:
        JSON string with import summary
    """
    try:
        result = spreadsheet_integration.import_test_cases(
            spreadsheet_file=spreadsheet_file,
            project_id=project_id,
            update_existing=update_existing
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "error": str(e)
        }, indent=2)


if __name__ == "__main__":
    # Run the MCP server
    print("=" * 60)
    print("Starting Polarion MCP Server")
    print("=" * 60)
    print(f"Polarion URL: {POLARION_URL}")
    print(f"Default Project: {DEFAULT_PROJECT}")
    print(f"SSL Verification: {VERIFY_SSL}")
    print(f"Token configured: {'Yes' if POLARION_TOKEN else 'No'}")
    print("=" * 60)
    print("\nAvailable tools:")
    print("  - Test Case Management (create, update, search, test steps)")
    print("  - Test Run Management (create, update results, status)")
    print("  - JUnit Integration (import results)")
    print("  - Spreadsheet Integration (import/export)")
    print("\nServer ready!")
    print("=" * 60)
    mcp.run()
