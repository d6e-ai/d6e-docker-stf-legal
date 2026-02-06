#!/usr/bin/env python3
"""
D6E Docker STF: Contract Review

Overview:
  Reviews contracts against negotiation playbook, flags deviations,
  classifies severity (GREEN/YELLOW/RED), and generates redline suggestions.

Main Operations:
  - review_contract: Full contract review against playbook
  - analyze_clause: Analyze a specific clause
  - generate_redline: Generate redline suggestion for a clause
  - classify_deviation: Classify deviation severity
  - generate_review_summary: Generate review summary with priorities

Limitations:
  - Provides legal workflow assistance, not legal advice
  - Rule-based analysis against standard commercial positions
  - All results should be reviewed by qualified legal professionals
"""

import sys
import os
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from utils import (
    logger, readInput, writeOutput, writeError,
    createApiClient, validateRequiredFields,
    generateId, getCurrentTimestamp, classifyContractDeviation
)


# Standard clause types and their review criteria
CLAUSE_TYPES = [
    "limitation_of_liability", "indemnification", "intellectual_property",
    "data_protection", "term_and_termination", "governing_law",
    "confidentiality", "warranties", "insurance"
]

# Default playbook positions (used when no custom playbook provided)
DEFAULT_PLAYBOOK = {
    "limitation_of_liability": {
        "standard_cap": "12 months of fees",
        "minimum_cap": "6 months of fees",
        "mutual_cap": True,
        "consequential_damages_exclusion": True,
        "standard_carveouts": ["gross_negligence", "willful_misconduct", "ip_infringement", "confidentiality_breach"]
    },
    "indemnification": {
        "mutual_indemnification": True,
        "standard_triggers": ["ip_infringement", "data_breach", "bodily_injury", "breach_of_reps"],
        "require_cap": True,
        "require_control_of_defense": True,
        "require_mitigation": True
    },
    "intellectual_property": {
        "retain_preexisting_ip": True,
        "work_for_hire_limited_to_deliverables": True,
        "no_unrestricted_feedback_clause": True,
        "license_scope_limited": True
    },
    "data_protection": {
        "require_dpa": True,
        "breach_notification_hours": 48,
        "subprocessor_notification": True,
        "data_deletion_on_termination": True,
        "audit_rights": True,
        "transfer_mechanism_required": True
    },
    "term_and_termination": {
        "max_initial_term_years": 3,
        "termination_for_convenience": True,
        "cure_period_days": 30,
        "auto_renewal_notice_days": 90,
        "transition_assistance": True
    },
    "governing_law": {
        "preferred_jurisdictions": ["Delaware", "New York", "California", "England and Wales"],
        "acceptable_jurisdictions": ["Texas", "Illinois", "Massachusetts", "Germany", "Singapore"],
        "prefer_litigation": True,
        "escalation_before_dispute": True
    }
}


