# Polarion MCP Server Examples

This directory contains example scripts showing how to use the Polarion MCP Server.

## Prerequisites

```bash
export POLARION_URL="https://polarion.example.com"
export POLARION_TOKEN="your-bearer-token"
export POLARION_PROJECT="YOUR_PROJECT"
```

## Examples

### Add Test Steps
Shows how to add test steps to an existing test case.

```bash
python3 examples/add_test_steps_example.py
```

Edit the script to replace `YOUR-TEST-CASE-ID` with your actual test case ID.

## Creating Your Own Scripts

Use these examples as templates for your own automation:

1. Copy an example script
2. Modify the test case IDs and data
3. Run against your Polarion instance
4. Never commit credentials or tokens
