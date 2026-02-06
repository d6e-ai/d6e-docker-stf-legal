"""
Shared utility functions for D6E Legal STFs.

Overview:
  Common functions used across all legal STF modules including:
  - D6E API communication
  - Input/output handling
  - Error handling
  - Logging configuration
  - Legal-specific helper utilities (risk scoring, classification, etc.)

Limitations:
  - SQL execution is restricted by D6E policy system
  - No DDL operations allowed
"""

import sys
import json
import logging
import requests
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def configureLogging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging to stderr (stdout is reserved for output).

    Args:
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        stream=sys.stderr,
        level=level,
        format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
    )
    return logging.getLogger(__name__)


logger = configureLogging()


def createSession() -> requests.Session:
    """
    Create HTTP session with retry logic for resilient API calls.

    Returns:
        Configured requests session with retry handling
    """
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def readInput() -> Dict[str, Any]:
    """
    Read and parse JSON input from stdin.

    Returns:
        Parsed input dictionary containing:
        - workspace_id: UUID of the workspace
        - stf_id: UUID of this STF
        - caller: UUID of the calling entity (or null)
        - api_url: Internal API URL
        - api_token: Authentication token
        - input: User-defined parameters
        - sources: Previous step outputs

    Raises:
        ValueError: If input is not valid JSON
    """
    try:
        inputData = json.load(sys.stdin)
        logger.info(
            f"Received input for operation: "
            f"{inputData.get('input', {}).get('operation', 'unknown')}"
        )
        return inputData
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON input: {str(e)}")


def writeOutput(result: Dict[str, Any]) -> None:
    """
    Write successful result to stdout.

    Args:
        result: Result dictionary to output
    """
    output = {"output": result}
    print(json.dumps(output, default=str))


def writeError(error: Exception, errorType: Optional[str] = None) -> None:
    """
    Write error response to stdout and exit with code 1.

    Args:
        error: Exception that occurred
        errorType: Optional error type override
    """
    errorOutput = {
        "error": str(error),
        "type": errorType or type(error).__name__
    }
    print(json.dumps(errorOutput))
    sys.exit(1)


