"""
Test Run Management
Handles creation and management of Polarion test runs
"""

from typing import Optional, Dict, Any, List


class TestRunManager:
    """Manager for Polarion test run operations"""

    def __init__(self, client):
        self.client = client

    def create_test_run(
        self,
        title: str,
        template: str,
        project_id: str,
        test_case_ids: Optional[List[str]] = None,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new test run"""

        test_run_data = {
            "data": [{
                "type": "testruns",
                "attributes": {
                    "title": title,
                    "projectId": project_id
                }
            }]
        }

        # Add template only if provided (not all Polarion installations support it)
        if template:
            test_run_data["data"][0]["attributes"]["templateId"] = template

        # Add test cases via query if provided
        if query:
            test_run_data["data"][0]["attributes"]["query"] = query

        # Create the test run first
        result = self.client._make_request(
            "POST",
            f"projects/{project_id}/testruns",
            data=test_run_data
        )

        if "error" in result:
            return {
                "status": "failed",
                "error": result["error"]
            }

        test_run = result.get("data", [{}])[0] if isinstance(result.get("data"), list) else result.get("data", {})
        test_run_id = test_run.get("id", "unknown")

        # Add test cases after creation if provided
        if test_case_ids:
            add_result = self.add_test_cases_to_run(test_run_id, test_case_ids, project_id)
            if add_result.get("status") != "success":
                return {
                    "status": "partial",
                    "message": f"Test run created but failed to add test cases: {add_result.get('error')}",
                    "test_run_id": test_run_id,
                    "error": add_result.get("error")
                }

        return {
            "status": "success",
            "message": "Test run created successfully",
            "test_run_id": test_run_id,
            "title": title,
            "url": f"{self.client.url}/polarion/redirect/project/{project_id}/testrun?id={test_run_id}"
        }

    def update_test_result(
        self,
        test_run_id: str,
        test_case_id: str,
        result: str,
        project_id: str,
        comment: Optional[str] = None,
        executed_by: Optional[str] = None,
        duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update test result within a test run"""
        from datetime import datetime

        # Strip project prefix from test_run_id if present (e.g., "OSE/20260423-0808" -> "20260423-0808")
        if "/" in test_run_id:
            test_run_id = test_run_id.split("/", 1)[1]

        # Build the test record update
        attributes = {
            "result": result,
            "executed": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        }

        if comment:
            attributes["comment"] = {
                "type": "text/html",
                "value": comment.replace("\n", "<br/>")
            }

        if executed_by:
            attributes["executedBy"] = executed_by

        if duration:
            attributes["duration"] = duration

        # Test record ID format includes project, test case, and iteration
        test_record_id = f"{project_id}/{test_run_id}/{project_id}/{test_case_id}/0"

        update_data = {
            "data": {
                "type": "testrecords",
                "id": test_record_id,
                "attributes": attributes
            }
        }

        # Update the test record
        # Test record ID format: {project_id}/{test_case_id}/0 (0 is the iteration number)
        endpoint = f"projects/{project_id}/testruns/{test_run_id}/testrecords/{project_id}/{test_case_id}/0"

        result_data = self.client._make_request(
            "PATCH",
            endpoint,
            data=update_data
        )

        if "error" in result_data:
            return {
                "status": "failed",
                "error": result_data["error"]
            }

        return {
            "status": "success",
            "message": f"Updated result for {test_case_id} in {test_run_id}",
            "test_run_id": test_run_id,
            "test_case_id": test_case_id,
            "result": result
        }

    def get_test_run_status(
        self,
        test_run_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """Get test run status and statistics"""

        # Strip project prefix from test_run_id if present (e.g., "OSE/20260423-0808" -> "20260423-0808")
        if "/" in test_run_id:
            test_run_id = test_run_id.split("/", 1)[1]

        result = self.client._make_request(
            "GET",
            f"projects/{project_id}/testruns/{test_run_id}"
        )

        if "error" in result:
            return {
                "status": "failed",
                "error": result["error"]
            }

        test_run = result.get("data", {}).get("attributes", {})

        # Get test records with result field included
        records_result = self.client._make_request(
            "GET",
            f"projects/{project_id}/testruns/{test_run_id}/testrecords",
            params={"fields[testrecords]": "result"}
        )

        records = records_result.get("data", [])

        # Calculate statistics
        stats = {
            "total": len(records),
            "passed": 0,
            "failed": 0,
            "blocked": 0,
            "not_executed": 0
        }

        for record in records:
            result_val = record.get("attributes", {}).get("result", "not_executed")
            if result_val == "passed":
                stats["passed"] += 1
            elif result_val == "failed":
                stats["failed"] += 1
            elif result_val == "blocked":
                stats["blocked"] += 1
            else:
                stats["not_executed"] += 1

        return {
            "status": "success",
            "test_run_id": test_run_id,
            "title": test_run.get("title"),
            "run_status": test_run.get("status"),
            "statistics": stats,
            "url": f"{self.client.url}/polarion/redirect/project/{project_id}/testrun?id={test_run_id}"
        }

    def update_test_run_description(
        self,
        test_run_id: str,
        description: str,
        project_id: str
    ) -> Dict[str, Any]:
        """Update test run description"""

        # Strip project prefix from test_run_id if present (e.g., "OSE/20260423-0808" -> "20260423-0808")
        if "/" in test_run_id:
            test_run_id = test_run_id.split("/", 1)[1]

        # Build the update payload
        update_data = {
            "data": {
                "type": "testruns",
                "id": f"{project_id}/{test_run_id}",
                "attributes": {
                    "description": {
                        "type": "text/plain",
                        "value": description
                    }
                }
            }
        }

        result = self.client._make_request(
            "PATCH",
            f"projects/{project_id}/testruns/{test_run_id}",
            data=update_data
        )

        if "error" in result:
            return {
                "status": "failed",
                "error": result["error"]
            }

        return {
            "status": "success",
            "message": f"Updated description for test run {test_run_id}",
            "test_run_id": test_run_id
        }

    def update_test_run_status(
        self,
        test_run_id: str,
        status: str,
        project_id: str
    ) -> Dict[str, Any]:
        """Update test run status (notrun, inprogress, finished)"""

        # Strip project prefix from test_run_id if present (e.g., "OSE/20260423-0808" -> "20260423-0808")
        if "/" in test_run_id:
            test_run_id = test_run_id.split("/", 1)[1]

        # Build the update payload
        update_data = {
            "data": {
                "type": "testruns",
                "id": f"{project_id}/{test_run_id}",
                "attributes": {
                    "status": status
                }
            }
        }

        result = self.client._make_request(
            "PATCH",
            f"projects/{project_id}/testruns/{test_run_id}",
            data=update_data
        )

        if "error" in result:
            return {
                "status": "failed",
                "error": result["error"]
            }

        return {
            "status": "success",
            "message": f"Updated status for test run {test_run_id} to {status}",
            "test_run_id": test_run_id
        }

    def add_test_cases_to_run(
        self,
        test_run_id: str,
        test_case_ids: List[str],
        project_id: str
    ) -> Dict[str, Any]:
        """Add additional test cases to an existing test run by creating test records"""

        # Strip project prefix from test_run_id if present (e.g., "OSE/20260423-0808" -> "20260423-0808")
        if "/" in test_run_id:
            test_run_id = test_run_id.split("/", 1)[1]

        # Create test records with relationships to test cases
        update_data = {
            "data": [
                {
                    "type": "testrecords",
                    "relationships": {
                        "testCase": {
                            "data": {
                                "type": "workitems",
                                "id": f"{project_id}/{tc_id}"
                            }
                        }
                    }
                }
                for tc_id in test_case_ids
            ]
        }

        result = self.client._make_request(
            "POST",
            f"projects/{project_id}/testruns/{test_run_id}/testrecords",
            data=update_data
        )

        if "error" in result:
            return {
                "status": "failed",
                "error": result["error"]
            }

        return {
            "status": "success",
            "message": f"Added {len(test_case_ids)} test cases to {test_run_id}",
            "test_run_id": test_run_id,
            "added_count": len(test_case_ids)
        }
