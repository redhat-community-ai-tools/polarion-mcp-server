#!/usr/bin/env python3
"""
Polarion Test Steps Update Script for OCP-88278

Problem Summary:
1. PATCH on /workitems endpoint returns "Malformed JSON" for testSteps attribute
2. POST on /teststeps endpoint returns "already contains Test Steps" error
3. DELETE on individual step indexes appears to work but doesn't clear the "has steps" flag

Findings:
- The Polarion REST API has a limitation where test steps cannot be replaced programmatically
- Once steps exist (even if individually deleted), the POST endpoint won't accept new steps
- PATCH doesn't support the testSteps attribute structure

Recommendation: Manual update via Polarion Web UI
URL: https://polarion.engineering.redhat.com/polarion/#/project/OSE/workitem?id=OCP-88278
"""

import sys
sys.path.insert(0, '.')
from polarion_client import PolarionClient
import os
import json

def main():
    # Initialize client
    client = PolarionClient(
        url=os.getenv('POLARION_URL', 'https://polarion.engineering.redhat.com'),
        token=os.getenv('POLARION_TOKEN'),
        verify_ssl=os.getenv('POLARION_VERIFY_SSL', 'false').lower() == 'true'
    )
    
    project_id = os.getenv('POLARION_PROJECT', 'OSE')
    
    # Test steps to add
    test_steps = [
        ("Verify Windows nodes are ready<br/><code>oc get nodes -l kubernetes.io/os=windows</code>", 
         "All Windows nodes show STATUS \"Ready\""),
        ("Query controllerConfig for certificate data<br/><code>oc get controllerconfig machine-config-controller -o yaml</code>",
         "controllerConfig contains:<br/>- spec.kubeAPIServerServingCAData (required)<br/>- spec.cloudProviderCAData (optional)<br/>- spec.additionalTrustBundle (optional)"),
        ("Extract and verify kubelet CA certificate<br/><code>oc get controllerconfig machine-config-controller -o jsonpath='{.spec.kubeAPIServerServingCAData}' | base64 -d</code>",
         "Base64-decoded PEM certificate displayed"),
        ("Verify kubelet-ca.crt exists on Windows nodes<br/><code>Get-Item C:\\k\\kubelet-ca.crt</code>",
         "File exists at C:\\k\\kubelet-ca.crt"),
        ("Verify kubelet-ca.crt matches controllerConfig<br/><code>Get-Content C:\\k\\kubelet-ca.crt -Raw</code>",
         "Certificate content matches controllerConfig.spec.kubeAPIServerServingCAData"),
        ("Verify cloud provider CA (if configured)<br/>Check: <code>oc get controllerconfig machine-config-controller -o jsonpath='{.spec.cloudProviderCAData}'</code><br/>If configured: <code>Get-Item C:\\k\\ca-bundle.crt</code>",
         "If configured: file exists and matches controllerConfig data<br/>If not configured: validation skipped (e.g., AWS)"),
        ("Verify user CA bundle (if configured)<br/><code>Get-ChildItem -Path Cert:\\LocalMachine\\Root | Measure-Object</code>",
         "If configured: certificates in Windows store, count > 0<br/>If not configured: validation skipped"),
        ("Verify kubelet service is running<br/><code>Get-Service kubelet</code>",
         "Kubelet service Status: Running"),
        ("Verify Windows nodes remain Ready<br/><code>oc get nodes -l kubernetes.io/os=windows -o wide</code>",
         "All Windows nodes Ready, no certificate errors")
    ]
    
    print("=" * 80)
    print("Polarion Test Steps Update - OCP-88278")
    print("=" * 80)
    print()
    print("ISSUE: Cannot update test steps programmatically via REST API")
    print()
    print("Errors encountered:")
    print("1. POST /teststeps: 'already contains Test Steps'")
    print("2. PATCH /workitems: 'Malformed JSON' at testSteps attribute")
    print()
    print("=" * 80)
    print("SOLUTION: Manual update required")
    print("=" * 80)
    print()
    print(f"URL: https://polarion.engineering.redhat.com/polarion/#/project/{project_id}/workitem?id=OCP-88278")
    print()
    print("Test Steps to Add (9 steps):")
    print()
    
    for i, (step, expected) in enumerate(test_steps, 1):
        print(f"Step {i}:")
        print(f"  Instruction: {step[:100]}{'...' if len(step) > 100 else ''}")
        print(f"  Expected: {expected[:100]}{'...' if len(expected) > 100 else ''}")
        print()
    
    print("=" * 80)
    print("Full test steps content saved to: polarion_test_steps_ocp88278.json")
    print("=" * 80)
    
    # Save to JSON for reference
    steps_json = []
    for i, (step, expected) in enumerate(test_steps, 1):
        steps_json.append({
            "stepNumber": i,
            "stepInstruction": step,
            "stepExpectedResult": expected
        })
    
    with open('polarion_test_steps_ocp88278.json', 'w') as f:
        json.dump(steps_json, f, indent=2)
    
    print("\nAlternative: Copy test steps from:")
    print("  WINC-1607-polarion-test-case.md")

if __name__ == '__main__':
    main()