class D6eApiClient:
    """
    Client for D6E internal SQL API.

    Handles authentication and SQL execution against workspace databases.
    """

    def __init__(self, apiUrl: str, apiToken: str, workspaceId: str, stfId: str):
        """
        Initialize API client.

        Args:
            apiUrl: Base URL for D6E API
            apiToken: Authentication token
            workspaceId: Workspace UUID
            stfId: STF UUID for policy evaluation
        """
        self.apiUrl = apiUrl
        self.apiToken = apiToken
        self.workspaceId = workspaceId
        self.stfId = stfId
        self.session = createSession()

    def _getHeaders(self) -> Dict[str, str]:
        """Get standard headers for API requests."""
        return {
            "Authorization": f"Bearer {self.apiToken}",
            "X-Internal-Bypass": "true",
            "X-Workspace-ID": self.workspaceId,
            "X-STF-ID": self.stfId,
            "Content-Type": "application/json"
        }

    def executeSql(self, sql: str) -> Dict[str, Any]:
        """
        Execute SQL query via D6E API.

        Args:
            sql: SQL query to execute (SELECT only, no DDL)

        Returns:
            Query results as dictionary with:
            - columns: List of column names
            - rows: List of row data

        Raises:
            Exception: If SQL execution fails
        """
        url = f"{self.apiUrl}/api/v1/workspaces/{self.workspaceId}/sql"

        logger.debug(f"Executing SQL: {sql[:100]}...")

        try:
            response = self.session.post(
                url,
                json={"sql": sql},
                headers=self._getHeaders(),
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            raise Exception(f"SQL execution timeout. Query: {sql[:100]}...")
        except requests.RequestException as e:
            raise Exception(f"SQL execution failed: {str(e)}. Query: {sql[:100]}...")

    def executeMultipleSql(self, statements: List[str]) -> List[Dict[str, Any]]:
        """
        Execute multiple SQL statements sequentially.

        Args:
            statements: List of SQL queries

        Returns:
            List of results for each statement
        """
        results = []
        for sql in statements:
            results.append(self.executeSql(sql))
        return results


def createApiClient(inputData: Dict[str, Any]) -> D6eApiClient:
    """
    Create D6E API client from standard input data.

    Args:
        inputData: Parsed input from stdin

    Returns:
        Configured API client
    """
    return D6eApiClient(
        apiUrl=inputData["api_url"],
        apiToken=inputData["api_token"],
        workspaceId=inputData["workspace_id"],
        stfId=inputData["stf_id"]
    )


def validateRequiredFields(userInput: Dict[str, Any], requiredFields: List[str]) -> None:
    """
    Validate that all required fields are present in user input.

    Args:
        userInput: User input dictionary
        requiredFields: List of required field names

    Raises:
        ValueError: If any required field is missing
    """
    missingFields = [f for f in requiredFields if f not in userInput]
    if missingFields:
        raise ValueError(f"Missing required fields: {', '.join(missingFields)}")


def generateId() -> str:
    """
    Generate a unique identifier.

    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def getCurrentTimestamp() -> str:
    """
    Get current timestamp in ISO format.

    Returns:
        ISO formatted timestamp string
    """
    return datetime.utcnow().isoformat() + "Z"


def calculateDeadline(startDate: str, days: int) -> str:
    """
    Calculate a deadline date from a start date.

    Args:
        startDate: Start date in YYYY-MM-DD format
        days: Number of calendar days to add

    Returns:
        Deadline date in YYYY-MM-DD format
    """
    start = datetime.strptime(startDate, "%Y-%m-%d")
    deadline = start + timedelta(days=days)
    return deadline.strftime("%Y-%m-%d")


def calculateBusinessDays(startDate: str, days: int) -> str:
    """
    Calculate a deadline date using business days only.

    Args:
        startDate: Start date in YYYY-MM-DD format
        days: Number of business days to add

    Returns:
        Deadline date in YYYY-MM-DD format
    """
    current = datetime.strptime(startDate, "%Y-%m-%d")
    addedDays = 0
    while addedDays < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            addedDays += 1
    return current.strftime("%Y-%m-%d")


# Risk classification helpers
RISK_LEVELS = {
    "GREEN": {"min_score": 1, "max_score": 4, "label": "Low Risk"},
    "YELLOW": {"min_score": 5, "max_score": 9, "label": "Medium Risk"},
    "ORANGE": {"min_score": 10, "max_score": 15, "label": "High Risk"},
    "RED": {"min_score": 16, "max_score": 25, "label": "Critical Risk"}
}


def classifyRiskLevel(score: int) -> Dict[str, Any]:
    """
    Classify risk level based on score.

    Args:
        score: Risk score (1-25)

    Returns:
        Dictionary with color, label, and score range
    """
    for color, info in RISK_LEVELS.items():
        if info["min_score"] <= score <= info["max_score"]:
            return {
                "color": color,
                "label": info["label"],
                "score": score,
                "min_score": info["min_score"],
                "max_score": info["max_score"]
            }
    raise ValueError(f"Invalid risk score: {score}. Must be between 1 and 25.")


def classifyNdaColor(issues: Dict[str, List[str]]) -> str:
    """
    Classify NDA based on detected issues.

    Args:
        issues: Dictionary with 'red', 'yellow', and 'green' issue lists

    Returns:
        Classification color: GREEN, YELLOW, or RED
    """
    if issues.get("red"):
        return "RED"
    if issues.get("yellow"):
        return "YELLOW"
    return "GREEN"


def classifyContractDeviation(deviationType: str) -> str:
    """
    Classify contract deviation severity.

    Args:
        deviationType: Type of deviation detected

    Returns:
        Classification color: GREEN, YELLOW, or RED
    """
    redDeviations = [
        "uncapped_liability", "no_liability_clause", "uncapped_indemnity",
        "ip_assignment_preexisting", "no_dpa_with_personal_data",
        "unreasonable_noncompete", "problematic_jurisdiction"
    ]
    yellowDeviations = [
        "low_liability_cap", "unilateral_ip_indemnity", "short_auto_renewal_notice",
        "non_preferred_jurisdiction", "broad_definition", "missing_carveout"
    ]

    if deviationType in redDeviations:
        return "RED"
    if deviationType in yellowDeviations:
        return "YELLOW"
    return "GREEN"
