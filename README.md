# Polarion MCP Server

A comprehensive Model Context Protocol (MCP) server for Siemens Polarion ALM integration, with full support for test case management, test runs, and result reporting.

## Features

### Test Case Management
- Create test cases with full details
- Update test case attributes
- Search and query test cases
- **Add/update test steps** (REST API + SOAP API fallback)
- **Blank Slate Strategy** - Add test steps immediately upon creation
- **SOAP API Integration** - Override existing test steps with username/password auth
- Link test cases to requirements

### Test Run Management
- Create test runs
- Add test cases to test runs
- Update test run status
- Record test results (passed/failed/blocked)
- Add attachments and comments

### Integration Capabilities
- **JUnit XML import** - Import test results from JUnit reports
- **Spreadsheet export** - Export test cases/results to Excel/CSV
- **Spreadsheet import** - Bulk import test cases from spreadsheets
- Webhook support for CI/CD integration

## Quick Start

### Prerequisites
```bash
pip install fastmcp requests openpyxl xmltodict
```

### Installation

1. Clone or copy this project:
```bash
cd ~/Documents/GitHub
git clone <repo-url> polarion-mcp-server
cd polarion-mcp-server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
export POLARION_TOKEN="your-personal-access-token"
export POLARION_URL="https://polarion.engineering.redhat.com"
export POLARION_PROJECT="OSE"
export POLARION_VERIFY_SSL="false"  # For internal Red Hat servers

# Optional: For SOAP API support (updating existing test steps)
export POLARION_USERNAME="your-username"
export POLARION_PASSWORD="your-password"
```

### Configuration for Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "polarion": {
      "command": "python3",
      "args": [
        "/path/to/polarion-mcp-server/server.py"
      ],
      "env": {
        "POLARION_TOKEN": "${POLARION_TOKEN}",
        "POLARION_URL": "https://polarion.engineering.redhat.com",
        "POLARION_PROJECT": "OSE",
        "POLARION_VERIFY_SSL": "false"
      }
    }
  }
}
```

### Running Standalone

```bash
python3 server.py
```

## Usage Examples

### 1. Create a Test Case

```python
# Using the MCP tool
create_polarion_test_case(
    title="Verify certificate validation",
    description="Test that certificates are read from controllerConfig",
    test_steps="1. Check config\n2. Verify certs\n3. Validate",
    expected_results="All certificates valid",
    severity="should_have",
    status="draft"
)
```

### 2. Add Test Steps

```python
add_test_steps_to_testcase(
    test_case_id="PROJECT-123",
    test_steps=[
        {
            "step": "Run command: oc get nodes",
            "expectedResult": "All nodes are Ready"
        },
        {
            "step": "Check certificate: Get-Item C:\\k\\cert.crt",
            "expectedResult": "File exists"
        }
    ]
)
```

### 3. Create Test Run

```python
create_test_run(
    title="Sprint 123 - Certificate Tests",
    template="Release Test",
    test_case_ids=["PROJECT-123", "PROJECT-456"],
    query="type:testcase AND title:certificate"
)
```

### 4. Update Test Run Results

```python
update_test_run_result(
    test_run_id="OSE-TR-12345",
    test_case_id="PROJECT-123",
    result="passed",
    comment="All certificates validated successfully",
    executed_by="user@example.com",
    duration=120  # seconds
)
```

### 5. Import JUnit Results

```python
import_junit_results(
    junit_file="/tmp/junit-results.xml",
    test_run_id="OSE-TR-12345",
    map_test_ids={
        "com.example.CertTest.testKubeletCA": "PROJECT-123",
        "com.example.CertTest.testCloudCA": "PROJECT-456"
    }
)
```

### 6. Export to Spreadsheet

```python
export_test_cases_to_spreadsheet(
    query="type:testcase AND author:username",
    output_file="/tmp/my-tests.xlsx",
    include_test_steps=True
)
```

### 7. Import from Spreadsheet

```python
import_test_cases_from_spreadsheet(
    spreadsheet_file="/tmp/test-cases.xlsx",
    project_id="OSE"
)
```

## Test Steps Management Strategies

The server supports two strategies for managing test steps, working around a known Polarion REST API limitation.

### Limitation: Test Steps Relationship is READ-ONLY

The Polarion REST API v1 has a limitation where the `testSteps` relationship cannot be modified after initial creation:

- **POST /teststeps**: Only works if NO test steps exist (blank slate)
- **DELETE /teststeps/{index}**: Removes step content but doesn't clear metadata flag
- **PATCH /workitems** with testSteps: Not supported (malformed JSON error)
- **PATCH /relationships/testSteps**: Fails with "Cannot modify read-only field(s)"

### Strategy 1: Blank Slate (Default - REST API)

Create test steps IMMEDIATELY when creating the test case, before any manual edits:

```python
# Create test case WITH test steps in one operation
create_polarion_test_case(
    title="Certificate validation test",
    description="Verify certificates from controllerConfig",
    test_steps=[
        {"step": "Check node status", "expectedResult": "All nodes Ready"},
        {"step": "Verify certificate", "expectedResult": "Certificate valid"}
    ],
    blank_slate_strategy=True  # Default - adds steps immediately
)
```

**Advantages:**
- Uses REST API only (Bearer token authentication)
- Atomic operation
- No credentials needed beyond access token
- Works for new test cases

**Limitation:**
- Only works for NEW test cases (before any manual edits)

### Strategy 2: SOAP API Fallback (For Existing Test Cases)

Use SOAP API to UPDATE existing test steps (requires username/password):

```python
# For test cases that already have steps
add_test_steps_to_testcase(
    test_case_id="PROJECT-123",
    test_steps=[
        {"step": "Updated step 1", "expectedResult": "Updated result 1"},
        {"step": "Updated step 2", "expectedResult": "Updated result 2"}
    ],
    force_soap=True  # Use SOAP API instead of REST
)
```

**Configuration Required:**
```bash
export POLARION_USERNAME="your-username"
export POLARION_PASSWORD="your-password"
```

**Advantages:**
- Can UPDATE existing test steps
- Replaces all steps at once
- Works for test cases with manual edits

**Requirements:**
- Polarion username/password (not just Bearer token)
- Basic Authentication support

### Automatic Fallback

The server automatically tries SOAP API if REST fails:

```python
# Automatically detects existing steps and uses SOAP if available
result = add_test_steps_to_testcase(
    test_case_id="PROJECT-123",
    test_steps=[...]
)

