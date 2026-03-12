"""
Polarion REST API Client with SOAP API support
Core client for interacting with Polarion REST and SOAP APIs
"""

import os
import requests
import base64
from typing import Optional, Dict, Any, List


class PolarionClient:
    """Client for Polarion REST API operations with SOAP fallback"""

    def __init__(
        self,
        url: str,
        token: str,
        verify_ssl: bool = True,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.url = url
        self.token = token
        self.verify_ssl = verify_ssl
        self.base_url = f"{url}/polarion/rest/v1"
        self.username = username
        self.password = password
        self.soap_url = f"{url}/polarion/ws/services/TestManagementWebService"

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Polarion REST API"""

        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=30,
                verify=self.verify_ssl
            )

            if response.status_code == 401:
                return {
                    "error": "Authentication failed. Check POLARION_TOKEN.",
                    "status": 401
                }

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    return {
                        "error": error_data.get("errors", [{}])[0].get("detail", "Unknown error"),
                        "status": response.status_code,
                        "response": error_data
                    }
                except:
                    return {
                        "error": response.text,
                        "status": response.status_code
                    }

            return response.json() if response.content else {"success": True}

        except Exception as e:
            return {"error": str(e), "status": 0}

    def test_connection(self, project_id: str) -> Dict[str, Any]:
        """Test connection to Polarion"""
        result = self._make_request("GET", f"projects/{project_id}")

        if "error" in result:
            return {
                "status": "failed",
                "message": "Connection test failed",
                "error": result["error"]
            }

        project_data = result.get("data", {})
        return {
            "status": "success",
            "message": "Successfully connected to Polarion",
            "polarion_url": self.url,
            "project_id": project_data.get("id"),
            "project_name": project_data.get("attributes", {}).get("name"),
            "authentication": "verified"
        }

    def create_test_case(
        self,
        title: str,
        description: str,
        project_id: str,
        test_steps: Optional[List[Dict[str, str]]] = None,
        severity: str = "should_have",
        status: str = "draft",
        blank_slate_strategy: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new test case with optional immediate test steps

        Args:
            title: Test case title
            description: Test case description
            project_id: Polarion project ID
            test_steps: Optional list of test step dicts with 'step' and 'expectedResult'
            severity: Test case severity
            status: Test case status
            blank_slate_strategy: If True and test_steps provided, add steps immediately
                                  before any manual edits (prevents REST API limitation)
        """

        workitem_data = {
            "data": [{
                "type": "workitems",
                "attributes": {
                    "type": "testcase",
                    "title": title,
                    "description": {
                        "type": "text/html",
                        "value": description.replace("\n", "<br/>")
                    },
                    "status": status,
                    "severity": severity
                }
            }]
        }

        result = self._make_request(
            "POST",
            f"projects/{project_id}/workitems",
            data=workitem_data
        )

        if "error" in result:
            return {
                "status": "failed",
                "error": result["error"]
            }

        test_case_data = result.get("data", [{}])[0] if isinstance(result.get("data"), list) else result.get("data", {})
        test_case_id = test_case_data.get("id", "unknown")

        response = {
            "status": "success",
            "message": "Test case created successfully",
            "test_case_id": test_case_id,
            "title": title,
            "project": project_id,
            "url": f"{self.url}/polarion/#/project/{project_id}/workitem?id={test_case_id}"
        }

        # Blank slate strategy: Add test steps immediately if provided
        if test_steps and blank_slate_strategy:
            steps_result = self.add_test_steps(test_case_id, test_steps, project_id)
            if steps_result["status"] == "success":
                response["message"] += f" with {len(test_steps)} test steps"
                response["test_steps_added"] = len(test_steps)
            else:
                response["warning"] = f"Test case created but failed to add steps: {steps_result.get('error')}"

        return response

    def _soap_set_test_steps(
        self,
        test_case_id: str,
        test_steps: List[Dict[str, str]],
        project_id: str
    ) -> Dict[str, Any]:
        """Set test steps using SOAP API (requires username/password)"""

        if not self.username or not self.password:
            return {
                "status": "failed",
                "error": "SOAP API requires username and password. Set POLARION_USERNAME and POLARION_PASSWORD environment variables."
            }

        # Build SOAP request
        work_item_uri = f"subterra:data-service:objects:/default/{project_id}${{WorkItem}}{test_case_id}"

        steps_xml = ""
        for idx, step in enumerate(test_steps):
            steps_xml += f"""
            <steps>
                <index>{idx}</index>
                <values>
                    <Text>
                        <type>text/html</type>
                        <content>{step.get('step', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</content>
                        <contentLossy>false</contentLossy>
                    </Text>
                    <Text>
                        <type>text/html</type>
                        <content>{step.get('expectedResult', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</content>
                        <contentLossy>false</contentLossy>
                    </Text>
                </values>
            </steps>"""

        soap_request = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:tes="http://ws.polarion.com/TestManagementWebService">
   <soapenv:Header/>
   <soapenv:Body>
      <tes:setTestSteps>
         <tes:workItemURI>{work_item_uri}</tes:workItemURI>
         <tes:testSteps>
            <tes:keys>step</tes:keys>
            <tes:keys>expectedResult</tes:keys>
            {steps_xml}
         </tes:testSteps>
      </tes:setTestSteps>
   </soapenv:Body>
</soapenv:Envelope>"""

        # Make SOAP request with Basic Auth
        auth = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "",
            "Authorization": f"Basic {auth}"
        }

        try:
            response = requests.post(
                self.soap_url,
                data=soap_request,
                headers=headers,
                verify=self.verify_ssl,
                timeout=30
            )

            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": f"Added {len(test_steps)} test steps to {test_case_id} via SOAP API",
                    "test_case_id": test_case_id,
                    "steps_added": len(test_steps),
                    "method": "SOAP",
                    "url": f"{self.url}/polarion/#/project/{project_id}/workitem?id={test_case_id}"
                }
            else:
                return {
                    "status": "failed",
                    "error": f"SOAP request failed: {response.status_code} - {response.text}"
                }

        except Exception as e:
            return {
                "status": "failed",
                "error": f"SOAP API error: {str(e)}"
            }

    def add_test_steps(
        self,
        test_case_id: str,
        test_steps: List[Dict[str, str]],
        project_id: str,
        force_soap: bool = False
    ) -> Dict[str, Any]:
        """
        Add test steps to a test case

        Strategies:
        1. REST API (default): POST to /teststeps if work item has no steps
        2. SOAP API (fallback): Use when REST fails or force_soap=True

        Args:
            test_case_id: Work item ID (e.g., 'OCP-88278')
            test_steps: List of dicts with 'step' and 'expectedResult' keys
            project_id: Polarion project ID (e.g., 'OSE')
            force_soap: Force use of SOAP API instead of REST
        """

        # Force SOAP if requested
        if force_soap:
            return self._soap_set_test_steps(test_case_id, test_steps, project_id)

        try:
            # Check if test steps already exist
            check_url = f"projects/{project_id}/workitems/{test_case_id}/relationships/testSteps"
            existing = self._make_request("GET", check_url)

            has_existing_steps = (
                "error" not in existing and
                len(existing.get("data", [])) > 0
            )

            # If steps exist, try SOAP API
            if has_existing_steps:
                soap_result = self._soap_set_test_steps(test_case_id, test_steps, project_id)
                if soap_result["status"] == "success":
                    return soap_result
                else:
                    return {
                        "status": "failed",
                        "error": "Test steps already exist and SOAP API unavailable. Use force_soap=True with credentials.",
                        "soap_error": soap_result.get("error")
                    }

            # Build test steps payload for REST API
            steps_data = []
            for step in test_steps:
                step_obj = {
                    "type": "teststeps",
                    "attributes": {
                        "keys": ["step", "expectedResult"],
                        "values": [
                            {"type": "text/html", "value": step.get("step", "").replace("\n", "<br/>")},
                            {"type": "text/html", "value": step.get("expectedResult", "").replace("\n", "<br/>")}
                        ]
                    }
                }
                steps_data.append(step_obj)

            # POST test steps via REST API
            result = self._make_request(
                "POST",
                f"projects/{project_id}/workitems/{test_case_id}/teststeps",
                data={"data": steps_data}
            )

            if "error" in result:
                # REST failed, try SOAP fallback
                soap_result = self._soap_set_test_steps(test_case_id, test_steps, project_id)
                if soap_result["status"] == "success":
                    return soap_result
                else:
                    return {
                        "status": "failed",
                        "error": f"REST API failed: {result['error']}. SOAP API also unavailable.",
                        "rest_error": result["error"],
                        "soap_error": soap_result.get("error")
                    }

            created_steps = result.get("data", [])

            return {
                "status": "success",
                "message": f"Added {len(created_steps)} test steps to {test_case_id}",
                "test_case_id": test_case_id,
                "steps_added": len(created_steps),
                "method": "REST",
                "url": f"{self.url}/polarion/#/project/{project_id}/workitem?id={test_case_id}"
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

    def get_test_case(
        self,
        test_case_id: str,
        project_id: str,
        include_test_steps: bool = True
    ) -> Dict[str, Any]:
        """Get test case details"""

        params = {}
        if include_test_steps:
            params["include"] = "testSteps"

        result = self._make_request(
            "GET",
            f"projects/{project_id}/workitems/{test_case_id}",
            params=params
        )

        if "error" in result:
            return {
                "status": "failed",
                "error": result["error"]
            }

        test_case = result.get("data", {}).get("attributes", {})

        return {
            "status": "success",
            "test_case_id": test_case_id,
            "title": test_case.get("title"),
            "type": test_case.get("type"),
            "status": test_case.get("status"),
            "severity": test_case.get("severity"),
            "description": test_case.get("description", {}).get("value", ""),
            "url": f"{self.url}/polarion/#/project/{project_id}/workitem?id={test_case_id}"
        }

    def update_test_case(
        self,
        test_case_id: str,
        project_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Update test case"""

        attributes = {}
        if kwargs.get("title"):
            attributes["title"] = kwargs["title"]
        if kwargs.get("description"):
            attributes["description"] = {
                "type": "text/html",
                "value": kwargs["description"].replace("\n", "<br/>")
            }
        if kwargs.get("status"):
            attributes["status"] = kwargs["status"]
        if kwargs.get("severity"):
            attributes["severity"] = kwargs["severity"]

        if not attributes:
            return {
                "status": "failed",
                "error": "No fields provided to update"
            }

        update_data = {
            "data": {
                "type": "workitems",
                "id": f"{project_id}/{test_case_id}",
                "attributes": attributes
            }
        }

        result = self._make_request(
            "PATCH",
            f"projects/{project_id}/workitems/{test_case_id}",
            data=update_data
        )

        if "error" in result:
            return {
                "status": "failed",
                "error": result["error"]
            }

        return {
            "status": "success",
            "message": f"Test case {test_case_id} updated successfully",
            "updated_fields": list(attributes.keys())
        }

    def search_test_cases(
        self,
        query: str,
        project_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search for test cases"""

        params = {
            "query": f"type:testcase AND {query}",
            "fields[workitems]": "title,type,status,severity",
            "page[size]": limit
        }

        result = self._make_request(
            "GET",
            f"projects/{project_id}/workitems",
            params=params
        )

        if "error" in result:
            return {
                "status": "failed",
                "error": result["error"]
            }

        test_cases = result.get("data", [])
        results = []
        for tc in test_cases:
            tc_id = tc.get("id", "")
            attrs = tc.get("attributes", {})
            results.append({
                "id": tc_id,
                "title": attrs.get("title"),
                "status": attrs.get("status"),
                "severity": attrs.get("severity"),
                "url": f"{self.url}/polarion/#/project/{project_id}/workitem?id={tc_id}"
            })

        return {
            "status": "success",
            "query": query,
            "total_results": len(results),
            "test_cases": results
        }
