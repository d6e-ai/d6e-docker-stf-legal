#!/usr/bin/env python3
"""
D6E Docker STF: Compliance

Overview:
  Handles privacy regulation compliance tasks including DPA reviews,
  data subject request processing, and regulatory timeline management.

Main Operations:
  - review_dpa: Review Data Processing Agreement against checklist
  - process_dsr: Process and track data subject requests
  - get_response_timeline: Get response timeline for applicable regulation
  - check_exemptions: Check applicable exemptions for a DSR
  - generate_dpa_checklist: Generate blank DPA review checklist
  - get_regulation_overview: Get overview of a specific regulation

Limitations:
  - Provides legal workflow assistance, not legal advice
  - Compliance determinations should be reviewed by qualified professionals
  - Regulatory requirements change frequently; verify with authoritative sources
"""

import sys
import os
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from utils import (
    logger, readInput, writeOutput, writeError,
    createApiClient, validateRequiredFields,
    generateId, getCurrentTimestamp,
    calculateDeadline, calculateBusinessDays
)


# DSR types
DSR_TYPES = [
    "access", "rectification", "erasure", "restriction",
    "portability", "objection", "opt_out_sale", "limit_sensitive_pi"
]

# Response timelines by regulation
RESPONSE_TIMELINES = {
    "GDPR": {
        "initial_acknowledgment": "Best practice: promptly",
        "substantive_response_days": 30,
        "extension_days": 60,
        "extension_notice_required": True
    },
    "CCPA": {
        "initial_acknowledgment_business_days": 10,
        "substantive_response_days": 45,
        "extension_days": 45,
        "extension_notice_required": True
    },
    "UK_GDPR": {
        "initial_acknowledgment": "Best practice: promptly",
        "substantive_response_days": 30,
        "extension_days": 60,
        "extension_notice_required": True
    },
    "LGPD": {
        "initial_acknowledgment": "Not specified",
        "substantive_response_days": 15,
        "extension_days": 0,
        "extension_notice_required": False
    }
}

# DPA required elements (GDPR Article 28)
DPA_REQUIRED_ELEMENTS = [
    "subject_matter_and_duration",
    "nature_and_purpose",
    "type_of_personal_data",
    "categories_of_data_subjects",
    "controller_obligations_and_rights"
]

DPA_PROCESSOR_OBLIGATIONS = [
    "process_on_instructions_only",
    "confidentiality_commitment",
    "security_measures",
    "sub_processor_requirements",
    "data_subject_rights_assistance",
    "security_breach_assistance",
    "deletion_or_return_on_termination",
    "audit_rights",
    "breach_notification"
]