# Result includes method used
print(result["method"])  # "REST" or "SOAP"
```

### Recommended Workflow

**For New Test Cases:**
1. Use `create_polarion_test_case()` with `test_steps` parameter
2. Let `blank_slate_strategy=True` add steps immediately
3. No manual intervention needed

**For Existing Test Cases:**
1. Set `POLARION_USERNAME` and `POLARION_PASSWORD` environment variables
2. Use `add_test_steps_to_testcase()` with `force_soap=True`
3. SOAP API will replace all existing steps

**For Automation:**
- Always create test cases programmatically with steps
- Avoid manual edits before automation completes
- Use SOAP API only when absolutely necessary

## API Documentation

### Test Case Tools

#### `create_polarion_test_case`
Create a new test case in Polarion.

**Parameters:**
- `title` (str): Test case title
- `description` (str): Detailed description
- `project_id` (str): Project ID (default: from env)
- `test_steps` (str, optional): Test steps (newline-separated)
- `expected_results` (str, optional): Expected outcomes
- `severity` (str): must_have, should_have, nice_to_have, will_not_have
- `status` (str): draft, approved, etc.

**Returns:** JSON with test case ID and URL

#### `add_test_steps_to_testcase`
Add or replace test steps for a test case.

**Parameters:**
- `test_case_id` (str): Test case ID (e.g., "PROJECT-123")
- `test_steps` (List[Dict]): List of {"step": "...", "expectedResult": "..."}
- `project_id` (str): Project ID

**Returns:** JSON with success status and steps count

#### `search_polarion_test_cases`
Search for test cases using Polarion query language.

**Parameters:**
- `query` (str): Polarion query (e.g., "type:testcase AND title:Windows")
- `project_id` (str): Project ID
- `limit` (int): Max results to return

**Returns:** JSON with matching test cases

### Test Run Tools

#### `create_test_run`
Create a new test run.

**Parameters:**
- `title` (str): Test run title
- `template` (str): Template name (e.g., "Release Test")
- `project_id` (str): Project ID
- `test_case_ids` (List[str], optional): Test case IDs to include
- `query` (str, optional): Query to select test cases

**Returns:** JSON with test run ID and URL

#### `update_test_run_result`
Update the result of a test case within a test run.

**Parameters:**
- `test_run_id` (str): Test run ID
- `test_case_id` (str): Test case ID
- `result` (str): passed, failed, blocked
- `comment` (str, optional): Comment about the result
- `executed_by` (str, optional): Who executed the test
- `duration` (int, optional): Duration in seconds

**Returns:** JSON with update status

### Integration Tools

#### `import_junit_results`
Import test results from JUnit XML file.

**Parameters:**
- `junit_file` (str): Path to JUnit XML file
- `test_run_id` (str): Test run ID to update
- `map_test_ids` (Dict[str, str]): Map JUnit test names to Polarion IDs
- `auto_create_test_run` (bool): Create test run if it doesn't exist

**Returns:** JSON with import summary

#### `export_test_cases_to_spreadsheet`
Export test cases to Excel/CSV.

**Parameters:**
- `query` (str): Query to select test cases
- `output_file` (str): Output file path (.xlsx or .csv)
- `include_test_steps` (bool): Include test steps
- `format` (str): xlsx or csv

**Returns:** JSON with export summary

#### `import_test_cases_from_spreadsheet`
Bulk import test cases from spreadsheet.

**Parameters:**
- `spreadsheet_file` (str): Input spreadsheet path
- `project_id` (str): Project ID
- `update_existing` (bool): Update if test case exists

**Returns:** JSON with import summary

## Spreadsheet Format

### Test Cases Import Template

| Title | Description | Severity | Status | Test Steps | Expected Results |
|-------|-------------|----------|--------|------------|------------------|
| Test case 1 | Description here | should_have | draft | Step 1\nStep 2 | Result 1\nResult 2 |
| Test case 2 | Description here | must_have | approved | Step 1\nStep 2 | Result 1\nResult 2 |

### Test Results Import Template

| Test Case ID | Result | Comment | Executed By | Duration (s) |
|--------------|--------|---------|-------------|--------------|
| PROJECT-123 | passed | All checks OK | user@example.com | 120 |
| PROJECT-456 | failed | Certificate mismatch | user@example.com | 45 |

## JUnit XML Mapping

The server automatically maps JUnit test results to Polarion test cases:

```xml
<testsuite name="Certificate Tests">
  <testcase classname="com.example.CertTest" name="testKubeletCA" time="1.234">
    <system-out>Test output here</system-out>
  </testcase>
  <testcase classname="com.example.CertTest" name="testCloudCA" time="0.567">
    <failure message="Certificate not found">Stack trace...</failure>
  </testcase>