class ContractReviewAnalyzer:
    """
    Analyzes contracts against negotiation playbook and generates recommendations.
    """

    def __init__(self, apiClient=None, playbook: Optional[Dict] = None):
        """
        Initialize contract review analyzer.

        Args:
            apiClient: Optional D6eApiClient for database operations
            playbook: Optional custom playbook (defaults to standard positions)
        """
        self.api = apiClient
        self.playbook = playbook or DEFAULT_PLAYBOOK

    def reviewContract(self, contractData: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform full contract review.

        Args:
            contractData: Contract details including:
                - contract_type: SaaS, professional_services, license, etc.
                - our_side: vendor, customer, licensor, licensee, partner
                - counterparty: Name of counterparty
                - clauses: Dict of clause type -> clause details

        Returns:
            Full review with deviations, redlines, and priority recommendations
        """
        logger.info(f"Reviewing contract with counterparty: {contractData.get('counterparty', 'unknown')}")

        contractType = contractData.get("contract_type", "general")
        ourSide = contractData.get("our_side", "customer")
        clauses = contractData.get("clauses", {})

        allDeviations = []
        allRedlines = []
        clauseAnalyses = []

        for clauseType, clauseDetails in clauses.items():
            if clauseType in CLAUSE_TYPES:
                analysis = self._analyzeClause(
                    clauseType, clauseDetails, ourSide, contractType
                )
                clauseAnalyses.append(analysis)

                for deviation in analysis.get("deviations", []):
                    allDeviations.append(deviation)

                for redline in analysis.get("redlines", []):
                    allRedlines.append(redline)

        # Classify all deviations
        redCount = len([d for d in allDeviations if d["severity"] == "RED"])
        yellowCount = len([d for d in allDeviations if d["severity"] == "YELLOW"])
        greenCount = len([d for d in allDeviations if d["severity"] == "GREEN"])

        # Overall risk classification
        if redCount > 0:
            overallRisk = "RED"
        elif yellowCount > 0:
            overallRisk = "YELLOW"
        else:
            overallRisk = "GREEN"

        # Prioritize redlines
        tier1 = [r for r in allRedlines if r.get("priority") == "must_have"]
        tier2 = [r for r in allRedlines if r.get("priority") == "should_have"]
        tier3 = [r for r in allRedlines if r.get("priority") == "nice_to_have"]

        return {
            "review_id": generateId(),
            "timestamp": getCurrentTimestamp(),
            "contract_type": contractType,
            "our_side": ourSide,
            "counterparty": contractData.get("counterparty", "Unknown"),
            "playbook_used": "custom" if contractData.get("playbook") else "default",
            "overall_risk": overallRisk,
            "deviation_summary": {
                "total": len(allDeviations),
                "red": redCount,
                "yellow": yellowCount,
                "green": greenCount
            },
            "clause_analyses": clauseAnalyses,
            "negotiation_priorities": {
                "tier_1_must_haves": tier1,
                "tier_2_should_haves": tier2,
                "tier_3_nice_to_haves": tier3
            },
            "summary": self._generateReviewSummary(
                overallRisk, allDeviations, contractData
            )
        }

    def analyzeClause(
        self,
        clauseType: str,
        clauseDetails: Dict[str, Any],
        ourSide: str = "customer",
        contractType: str = "general"
    ) -> Dict[str, Any]:
        """
        Analyze a specific contract clause.

        Args:
            clauseType: Type of clause to analyze
            clauseDetails: Details of the clause
            ourSide: Our position in the contract
            contractType: Type of contract

        Returns:
            Clause analysis with deviations and recommendations
        """
        logger.info(f"Analyzing clause: {clauseType}")

        if clauseType not in CLAUSE_TYPES:
            raise ValueError(
                f"Unknown clause type: {clauseType}. "
                f"Valid types: {', '.join(CLAUSE_TYPES)}"
            )

        return self._analyzeClause(clauseType, clauseDetails, ourSide, contractType)

    def generateRedline(
        self,
        clauseType: str,
        currentLanguage: str,
        issueDescription: str,
        priority: str = "should_have"
    ) -> Dict[str, Any]:
        """
        Generate redline suggestion for a specific issue.

        Args:
            clauseType: Type of clause
            currentLanguage: Current contract language
            issueDescription: Description of the issue
            priority: must_have, should_have, nice_to_have

        Returns:
            Redline suggestion with proposed language and rationale
        """
        logger.info(f"Generating redline for clause: {clauseType}")

        redlineTemplates = self._getRedlineTemplates(clauseType)
        proposedLanguage = redlineTemplates.get(
            issueDescription,
            f"[Proposed alternative language for: {issueDescription}]"
        )

        return {
            "clause_type": clauseType,
            "current_language": currentLanguage,
            "proposed_redline": proposedLanguage,
            "rationale": self._getRedlineRationale(clauseType, issueDescription),
            "priority": priority,
            "fallback": self._getFallbackPosition(clauseType, issueDescription)
        }

    def classifyDeviation(
        self,
        clauseType: str,
        deviationType: str,
        details: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Classify a specific deviation's severity.

        Args:
            clauseType: Clause type where deviation found
            deviationType: Type of deviation
            details: Additional details

        Returns:
            Classification with severity and recommendations
        """
        severity = classifyContractDeviation(deviationType)

        return {
            "clause_type": clauseType,
            "deviation_type": deviationType,
            "severity": severity,
            "severity_label": self._getSeverityLabel(severity),
            "action": self._getSeverityAction(severity),
            "details": details
        }

    def generateReviewSummary(
        self,
        deviations: List[Dict],
        contractData: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a structured review summary.

        Args:
            deviations: List of deviations found
            contractData: Contract metadata

        Returns:
            Structured review summary
        """
        redCount = len([d for d in deviations if d["severity"] == "RED"])
        overallRisk = "RED" if redCount > 0 else (
            "YELLOW" if any(d["severity"] == "YELLOW" for d in deviations) else "GREEN"
        )

        return {
            "overall_risk": overallRisk,
            "summary_text": self._generateReviewSummary(
                overallRisk, deviations, contractData
            ),
            "deviation_count": {
                "red": redCount,
                "yellow": len([d for d in deviations if d["severity"] == "YELLOW"]),
                "green": len([d for d in deviations if d["severity"] == "GREEN"])
            }
        }

    # --- Internal analysis methods ---

    def _analyzeClause(
        self,
        clauseType: str,
        clauseDetails: Dict[str, Any],
        ourSide: str,
        contractType: str
    ) -> Dict[str, Any]:
        """Analyze a clause against playbook position."""
        playbookPosition = self.playbook.get(clauseType, {})
        deviations = []
        redlines = []

        if clauseType == "limitation_of_liability":
            deviations, redlines = self._analyzeLiabilityClause(
                clauseDetails, playbookPosition, ourSide
            )
        elif clauseType == "indemnification":
            deviations, redlines = self._analyzeIndemnificationClause(
                clauseDetails, playbookPosition, ourSide
            )
        elif clauseType == "intellectual_property":
            deviations, redlines = self._analyzeIpClause(
                clauseDetails, playbookPosition, ourSide
            )
        elif clauseType == "data_protection":
            deviations, redlines = self._analyzeDataProtectionClause(
                clauseDetails, playbookPosition
            )
        elif clauseType == "term_and_termination":
            deviations, redlines = self._analyzeTermClause(
                clauseDetails, playbookPosition
            )
        elif clauseType == "governing_law":
            deviations, redlines = self._analyzeGoverningLawClause(
                clauseDetails, playbookPosition
            )
        else:
            deviations.append({
                "severity": "GREEN",
                "description": f"Clause type '{clauseType}' reviewed - no specific playbook criteria",
                "clause_type": clauseType
            })

        return {
            "clause_type": clauseType,
            "playbook_position": playbookPosition,
            "deviations": deviations,
            "redlines": redlines,
            "deviation_count": len(deviations),
            "highest_severity": max(
                [d["severity"] for d in deviations],
                key=lambda x: {"RED": 3, "YELLOW": 2, "GREEN": 1}.get(x, 0),
                default="GREEN"
            )
        }

    def _analyzeLiabilityClause(
        self, details: Dict, playbook: Dict, ourSide: str
    ) -> tuple:
        """Analyze limitation of liability clause."""
        deviations = []
        redlines = []

        capType = details.get("cap_type", "unknown")
        capAmount = details.get("cap_months_of_fees")
        isMutual = details.get("is_mutual", False)
        hasConsequentialExclusion = details.get("has_consequential_exclusion", False)
        carveouts = details.get("carveouts_from_cap", [])

        # Check cap
        if capType == "uncapped" or details.get("no_liability_clause", False):
            deviations.append({
                "severity": "RED",
                "description": "Uncapped liability or no limitation of liability clause",
                "clause_type": "limitation_of_liability",
                "deviation_type": "uncapped_liability"
            })
            redlines.append({
                "clause_type": "limitation_of_liability",
                "issue": "No liability cap",
                "proposed": f"Aggregate liability capped at {playbook.get('standard_cap', '12 months of fees')}",
                "rationale": "Uncapped liability creates unquantifiable risk exposure",
                "priority": "must_have",
                "fallback": f"Minimum cap at {playbook.get('minimum_cap', '6 months of fees')}"
            })
        elif capAmount is not None and capAmount < 6:
            deviations.append({
                "severity": "YELLOW",
                "description": f"Liability cap at {capAmount} months of fees (below standard {playbook.get('standard_cap')})",
                "clause_type": "limitation_of_liability",
                "deviation_type": "low_liability_cap"
            })
            redlines.append({
                "clause_type": "limitation_of_liability",
                "issue": "Low liability cap",
                "proposed": f"Increase cap to {playbook.get('standard_cap', '12 months of fees')}",
                "rationale": f"Current cap of {capAmount} months is below market standard",
                "priority": "should_have",
                "fallback": f"Accept {playbook.get('minimum_cap', '6 months of fees')} minimum"
            })
        else:
            deviations.append({
                "severity": "GREEN",
                "description": "Liability cap within acceptable range",
                "clause_type": "limitation_of_liability"
            })

        # Check mutual
        if playbook.get("mutual_cap") and not isMutual:
            deviations.append({
                "severity": "YELLOW",
                "description": "Liability cap is not mutual",
                "clause_type": "limitation_of_liability",
                "deviation_type": "asymmetric_cap"
            })

        # Check consequential damages exclusion
        if not hasConsequentialExclusion:
            deviations.append({
                "severity": "YELLOW",
                "description": "No exclusion of consequential damages",
                "clause_type": "limitation_of_liability",
                "deviation_type": "no_consequential_exclusion"
            })

        return deviations, redlines

    def _analyzeIndemnificationClause(
        self, details: Dict, playbook: Dict, ourSide: str
    ) -> tuple:
        """Analyze indemnification clause."""
        deviations = []
        redlines = []

        isMutual = details.get("is_mutual", False)
        isCapped = details.get("is_capped", True)
        hasControlOfDefense = details.get("has_control_of_defense", False)
        scope = details.get("scope", [])

        if not isMutual and playbook.get("mutual_indemnification"):
            if "ip_infringement" in scope:
                deviations.append({
                    "severity": "YELLOW",
                    "description": "Unilateral IP indemnification when mutual is preferred",
                    "clause_type": "indemnification",
                    "deviation_type": "unilateral_ip_indemnity"
                })

        if not isCapped and "any_breach" in scope:
            deviations.append({
                "severity": "RED",
                "description": "Uncapped indemnification for 'any breach' - effectively eliminates liability cap",
                "clause_type": "indemnification",
                "deviation_type": "uncapped_indemnity"
            })
            redlines.append({
                "clause_type": "indemnification",
                "issue": "Uncapped broad indemnification",
                "proposed": "Cap indemnification at the overall liability cap. Limit triggers to specific events.",
                "rationale": "Indemnification for 'any breach' with no cap eliminates the limitation of liability",
                "priority": "must_have",
                "fallback": "At minimum, cap indemnification and limit to specific triggers"
            })

        if not hasControlOfDefense and playbook.get("require_control_of_defense"):
            deviations.append({
                "severity": "YELLOW",
                "description": "No right to control defense of indemnified claims",
                "clause_type": "indemnification"
            })

        if not deviations:
            deviations.append({
                "severity": "GREEN",
                "description": "Indemnification provisions within acceptable range",
                "clause_type": "indemnification"
            })

        return deviations, redlines

    def _analyzeIpClause(
        self, details: Dict, playbook: Dict, ourSide: str
    ) -> tuple:
        """Analyze intellectual property clause."""
        deviations = []
        redlines = []

        retainsPreexistingIp = details.get("retains_preexisting_ip", True)
        workForHireLimited = details.get("work_for_hire_limited", True)
        hasBroadFeedback = details.get("has_broad_feedback_clause", False)
        hasBroadLicense = details.get("has_broad_license_scope", False)

        if not retainsPreexistingIp:
            deviations.append({
                "severity": "RED",
                "description": "IP assignment could capture pre-existing IP",
                "clause_type": "intellectual_property",
                "deviation_type": "ip_assignment_preexisting"
            })
            redlines.append({
                "clause_type": "intellectual_property",
                "issue": "Pre-existing IP at risk",
                "proposed": "Each party retains all rights in their pre-existing IP. Assignment limited to deliverables specifically created under this agreement.",
                "rationale": "Broad IP assignment could jeopardize core assets",
                "priority": "must_have",
                "fallback": "Explicit carveout for all pre-existing IP with license grant only"
            })

        if not workForHireLimited:
            deviations.append({
                "severity": "YELLOW",
                "description": "Work-for-hire provisions extend beyond deliverables",
                "clause_type": "intellectual_property"
            })

        if hasBroadFeedback:
            deviations.append({
                "severity": "YELLOW",
                "description": "Unrestricted feedback clause granting perpetual, irrevocable license",
                "clause_type": "intellectual_property"
            })

        if hasBroadLicense:
            deviations.append({
                "severity": "YELLOW",
                "description": "License scope broader than needed for the business relationship",
                "clause_type": "intellectual_property"
            })

        if not deviations:
            deviations.append({
                "severity": "GREEN",
                "description": "IP provisions acceptable",
                "clause_type": "intellectual_property"
            })

        return deviations, redlines

    def _analyzeDataProtectionClause(
        self, details: Dict, playbook: Dict
    ) -> tuple:
        """Analyze data protection clause."""
        deviations = []
        redlines = []

        processesPersonalData = details.get("processes_personal_data", False)
        hasDpa = details.get("has_dpa", False)
        breachNotificationHours = details.get("breach_notification_hours")
        hasSubprocessorNotification = details.get("has_subprocessor_notification", False)
        hasDeletionProvision = details.get("has_deletion_provision", False)
        hasAuditRights = details.get("has_audit_rights", False)
        hasTransferMechanism = details.get("has_transfer_mechanism", False)

        if processesPersonalData and not hasDpa:
            deviations.append({
                "severity": "RED",
                "description": "Personal data processed but no DPA in place",
                "clause_type": "data_protection",
                "deviation_type": "no_dpa_with_personal_data"
            })
            redlines.append({
                "clause_type": "data_protection",
                "issue": "Missing DPA",
                "proposed": "Execute Data Processing Agreement/Addendum before processing begins",
                "rationale": "GDPR Article 28 requires a written DPA when engaging a data processor",
                "priority": "must_have",
                "fallback": "No fallback - DPA is legally required"
            })

        if breachNotificationHours and breachNotificationHours > 72:
            deviations.append({
                "severity": "YELLOW",
                "description": f"Breach notification timeline ({breachNotificationHours}h) may prevent timely regulatory notification",
                "clause_type": "data_protection"
            })

        if processesPersonalData and not hasSubprocessorNotification:
            deviations.append({
                "severity": "YELLOW",
                "description": "Blanket sub-processor authorization without notification",
                "clause_type": "data_protection"
            })

        if processesPersonalData and not hasDeletionProvision:
            deviations.append({
                "severity": "YELLOW",
                "description": "No data deletion provision on termination",
                "clause_type": "data_protection"
            })

        if not deviations:
            deviations.append({
                "severity": "GREEN",
                "description": "Data protection provisions acceptable",
                "clause_type": "data_protection"
            })

        return deviations, redlines

    def _analyzeTermClause(self, details: Dict, playbook: Dict) -> tuple:
        """Analyze term and termination clause."""
        deviations = []
        redlines = []

        initialTermYears = details.get("initial_term_years")
        hasTermForConvenience = details.get("has_termination_for_convenience", False)
        curePeriodDays = details.get("cure_period_days")
        autoRenewalNoticeDays = details.get("auto_renewal_notice_days")
        hasTransitionAssistance = details.get("has_transition_assistance", False)

        maxTerm = playbook.get("max_initial_term_years", 3)
        if initialTermYears and initialTermYears > maxTerm:
            if not hasTermForConvenience:
                deviations.append({
                    "severity": "YELLOW",
                    "description": f"Long initial term ({initialTermYears} years) with no termination for convenience",
                    "clause_type": "term_and_termination"
                })

        if autoRenewalNoticeDays and autoRenewalNoticeDays < playbook.get("auto_renewal_notice_days", 90):
            deviations.append({
                "severity": "YELLOW",
                "description": f"Auto-renewal notice window ({autoRenewalNoticeDays} days) shorter than standard ({playbook.get('auto_renewal_notice_days', 90)} days)",
                "clause_type": "term_and_termination",
                "deviation_type": "short_auto_renewal_notice"
            })

        if curePeriodDays is not None and curePeriodDays == 0:
            deviations.append({
                "severity": "YELLOW",
                "description": "No cure period for termination for cause",
                "clause_type": "term_and_termination"
            })

        if not deviations:
            deviations.append({
                "severity": "GREEN",
                "description": "Term and termination provisions acceptable",
                "clause_type": "term_and_termination"
            })

        return deviations, redlines

    def _analyzeGoverningLawClause(self, details: Dict, playbook: Dict) -> tuple:
        """Analyze governing law and dispute resolution."""
        deviations = []
        redlines = []

        jurisdiction = details.get("jurisdiction", "")
        preferred = playbook.get("preferred_jurisdictions", [])
        acceptable = playbook.get("acceptable_jurisdictions", [])
        hasMandatoryArbitration = details.get("has_mandatory_arbitration", False)
        hasEscalation = details.get("has_escalation_process", False)

        if jurisdiction in preferred:
            deviations.append({
                "severity": "GREEN",
                "description": f"Preferred jurisdiction: {jurisdiction}",
                "clause_type": "governing_law"
            })
        elif jurisdiction in acceptable:
            deviations.append({
                "severity": "YELLOW",
                "description": f"Acceptable but non-preferred jurisdiction: {jurisdiction}",
                "clause_type": "governing_law",
                "deviation_type": "non_preferred_jurisdiction"
            })
        elif jurisdiction:
            if hasMandatoryArbitration:
                deviations.append({
                    "severity": "RED",
                    "description": f"Problematic jurisdiction ({jurisdiction}) with mandatory arbitration",
                    "clause_type": "governing_law",
                    "deviation_type": "problematic_jurisdiction"
                })
            else:
                deviations.append({
                    "severity": "YELLOW",
                    "description": f"Non-standard jurisdiction: {jurisdiction}",
                    "clause_type": "governing_law"
                })

        if not deviations:
            deviations.append({
                "severity": "GREEN",
                "description": "Governing law provisions acceptable",
                "clause_type": "governing_law"
            })

        return deviations, redlines

    # --- Helper methods ---

    def _getSeverityLabel(self, severity: str) -> str:
        """Get human-readable severity label."""
        labels = {
            "GREEN": "Acceptable - No negotiation needed",
            "YELLOW": "Negotiate - Falls outside standard but within range",
            "RED": "Escalate - Material risk requiring senior review"
        }
        return labels.get(severity, "Unknown")

    def _getSeverityAction(self, severity: str) -> str:
        """Get recommended action for severity level."""
        actions = {
            "GREEN": "Note for awareness. No negotiation needed.",
            "YELLOW": "Generate redline language. Provide fallback position. Estimate business impact.",
            "RED": "Explain specific risk. Provide market-standard alternative. Recommend escalation path."
        }
        return actions.get(severity, "Review required.")

    def _getRedlineTemplates(self, clauseType: str) -> Dict[str, str]:
        """Get redline templates for common issues by clause type."""
        templates = {
            "limitation_of_liability": {
                "uncapped_liability": "The aggregate liability of each party under this Agreement shall not exceed the total fees paid or payable in the twelve (12) month period immediately preceding the claim.",
                "no_consequential_exclusion": "IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES."
            },
            "indemnification": {
                "uncapped_indemnity": "All indemnification obligations under this Section shall be subject to the overall limitation of liability set forth in Section [X]."
            },
            "data_protection": {
                "no_dpa_with_personal_data": "The parties shall execute a Data Processing Agreement substantially in the form attached hereto as Exhibit [X] prior to any processing of personal data."
            }
        }
        return templates.get(clauseType, {})

    def _getRedlineRationale(self, clauseType: str, issue: str) -> str:
        """Get rationale for a redline suggestion."""
        return f"Standard commercial practice requires appropriate protections for {clauseType.replace('_', ' ')}. The current provision ({issue}) falls outside market standard."

    def _getFallbackPosition(self, clauseType: str, issue: str) -> str:
        """Get fallback position for negotiation."""
        return f"If primary position is rejected, negotiate to minimum acceptable terms for {clauseType.replace('_', ' ')}."

    def _generateReviewSummary(
        self,
        overallRisk: str,
        deviations: List,
        contractData: Dict
    ) -> str:
        """Generate text summary of the review."""
        counterparty = contractData.get("counterparty", "Unknown")
        contractType = contractData.get("contract_type", "unknown")

        redItems = [d for d in deviations if d.get("severity") == "RED"]
        yellowItems = [d for d in deviations if d.get("severity") == "YELLOW"]

        lines = [
            "CONTRACT REVIEW SUMMARY",
            f"Counterparty: {counterparty}",
            f"Contract Type: {contractType}",
            f"Overall Risk: {overallRisk}",
            f"Total Deviations: {len(deviations)} (RED: {len(redItems)}, YELLOW: {len(yellowItems)})",
            ""
        ]

        if redItems:
            lines.append("TIER 1 - MUST-HAVES (Deal Breakers):")
            for item in redItems:
                lines.append(f"  - {item.get('description', 'N/A')}")
            lines.append("")

        if yellowItems:
            lines.append("TIER 2 - SHOULD-HAVES (Negotiation Items):")
            for item in yellowItems:
                lines.append(f"  - {item.get('description', 'N/A')}")

        return "\n".join(lines)


def main():
    """Main entry point for the Contract Review STF."""
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

        playbook = userInput.get("playbook")
        analyzer = ContractReviewAnalyzer(apiClient, playbook)

        if operation == "review_contract":
            validateRequiredFields(userInput, ["contract_data"])
            result = analyzer.reviewContract(contractData=userInput["contract_data"])

        elif operation == "analyze_clause":
            validateRequiredFields(userInput, ["clause_type", "clause_details"])
            result = analyzer.analyzeClause(
                clauseType=userInput["clause_type"],
                clauseDetails=userInput["clause_details"],
                ourSide=userInput.get("our_side", "customer"),
                contractType=userInput.get("contract_type", "general")
            )

        elif operation == "generate_redline":
            validateRequiredFields(userInput, ["clause_type", "current_language", "issue_description"])
            result = analyzer.generateRedline(
                clauseType=userInput["clause_type"],
                currentLanguage=userInput["current_language"],
                issueDescription=userInput["issue_description"],
                priority=userInput.get("priority", "should_have")
            )

        elif operation == "classify_deviation":
            validateRequiredFields(userInput, ["clause_type", "deviation_type"])
            result = analyzer.classifyDeviation(
                clauseType=userInput["clause_type"],
                deviationType=userInput["deviation_type"],
                details=userInput.get("details")
            )

        elif operation == "generate_review_summary":
            validateRequiredFields(userInput, ["deviations", "contract_data"])
            result = analyzer.generateReviewSummary(
                deviations=userInput["deviations"],
                contractData=userInput["contract_data"]
            )

        else:
            raise ValueError(
                f"Unknown operation: {operation}. "
                f"Valid operations: review_contract, analyze_clause, "
                f"generate_redline, classify_deviation, generate_review_summary"
            )

        writeOutput({
            "status": "success",
            "operation": operation,
            "data": result
        })

    except ValueError as e:
        logger.error(f"Validation error in ContractReviewAnalyzer: {str(e)}")
        writeError(e, "ValidationError")
    except Exception as e:
        logger.error(f"Unexpected error in ContractReviewAnalyzer: {str(e)}", exc_info=True)
        writeError(e)


if __name__ == "__main__":
    main()