class ComplianceAnalyzer:
    """
    Handles privacy compliance tasks including DPA reviews and DSR processing.
    """

    def __init__(self, apiClient=None):
        """
        Initialize compliance analyzer.

        Args:
            apiClient: Optional D6eApiClient for database operations
        """
        self.api = apiClient

    def reviewDpa(self, dpaData: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review a Data Processing Agreement against compliance checklist.

        Args:
            dpaData: DPA details including:
                - counterparty: Name of the processor/controller
                - required_elements: Dict of element -> present (bool)
                - processor_obligations: Dict of obligation -> present (bool)
                - international_transfers: Dict of transfer mechanism details
                - practical_considerations: Dict of practical items
                - breach_notification_hours: Number or None
                - sub_processor_authorization: "specific", "general_with_notice", "blanket"

        Returns:
            DPA review result with findings and compliance status
        """
        logger.info(f"Reviewing DPA for: {dpaData.get('counterparty', 'unknown')}")

        findings = []
        compliantCount = 0
        nonCompliantCount = 0
        warningCount = 0
        totalChecks = 0

        # Check required elements
        requiredElements = dpaData.get("required_elements", {})
        for element in DPA_REQUIRED_ELEMENTS:
            totalChecks += 1
            present = requiredElements.get(element, False)
            if present:
                compliantCount += 1
                findings.append({
                    "section": "Required Elements",
                    "item": element.replace("_", " ").title(),
                    "status": "compliant",
                    "severity": "green"
                })
            else:
                nonCompliantCount += 1
                findings.append({
                    "section": "Required Elements",
                    "item": element.replace("_", " ").title(),
                    "status": "missing",
                    "severity": "red",
                    "recommendation": f"Add {element.replace('_', ' ')} to the DPA (GDPR Article 28 requirement)"
                })

        # Check processor obligations
        processorObligations = dpaData.get("processor_obligations", {})
        for obligation in DPA_PROCESSOR_OBLIGATIONS:
            totalChecks += 1
            present = processorObligations.get(obligation, False)
            if present:
                compliantCount += 1
                findings.append({
                    "section": "Processor Obligations",
                    "item": obligation.replace("_", " ").title(),
                    "status": "compliant",
                    "severity": "green"
                })
            else:
                nonCompliantCount += 1
                findings.append({
                    "section": "Processor Obligations",
                    "item": obligation.replace("_", " ").title(),
                    "status": "missing",
                    "severity": "red",
                    "recommendation": f"Include {obligation.replace('_', ' ')} obligation"
                })

        # Check breach notification timeline
        breachHours = dpaData.get("breach_notification_hours")
        totalChecks += 1
        if breachHours is not None:
            if breachHours <= 48:
                compliantCount += 1
                findings.append({
                    "section": "Breach Notification",
                    "item": f"Notification within {breachHours} hours",
                    "status": "compliant",
                    "severity": "green"
                })
            elif breachHours <= 72:
                warningCount += 1
                findings.append({
                    "section": "Breach Notification",
                    "item": f"Notification within {breachHours} hours",
                    "status": "acceptable",
                    "severity": "yellow",
                    "recommendation": "Consider negotiating to 24-48 hours for buffer"
                })
            else:
                nonCompliantCount += 1
                findings.append({
                    "section": "Breach Notification",
                    "item": f"Notification within {breachHours} hours",
                    "status": "non_compliant",
                    "severity": "red",
                    "recommendation": "Must be within 72 hours to enable regulatory notification. Negotiate to 24-48 hours."
                })

        # Check sub-processor authorization
        subAuth = dpaData.get("sub_processor_authorization", "unknown")
        totalChecks += 1
        if subAuth == "specific":
            compliantCount += 1
            findings.append({
                "section": "Sub-Processors",
                "item": "Specific authorization required",
                "status": "compliant",
                "severity": "green"
            })
        elif subAuth == "general_with_notice":
            compliantCount += 1
            findings.append({
                "section": "Sub-Processors",
                "item": "General authorization with change notification",
                "status": "compliant",
                "severity": "green",
                "note": "Ensure right to object is included"
            })
        elif subAuth == "blanket":
            nonCompliantCount += 1
            findings.append({
                "section": "Sub-Processors",
                "item": "Blanket authorization without notification",
                "status": "non_compliant",
                "severity": "red",
                "recommendation": "Require notification of sub-processor changes with right to object"
            })

        # Check international transfers
        transfers = dpaData.get("international_transfers", {})
        if transfers:
            totalChecks += 1
            hasMechanism = transfers.get("has_transfer_mechanism", False)
            if hasMechanism:
                mechanism = transfers.get("mechanism", "unknown")
                sccsVersion = transfers.get("sccs_version", "")
                if sccsVersion and "2021" not in sccsVersion:
                    warningCount += 1
                    findings.append({
                        "section": "International Transfers",
                        "item": f"Transfer mechanism: {mechanism}",
                        "status": "outdated",
                        "severity": "yellow",
                        "recommendation": "Update to current EU SCCs (June 2021 version)"
                    })
                else:
                    compliantCount += 1
                    findings.append({
                        "section": "International Transfers",
                        "item": f"Transfer mechanism: {mechanism}",
                        "status": "compliant",
                        "severity": "green"
                    })
            else:
                nonCompliantCount += 1
                findings.append({
                    "section": "International Transfers",
                    "item": "No transfer mechanism identified",
                    "status": "missing",
                    "severity": "red",
                    "recommendation": "Identify and implement appropriate transfer mechanism (SCCs, adequacy decision, BCRs)"
                })

        # Overall compliance status
        if nonCompliantCount > 0:
            overallStatus = "non_compliant"
        elif warningCount > 0:
            overallStatus = "needs_attention"
        else:
            overallStatus = "compliant"

        return {
            "review_id": generateId(),
            "timestamp": getCurrentTimestamp(),
            "counterparty": dpaData.get("counterparty", "Unknown"),
            "overall_status": overallStatus,
            "score": {
                "total_checks": totalChecks,
                "compliant": compliantCount,
                "non_compliant": nonCompliantCount,
                "warnings": warningCount,
                "compliance_percentage": round(compliantCount / totalChecks * 100, 1) if totalChecks > 0 else 0
            },
            "findings": findings,
            "summary": self._generateDpaSummary(
                overallStatus, nonCompliantCount, warningCount, dpaData
            )
        }

    def processDsr(self, dsrData: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a data subject request.

        Args:
            dsrData: DSR details including:
                - request_type: Type of DSR (access, erasure, etc.)
                - regulation: Applicable regulation (GDPR, CCPA, etc.)
                - requester_name: Name of the requester
                - requester_location: Location/jurisdiction of requester
                - date_received: Date request was received (YYYY-MM-DD)
                - identity_verified: Whether identity has been verified
                - subject_to_litigation_hold: Whether data is under litigation hold
                - involves_minor: Whether request involves a minor
                - special_category_data: Whether special category data involved

        Returns:
            DSR processing result with timelines, steps, and exemption checks
        """
        logger.info(f"Processing DSR type: {dsrData.get('request_type', 'unknown')}")

        requestType = dsrData.get("request_type", "access")
        regulation = dsrData.get("regulation", "GDPR").upper()
        dateReceived = dsrData.get("date_received")

        if requestType not in DSR_TYPES:
            raise ValueError(
                f"Unknown DSR type: {requestType}. Valid types: {', '.join(DSR_TYPES)}"
            )

        # Calculate timeline
        timeline = self._calculateDsrTimeline(regulation, dateReceived)

        # Check for escalation triggers
        escalationTriggers = self._checkDsrEscalationTriggers(dsrData)

        # Check exemptions
        exemptions = self._checkExemptions(dsrData)

        # Generate processing steps
        processingSteps = self._generateProcessingSteps(requestType, dsrData)

        return {
            "dsr_id": generateId(),
            "timestamp": getCurrentTimestamp(),
            "request_type": requestType,
            "regulation": regulation,
            "requester": dsrData.get("requester_name", "Unknown"),
            "date_received": dateReceived,
            "timeline": timeline,
            "identity_verified": dsrData.get("identity_verified", False),
            "escalation_triggers": escalationTriggers,
            "has_escalation_triggers": len(escalationTriggers) > 0,
            "applicable_exemptions": exemptions,
            "processing_steps": processingSteps,
            "status": "requires_escalation" if escalationTriggers else "proceed"
        }

    def getResponseTimeline(
        self,
        regulation: str,
        dateReceived: str
    ) -> Dict[str, Any]:
        """
        Get response timeline for a specific regulation.

        Args:
            regulation: Regulation name (GDPR, CCPA, etc.)
            dateReceived: Date request received (YYYY-MM-DD)

        Returns:
            Timeline with key dates
        """
        return self._calculateDsrTimeline(regulation.upper(), dateReceived)

    def checkExemptions(self, dsrData: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check applicable exemptions for a DSR.

        Args:
            dsrData: DSR details

        Returns:
            List of applicable exemptions
        """
        return {
            "exemptions": self._checkExemptions(dsrData),
            "request_type": dsrData.get("request_type", "unknown"),
            "regulation": dsrData.get("regulation", "GDPR")
        }

    def generateDpaChecklist(
        self,
        includeTransfers: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a blank DPA review checklist.

        Args:
            includeTransfers: Whether to include international transfer checks

        Returns:
            Structured DPA review checklist
        """
        checklist = {
            "generated_at": getCurrentTimestamp(),
            "sections": [
                {
                    "name": "Required Elements (GDPR Article 28)",
                    "items": [
                        {"check": e.replace("_", " ").title(), "status": "pending", "key": e}
                        for e in DPA_REQUIRED_ELEMENTS
                    ]
                },
                {
                    "name": "Processor Obligations",
                    "items": [
                        {"check": o.replace("_", " ").title(), "status": "pending", "key": o}
                        for o in DPA_PROCESSOR_OBLIGATIONS
                    ]
                },
                {
                    "name": "Practical Considerations",
                    "items": [
                        {"check": "Liability alignment with main agreement", "status": "pending"},
                        {"check": "Termination alignment", "status": "pending"},
                        {"check": "Data processing locations specified", "status": "pending"},
                        {"check": "Security standards (SOC 2, ISO 27001)", "status": "pending"},
                        {"check": "Insurance coverage adequate", "status": "pending"}
                    ]
                }
            ]
        }

        if includeTransfers:
            checklist["sections"].append({
                "name": "International Transfers",
                "items": [
                    {"check": "Transfer mechanism identified", "status": "pending"},
                    {"check": "SCCs version current (June 2021)", "status": "pending"},
                    {"check": "Correct SCC module selected", "status": "pending"},
                    {"check": "Transfer impact assessment completed", "status": "pending"},
                    {"check": "Supplementary measures documented", "status": "pending"},
                    {"check": "UK addendum included (if UK data)", "status": "pending"}
                ]
            })

        return checklist

    def getRegulationOverview(self, regulation: str) -> Dict[str, Any]:
        """
        Get overview of a specific privacy regulation.

        Args:
            regulation: Regulation name

        Returns:
            Regulation overview with key obligations
        """
        overviews = {
            "GDPR": {
                "name": "General Data Protection Regulation",
                "jurisdiction": "EU/EEA",
                "key_obligations": [
                    "Lawful basis for processing",
                    "Data subject rights (access, rectification, erasure, portability, restriction, objection)",
                    "Data protection impact assessments",
                    "Breach notification (72 hours to supervisory authority)",
                    "Records of processing activities (Article 30)",
                    "International transfer safeguards",
                    "DPO appointment (if required)"
                ],
                "response_timeline": RESPONSE_TIMELINES["GDPR"],
                "penalties": "Up to EUR 20M or 4% of annual global turnover"
            },
            "CCPA": {
                "name": "California Consumer Privacy Act / CPRA",
                "jurisdiction": "California, USA",
                "key_obligations": [
                    "Right to know (disclosure of PI collected, used, shared)",
                    "Right to delete",
                    "Right to opt-out of sale/sharing",
                    "Right to correct (CPRA)",
                    "Right to limit use of sensitive PI (CPRA)",
                    "Non-discrimination",
                    "Privacy notice at or before collection"
                ],
                "response_timeline": RESPONSE_TIMELINES["CCPA"],
                "penalties": "Up to $7,500 per intentional violation"
            },
            "UK_GDPR": {
                "name": "UK General Data Protection Regulation",
                "jurisdiction": "United Kingdom",
                "key_obligations": [
                    "Similar to EU GDPR with UK-specific provisions",
                    "ICO oversight",
                    "UK International Data Transfer Addendum for cross-border transfers"
                ],
                "response_timeline": RESPONSE_TIMELINES["UK_GDPR"],
                "penalties": "Up to GBP 17.5M or 4% of annual global turnover"
            },
            "LGPD": {
                "name": "Lei Geral de Protecao de Dados",
                "jurisdiction": "Brazil",
                "key_obligations": [
                    "Similar framework to GDPR",
                    "DPO appointment required",
                    "ANPD enforcement"
                ],
                "response_timeline": RESPONSE_TIMELINES["LGPD"],
                "penalties": "Up to 2% of revenue in Brazil (capped at BRL 50M per violation)"
            }
        }

        regulationUpper = regulation.upper().replace(" ", "_")
        if regulationUpper not in overviews:
            raise ValueError(
                f"Unknown regulation: {regulation}. "
                f"Available: {', '.join(overviews.keys())}"
            )

        return overviews[regulationUpper]

    # --- Internal methods ---

    def _calculateDsrTimeline(self, regulation: str, dateReceived: Optional[str]) -> Dict[str, Any]:
        """Calculate DSR response timeline."""
        timeline = RESPONSE_TIMELINES.get(regulation, RESPONSE_TIMELINES["GDPR"])
        result = {
            "regulation": regulation,
            "timeline_rules": timeline
        }

        if dateReceived:
            result["date_received"] = dateReceived

            if "initial_acknowledgment_business_days" in timeline:
                ackDays = timeline["initial_acknowledgment_business_days"]
                result["acknowledgment_deadline"] = calculateBusinessDays(dateReceived, ackDays)

            substDays = timeline.get("substantive_response_days", 30)
            result["response_deadline"] = calculateDeadline(dateReceived, substDays)

            extDays = timeline.get("extension_days", 0)
            if extDays > 0:
                result["extended_deadline"] = calculateDeadline(dateReceived, substDays + extDays)
                result["extension_available"] = True
            else:
                result["extension_available"] = False

        return result

    def _checkDsrEscalationTriggers(self, dsrData: Dict) -> List[Dict[str, str]]:
        """Check for DSR-specific escalation triggers."""
        triggers = []

        if dsrData.get("involves_minor", False):
            triggers.append({
                "trigger": "Request involves a minor",
                "action": "Escalate to senior counsel for review"
            })

        if dsrData.get("subject_to_litigation_hold", False):
            triggers.append({
                "trigger": "Data subject to litigation hold",
                "action": "Coordinate with litigation counsel before proceeding"
            })

        if dsrData.get("active_litigation", False):
            triggers.append({
                "trigger": "Requester in active litigation with organization",
                "action": "Escalate to litigation counsel"
            })

        if dsrData.get("active_hr_matter", False):
            triggers.append({
                "trigger": "Employee with active HR matter",
                "action": "Coordinate with employment counsel"
            })

        if dsrData.get("special_category_data", False):
            triggers.append({
                "trigger": "Involves special category data (health, biometric, genetic)",
                "action": "Enhanced review required for sensitive data handling"
            })

        if dsrData.get("broad_scope", False):
            triggers.append({
                "trigger": "Request scope appears unusually broad",
                "action": "Assess whether clarification is needed from requester"
            })

        return triggers

    def _checkExemptions(self, dsrData: Dict) -> List[Dict[str, str]]:
        """Check applicable exemptions for a DSR."""
        exemptions = []
        requestType = dsrData.get("request_type", "")

        if dsrData.get("subject_to_litigation_hold", False) and requestType == "erasure":
            exemptions.append({
                "exemption": "Legal claims defense",
                "basis": "Data required for establishment, exercise, or defense of legal claims",
                "applies_to": "erasure"
            })

        if dsrData.get("regulatory_retention", False):
            exemptions.append({
                "exemption": "Legal obligation",
                "basis": "Retention required by applicable law or regulation",
                "applies_to": "erasure"
            })

        if dsrData.get("public_interest", False):
            exemptions.append({
                "exemption": "Public interest",
                "basis": "Processing necessary for public interest or official authority",
                "applies_to": "erasure, objection"
            })

        if dsrData.get("third_party_rights_affected", False):
            exemptions.append({
                "exemption": "Third-party rights",
                "basis": "Fulfilling request would adversely affect rights of others",
                "applies_to": "access, portability"
            })

        return exemptions

    def _generateProcessingSteps(self, requestType: str, dsrData: Dict) -> List[Dict[str, Any]]:
        """Generate processing steps for a DSR."""
        steps = [
            {
                "step": 1,
                "action": "Verify requester identity",
                "status": "completed" if dsrData.get("identity_verified") else "pending",
                "notes": "Use reasonable verification proportionate to data sensitivity"
            },
            {
                "step": 2,
                "action": "Log request in DSR register",
                "status": "pending",
                "notes": "Record date, type, requester, regulation, deadline, handler"
            },
            {
                "step": 3,
                "action": "Check for applicable exemptions",
                "status": "pending",
                "notes": "Review litigation holds, retention requirements, third-party rights"
            },
            {
                "step": 4,
                "action": f"Gather personal data across systems for {requestType} request",
                "status": "pending",
                "notes": "Search all systems where requester's data may be stored"
            },
            {
                "step": 5,
                "action": "Apply exemptions and document basis",
                "status": "pending",
                "notes": "Document specific legal basis for any partial or full denial"
            },
            {
                "step": 6,
                "action": "Prepare and send response",
                "status": "pending",
                "notes": "Include right to lodge complaint with supervisory authority"
            },
            {
                "step": 7,
                "action": "Document response and retain records",
                "status": "pending",
                "notes": "Retain records of request and response for compliance evidence"
            }
        ]

        return steps

    def _generateDpaSummary(
        self,
        status: str,
        nonCompliant: int,
        warnings: int,
        dpaData: Dict
    ) -> str:
        """Generate DPA review summary text."""
        counterparty = dpaData.get("counterparty", "Unknown")
        lines = [
            "DPA REVIEW SUMMARY",
            f"Counterparty: {counterparty}",
            f"Status: {status.upper().replace('_', ' ')}",
            ""
        ]

        if status == "compliant":
            lines.append("The DPA meets all reviewed compliance requirements.")
        elif status == "needs_attention":
            lines.append(f"The DPA has {warnings} item(s) requiring attention but no critical gaps.")
        else:
            lines.append(f"The DPA has {nonCompliant} non-compliant item(s) that must be addressed.")

        return "\n".join(lines)


def main():
    """Main entry point for the Compliance STF."""
    try:
        inputData = readInput()
        userInput = inputData.get("input", {})

        operation = userInput.get("operation")
        if not operation:
            raise ValueError("Missing required field: operation")

        apiClient = None
        try:
            apiClient = createApiClient(inputData)
        except Exception:
            logger.info("No API client available (non-DB operations only)")

        analyzer = ComplianceAnalyzer(apiClient)

        if operation == "review_dpa":
            validateRequiredFields(userInput, ["dpa_data"])
            result = analyzer.reviewDpa(dpaData=userInput["dpa_data"])

        elif operation == "process_dsr":
            validateRequiredFields(userInput, ["dsr_data"])
            result = analyzer.processDsr(dsrData=userInput["dsr_data"])

        elif operation == "get_response_timeline":
            validateRequiredFields(userInput, ["regulation", "date_received"])
            result = analyzer.getResponseTimeline(
                regulation=userInput["regulation"],
                dateReceived=userInput["date_received"]
            )

        elif operation == "check_exemptions":
            validateRequiredFields(userInput, ["dsr_data"])
            result = analyzer.checkExemptions(dsrData=userInput["dsr_data"])

        elif operation == "generate_dpa_checklist":
            result = analyzer.generateDpaChecklist(
                includeTransfers=userInput.get("include_transfers", True)
            )

        elif operation == "get_regulation_overview":
            validateRequiredFields(userInput, ["regulation"])
            result = analyzer.getRegulationOverview(
                regulation=userInput["regulation"]
            )

        else:
            raise ValueError(
                f"Unknown operation: {operation}. "
                f"Valid operations: review_dpa, process_dsr, "
                f"get_response_timeline, check_exemptions, "
                f"generate_dpa_checklist, get_regulation_overview"
            )

        writeOutput({
            "status": "success",
            "operation": operation,
            "data": result
        })

    except ValueError as e:
        logger.error(f"Validation error in ComplianceAnalyzer: {str(e)}")
        writeError(e, "ValidationError")
    except Exception as e:
        logger.error(f"Unexpected error in ComplianceAnalyzer: {str(e)}", exc_info=True)
        writeError(e)


if __name__ == "__main__":
    main()