</testsuite>
```

Maps to Polarion test cases via `map_test_ids` parameter.

## Architecture

### Components

```
polarion-mcp-server/
├── server.py              # Main MCP server
├── polarion_client.py     # Polarion REST API client
├── test_runs.py          # Test run management
├── integrations/
│   ├── junit_import.py   # JUnit XML parser
│   ├── spreadsheet.py    # Excel/CSV integration
│   └── webhooks.py       # CI/CD webhooks
├── examples/
│   ├── create_test_case.py
│   ├── create_test_run.py
│   ├── import_junit.py
│   └── export_to_excel.py
├── tests/
│   ├── test_client.py
│   └── test_integrations.py
├── requirements.txt
├── .env.example
└── README.md
```

### REST API Endpoints Discovered

This server uses several Polarion REST API endpoints, including some undocumented ones:

| Endpoint | Method | Purpose | Documented? |
|----------|--------|---------|-------------|
| `/projects/{id}/workitems` | POST | Create workitem | Yes |
| `/projects/{id}/workitems/{id}` | PATCH | Update workitem | Yes |
| `/projects/{id}/workitems/{id}/teststeps` | POST | **Add test steps** | **No - Discovered!** |
| `/projects/{id}/workitems/{id}/teststeps/{index}` | GET | Get test step | **No - Discovered!** |
| `/projects/{id}/workitems/{id}/teststeps/{index}` | DELETE | Delete test step | **No - Discovered!** |
| `/projects/{id}/testruns` | POST | Create test run | Yes |
| `/projects/{id}/testruns/{id}/records` | PATCH | Update test result | Yes |

## Authentication

The server uses **Personal Access Tokens (PAT)** for authentication. Get your token from:

1. Log into Polarion
2. Go to your profile settings
3. Click "Personal Access Token"
4. Create a new token (max 90 days)
5. Copy the token and set `POLARION_TOKEN` environment variable

## Security Considerations

- Never commit `POLARION_TOKEN` to version control
- Use environment variables or secure vaults
- Set `POLARION_VERIFY_SSL=true` for production
- Limit token permissions to minimum required

## Troubleshooting

### SSL Certificate Errors

For Red Hat internal Polarion:
```bash
export POLARION_VERIFY_SSL="false"
```

For production systems, download the CA certificate and use:
```bash
export POLARION_CA_CERT="/path/to/ca-cert.pem"
```

### Authentication Failures

1. Check token is valid (not expired)
2. Verify token has correct permissions
3. Check Polarion URL is correct
4. Test with curl:
```bash
curl -H "Authorization: Bearer $POLARION_TOKEN" \
  "https://polarion.engineering.redhat.com/polarion/rest/v1/projects/OSE"
```

### Test Steps Not Appearing

- Ensure you're using the `/teststeps` endpoint (not `/relationships/testSteps`)
- Check keys are exactly `["step", "expectedResult"]`
- Verify HTML escaping in values

## Contributing

Contributions welcome! Areas for improvement:
- Additional integration formats (TestRail, Zephyr, etc.)
- Bulk operations optimization
- Advanced query builders
- Test run templates
- Attachment management
- Custom field support

## License

MIT License - See LICENSE file

## Credits

Developed for Red Hat OpenShift Windows Container testing.

Discovered and documented undocumented Polarion REST API test steps endpoints.

## Support

- GitHub Issues: [Create an issue](#)
- Internal: Red Hat WINC team
- Polarion Docs: https://developer.siemens.com/polarion/

## Changelog

### v1.0.0 (2026-03-12)
- Initial release
- Test case management
- Test steps API discovery
- Test run management
- JUnit integration
- Spreadsheet import/export
- Full MCP server implementation
