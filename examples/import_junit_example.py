#!/usr/bin/env python3
"""
Example: Import JUnit Test Results
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from polarion_client import PolarionClient
from integrations.junit_import import JUnitImporter

# Initialize client
client = PolarionClient(
    url=os.getenv("POLARION_URL"),
    token=os.getenv("POLARION_TOKEN"),
    verify_ssl=False
)

# Initialize JUnit importer
junit_importer = JUnitImporter(client)

# Map JUnit test names to Polarion test case IDs
test_id_mapping = {
    "com.example.winc.CertificateTest.testKubeletCA": "PROJECT-123",
    "com.example.winc.CertificateTest.testCloudProviderCA": "PROJECT-456",
    "com.example.winc.CertificateTest.testUserCABundle": "PROJECT-789"
}

# Import results
result = junit_importer.import_junit_results(
    junit_file="/tmp/junit-results.xml",
    test_run_id="OSE-TR-12345",
    project_id=os.getenv("POLARION_PROJECT", "OSE"),
    map_test_ids=test_id_mapping,
    auto_create_test_run=False
)

print("Import result:")
print(result)
