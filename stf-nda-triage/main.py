#!/usr/bin/env python3
"""
D6E Docker STF: NDA Triage

Overview:
  Screens incoming NDAs and classifies them as GREEN (standard),
  YELLOW (needs review), or RED (significant issues).
  Provides routing recommendations and detailed issue analysis.

Main Operations:
  - triage_nda: Evaluate NDA clauses and classify risk level
  - check_clause: Check a specific clause against standard criteria
  - get_routing_recommendation: Get routing based on classification
  - generate_checklist: Generate NDA screening checklist

Limitations:
  - Provides legal workflow assistance, not legal advice
  - Analysis based on rule-based pattern matching against standard criteria
  - All results should be reviewed by qualified legal professionals
"""

import sys
import os
import re
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from utils import (
    logger, readInput, writeOutput, writeError,
    createApiClient, validateRequiredFields,
    generateId, getCurrentTimestamp, classifyNdaColor
)


# Standard NDA criteria definitions
STANDARD_CARVEOUTS = [
    "public_knowledge",
    "prior_possession",
    "independent_development",
    "third_party_receipt",
    "legal_compulsion"
]

PROBLEMATIC_PROVISIONS = [
    "non_solicitation",
    "non_compete",
    "exclusivity",
    "standstill",
    "broad_residuals",
    "ip_assignment",
    "audit_rights",
    "liquidated_damages"
]

STANDARD_TERM_RANGE = {"min_years": 1, "max_years": 3}
STANDARD_SURVIVAL_RANGE = {"min_years": 2, "max_years": 5}


class NdaTriageAnalyzer:
    """
    Analyzes NDAs against standard screening criteria and classifies risk level.
    """

    def __init__(self, apiClient=None):
        """
        Initialize NDA triage analyzer.

        Args:
            apiClient: Optional D6eApiClient for database operations
        """
        self.api = apiClient

    def triageNda(self, ndaData: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform full NDA triage evaluation.

        Args:
            ndaData: NDA details including clauses and terms. Expected fields:
                - nda_type: "mutual", "unilateral_disclosing", "unilateral_receiving"
                - counterparty: Name of the counterparty
                - purpose: Purpose of the NDA
                - confidential_info_definition: Description of CI definition scope
                - carveouts_present: List of standard carveouts present
                - term_years: Agreement term in years
                - survival_years: Survival period in years
                - governing_law: Governing law jurisdiction
                - has_marking_requirement: Boolean
                - permitted_disclosures: List of permitted disclosure categories
                - return_destruction: Dict with obligation details
                - problematic_provisions: List of problematic provisions found
                - additional_clauses: Optional additional clause details

        Returns:
            Triage result with classification, issues, and recommendations
        """
        logger.info(f"Triaging NDA with counterparty: {ndaData.get('counterparty', 'unknown')}")

        redIssues = []
        yellowIssues = []
        greenNotes = []
        checklistResults = []

        # 1. Agreement Structure
        structureResult = self._checkAgreementStructure(ndaData)
        checklistResults.append(structureResult)
        self._categorizeIssues(structureResult, redIssues, yellowIssues, greenNotes)

        # 2. Confidential Information Definition
        ciResult = self._checkConfidentialInfoDefinition(ndaData)
        checklistResults.append(ciResult)
        self._categorizeIssues(ciResult, redIssues, yellowIssues, greenNotes)

        # 3. Standard Carveouts
        carveoutResult = self._checkCarveouts(ndaData)
        checklistResults.append(carveoutResult)
        self._categorizeIssues(carveoutResult, redIssues, yellowIssues, greenNotes)

        # 4. Permitted Disclosures
        disclosureResult = self._checkPermittedDisclosures(ndaData)
        checklistResults.append(disclosureResult)
        self._categorizeIssues(disclosureResult, redIssues, yellowIssues, greenNotes)

        # 5. Term and Duration
        termResult = self._checkTermAndDuration(ndaData)
        checklistResults.append(termResult)
        self._categorizeIssues(termResult, redIssues, yellowIssues, greenNotes)

        # 6. Return and Destruction
        returnResult = self._checkReturnDestruction(ndaData)
        checklistResults.append(returnResult)
        self._categorizeIssues(returnResult, redIssues, yellowIssues, greenNotes)

        # 7. Problematic Provisions
        provisionsResult = self._checkProblematicProvisions(ndaData)
        checklistResults.append(provisionsResult)
        self._categorizeIssues(provisionsResult, redIssues, yellowIssues, greenNotes)

        # 8. Governing Law
        govLawResult = self._checkGoverningLaw(ndaData)
        checklistResults.append(govLawResult)
        self._categorizeIssues(govLawResult, redIssues, yellowIssues, greenNotes)

        # 9. Remedies
        remediesResult = self._checkRemedies(ndaData)
        checklistResults.append(remediesResult)
        self._categorizeIssues(remediesResult, redIssues, yellowIssues, greenNotes)

        # Classify overall
        issues = {"red": redIssues, "yellow": yellowIssues, "green": greenNotes}
        classification = classifyNdaColor(issues)

        # Get routing recommendation
        routing = self._getRoutingRecommendation(classification)

        return {
            "triage_id": generateId(),
            "timestamp": getCurrentTimestamp(),
            "counterparty": ndaData.get("counterparty", "Unknown"),
            "nda_type": ndaData.get("nda_type", "unknown"),
            "classification": classification,
            "classification_label": self._getClassificationLabel(classification),
            "issues": issues,
            "issue_counts": {
                "red": len(redIssues),
                "yellow": len(yellowIssues),
                "green": len(greenNotes)
            },
            "checklist_results": checklistResults,
            "routing": routing,
            "summary": self._generateSummary(
                classification, ndaData, redIssues, yellowIssues
            )
        }

    def checkClause(
        self,
        clauseType: str,
        clauseData: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check a specific NDA clause against standard criteria.

        Args:
            clauseType: Type of clause to check (e.g., "term", "carveouts",
                        "governing_law", "confidential_info", "remedies")
            clauseData: Clause-specific data

        Returns:
            Clause check result with findings and classification
        """
        logger.info(f"Checking clause type: {clauseType}")

        checkMethods = {
            "agreement_structure": self._checkAgreementStructure,
            "confidential_info": self._checkConfidentialInfoDefinition,
            "carveouts": self._checkCarveouts,
            "permitted_disclosures": self._checkPermittedDisclosures,
            "term": self._checkTermAndDuration,
            "return_destruction": self._checkReturnDestruction,
            "problematic_provisions": self._checkProblematicProvisions,
            "governing_law": self._checkGoverningLaw,
            "remedies": self._checkRemedies
        }

        if clauseType not in checkMethods:
            raise ValueError(
                f"Unknown clause type: {clauseType}. "
                f"Valid types: {', '.join(checkMethods.keys())}"
            )

        return checkMethods[clauseType](clauseData)

    def getRoutingRecommendation(
        self,
        classification: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get routing recommendation based on classification.

        Args:
            classification: GREEN, YELLOW, or RED
            context: Optional additional context

        Returns:
            Routing recommendation with actions and timeline
        """
        logger.info(f"Getting routing for classification: {classification}")
        return self._getRoutingRecommendation(classification, context)

    def generateChecklist(
        self,
        ndaType: str = "mutual"
    ) -> Dict[str, Any]:
        """
        Generate a blank NDA screening checklist.

        Args:
            ndaType: Type of NDA (mutual, unilateral_disclosing, unilateral_receiving)

        Returns:
            Structured checklist for NDA screening
        """
        logger.info(f"Generating checklist for NDA type: {ndaType}")

        checklist = {
            "nda_type": ndaType,
            "generated_at": getCurrentTimestamp(),
            "sections": [
                {
                    "name": "Agreement Structure",
                    "items": [
                        {"check": "Type identified (mutual/unilateral)", "status": "pending"},
                        {"check": "Appropriate for business context", "status": "pending"},
                        {"check": "Standalone agreement (not embedded)", "status": "pending"}
                    ]
                },
                {
                    "name": "Confidential Information Definition",
                    "items": [
                        {"check": "Reasonable scope (not overbroad)", "status": "pending"},
                        {"check": "Marking requirements workable", "status": "pending"},
                        {"check": "Standard exclusions present", "status": "pending"},
                        {"check": "No problematic inclusions", "status": "pending"}
                    ]
                },
                {
                    "name": "Standard Carveouts",
                    "items": [
                        {"check": "Public knowledge carveout", "status": "pending"},
                        {"check": "Prior possession carveout", "status": "pending"},
                        {"check": "Independent development carveout", "status": "pending"},
                        {"check": "Third-party receipt carveout", "status": "pending"},
                        {"check": "Legal compulsion carveout", "status": "pending"}
                    ]
                },
                {
                    "name": "Permitted Disclosures",
                    "items": [
                        {"check": "Employees with need to know", "status": "pending"},
                        {"check": "Contractors/advisors under NDA", "status": "pending"},
                        {"check": "Affiliates (if needed)", "status": "pending"},
                        {"check": "Legal/regulatory disclosures", "status": "pending"}
                    ]
                },
                {
                    "name": "Term and Duration",
                    "items": [
                        {"check": f"Agreement term (standard: {STANDARD_TERM_RANGE['min_years']}-{STANDARD_TERM_RANGE['max_years']} years)", "status": "pending"},
                        {"check": f"Survival period (standard: {STANDARD_SURVIVAL_RANGE['min_years']}-{STANDARD_SURVIVAL_RANGE['max_years']} years)", "status": "pending"},
                        {"check": "Not perpetual (unless trade secret)", "status": "pending"}
                    ]
                },
                {
                    "name": "Return and Destruction",
                    "items": [
                        {"check": "Triggered on termination/request", "status": "pending"},
                        {"check": "Return or destroy all copies", "status": "pending"},
                        {"check": "Retention exception for legal/compliance", "status": "pending"},
                        {"check": "Certification reasonable (not sworn affidavit)", "status": "pending"}
                    ]
                },
                {
                    "name": "Problematic Provisions (should NOT be present)",
                    "items": [
                        {"check": "No non-solicitation", "status": "pending"},
                        {"check": "No non-compete", "status": "pending"},
                        {"check": "No exclusivity", "status": "pending"},
                        {"check": "No standstill", "status": "pending"},
                        {"check": "No broad residuals clause", "status": "pending"},
                        {"check": "No IP assignment/license", "status": "pending"},
                        {"check": "No audit rights", "status": "pending"},
                        {"check": "No liquidated damages", "status": "pending"}
                    ]
                },
                {
                    "name": "Governing Law and Jurisdiction",
                    "items": [
                        {"check": "Reasonable jurisdiction", "status": "pending"},
                        {"check": "Governing law and venue consistent", "status": "pending"},
                        {"check": "No mandatory arbitration", "status": "pending"}
                    ]
                },
                {
                    "name": "Remedies",
                    "items": [
                        {"check": "Injunctive relief acknowledgment (standard)", "status": "pending"},
                        {"check": "No pre-determined damages", "status": "pending"},
                        {"check": "Remedies apply equally (mutual NDA)", "status": "pending"}
                    ]
                }
            ]
        }

        return checklist

    def describe(self) -> Dict[str, Any]:
        """
        Return the input schema and available operations for this STF.

        Returns:
            Schema definition with operations, required/optional fields, and property types
        """
        return {
            "input_schema": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "triage_nda", "check_clause",
                            "get_routing_recommendation", "generate_checklist",
                            "describe"
                        ],
                        "description": "The operation to perform"
                    },
                    "nda_data": {
                        "type": "object",
                        "description": "NDA details for triage evaluation",
                        "properties": {
                            "nda_type": {"type": "string", "enum": ["mutual", "unilateral_disclosing", "unilateral_receiving"]},
                            "counterparty": {"type": "string"},
                            "purpose": {"type": "string"},
                            "confidential_info_definition": {"type": "string"},
                            "confidential_info_scope": {"type": "string", "enum": ["reasonable", "broad", "overbroad"]},
                            "carveouts_present": {"type": "array", "items": {"type": "string"}},
                            "term_years": {"type": "number"},
                            "survival_years": {"type": "number"},
                            "is_perpetual": {"type": "boolean"},
                            "governing_law": {"type": "string"},
                            "has_marking_requirement": {"type": "boolean"},
                            "marking_workable": {"type": "boolean"},
                            "permitted_disclosures": {"type": "array", "items": {"type": "string"}},
                            "return_destruction": {
                                "type": "object",
                                "properties": {
                                    "has_obligation": {"type": "boolean"},
                                    "has_retention_exception": {"type": "boolean"},
                                    "requires_sworn_affidavit": {"type": "boolean"}
                                }
                            },
                            "problematic_provisions": {"type": "array", "items": {"type": "string"}},
                            "has_mandatory_arbitration": {"type": "boolean"},
                            "jurisdiction_acceptable": {"type": "boolean"},
                            "has_injunctive_relief": {"type": "boolean"},
                            "has_liquidated_damages": {"type": "boolean"},
                            "is_mutual_remedies": {"type": "boolean"},
                            "is_standalone": {"type": "boolean"},
                            "expected_type": {"type": "string"},
                            "trade_secret_justification": {"type": "boolean"}
                        }
                    },
                    "clause_type": {
                        "type": "string",
                        "enum": [
                            "agreement_structure", "confidential_info", "carveouts",
                            "permitted_disclosures", "term", "return_destruction",
                            "problematic_provisions", "governing_law", "remedies"
                        ],
                        "description": "Type of clause to check"
                    },
                    "clause_data": {
                        "type": "object",
                        "description": "Clause-specific data for check_clause operation"
                    },
                    "classification": {
                        "type": "string",
                        "enum": ["GREEN", "YELLOW", "RED"],
                        "description": "NDA classification for routing recommendation"
                    },
                    "context": {
                        "type": "object",
                        "description": "Optional additional context for routing"
                    },
                    "nda_type": {
                        "type": "string",
                        "enum": ["mutual", "unilateral_disclosing", "unilateral_receiving"],
                        "description": "NDA type for checklist generation"
                    }
                },
                "required": ["operation"]
            },
            "operations": {
                "triage_nda": {
                    "description": "Perform full NDA triage evaluation with GREEN/YELLOW/RED classification",
                    "required": ["nda_data"],
                    "optional": []
                },
                "check_clause": {
                    "description": "Check a specific NDA clause against standard criteria",
                    "required": ["clause_type", "clause_data"],
                    "optional": []
                },
                "get_routing_recommendation": {
                    "description": "Get routing recommendation based on NDA classification",
                    "required": ["classification"],
                    "optional": ["context"]
                },
                "generate_checklist": {
                    "description": "Generate a blank NDA screening checklist",
                    "required": [],
                    "optional": ["nda_type"]
                },
                "describe": {
                    "description": "Return the input schema and available operations",
                    "required": [],
                    "optional": []
                }
            }
        }

    # --- Internal check methods ---

    def _checkAgreementStructure(self, ndaData: Dict[str, Any]) -> Dict[str, Any]:
        """Check agreement structure against standards."""
        findings = []
        ndaType = ndaData.get("nda_type", "unknown")
        expectedType = ndaData.get("expected_type", "mutual")

        if ndaType == "unknown":
            findings.append({
                "severity": "yellow",
                "finding": "NDA type not identified",
                "recommendation": "Determine if mutual or unilateral NDA is appropriate"
            })
        elif ndaType != expectedType and expectedType:
            if expectedType == "mutual" and ndaType.startswith("unilateral"):
                findings.append({
                    "severity": "red",
                    "finding": f"Unilateral NDA provided when mutual is required (type: {ndaType})",
                    "recommendation": "Request mutual NDA or send organization's standard form"
                })
            else:
                findings.append({
                    "severity": "green",
                    "finding": f"NDA type ({ndaType}) matches expected type"
                })

        isStandalone = ndaData.get("is_standalone", True)
        if not isStandalone:
            findings.append({
                "severity": "red",
                "finding": "Confidentiality provisions embedded in larger commercial agreement",
                "recommendation": "This is not a standalone NDA. Full commercial review required."
            })

        if not findings:
            findings.append({
                "severity": "green",
                "finding": f"Agreement structure acceptable ({ndaType})"
            })

        return {
            "section": "Agreement Structure",
            "findings": findings
        }

    def _checkConfidentialInfoDefinition(self, ndaData: Dict[str, Any]) -> Dict[str, Any]:
        """Check confidential information definition."""
        findings = []
        ciScope = ndaData.get("confidential_info_scope", "reasonable")
        hasMarking = ndaData.get("has_marking_requirement", False)

        if ciScope == "overbroad":
            findings.append({
                "severity": "red",
                "finding": "Overbroad definition of confidential information that could capture public or independently developed information",
                "recommendation": "Narrow definition to information marked or identified as confidential"
            })
        elif ciScope == "broad":
            findings.append({
                "severity": "yellow",
                "finding": "Broader than preferred definition but not unreasonable",
                "recommendation": "Consider narrowing to marked/identified information"
            })
        else:
            findings.append({
                "severity": "green",
                "finding": "Confidential information definition is reasonably scoped"
            })

        if hasMarking:
            markingWorkable = ndaData.get("marking_workable", True)
            if markingWorkable:
                findings.append({
                    "severity": "yellow",
                    "finding": "Marking requirement present but workable",
                    "recommendation": "Verify 30-day window for marking oral disclosures"
                })
            else:
                findings.append({
                    "severity": "yellow",
                    "finding": "Marking requirement may be impractical",
                    "recommendation": "Negotiate workable marking timeframe"
                })

        return {
            "section": "Confidential Information Definition",
            "findings": findings
        }

    def _checkCarveouts(self, ndaData: Dict[str, Any]) -> Dict[str, Any]:
        """Check standard carveouts are present."""
        findings = []
        carveoutsPresent = ndaData.get("carveouts_present", [])

        missingCritical = []
        missingOther = []

        for carveout in STANDARD_CARVEOUTS:
            if carveout not in carveoutsPresent:
                if carveout in ["independent_development", "legal_compulsion"]:
                    missingCritical.append(carveout)
                else:
                    missingOther.append(carveout)

        if missingCritical:
            findings.append({
                "severity": "red",
                "finding": f"Missing critical carveouts: {', '.join(missingCritical)}",
                "recommendation": "These carveouts are essential. Add standard language."
            })

        if missingOther:
            findings.append({
                "severity": "yellow",
                "finding": f"Missing standard carveouts: {', '.join(missingOther)}",
                "recommendation": "Add missing standard carveouts"
            })

        presentCount = len(carveoutsPresent)
        totalCount = len(STANDARD_CARVEOUTS)

        if presentCount == totalCount:
            findings.append({
                "severity": "green",
                "finding": f"All {totalCount} standard carveouts present"
            })

        return {
            "section": "Standard Carveouts",
            "findings": findings,
            "carveouts_present": carveoutsPresent,
            "carveouts_missing": missingCritical + missingOther,
            "completeness": f"{presentCount}/{totalCount}"
        }

    def _checkPermittedDisclosures(self, ndaData: Dict[str, Any]) -> Dict[str, Any]:
        """Check permitted disclosure provisions."""
        findings = []
        permitted = ndaData.get("permitted_disclosures", [])

        standardPermitted = ["employees", "contractors_advisors", "legal_regulatory"]
        missing = [p for p in standardPermitted if p not in permitted]

        if missing:
            findings.append({
                "severity": "yellow",
                "finding": f"Missing permitted disclosure categories: {', '.join(missing)}",
                "recommendation": "Add standard permitted disclosure provisions"
            })
        else:
            findings.append({
                "severity": "green",
                "finding": "Standard permitted disclosure provisions present"
            })

        return {
            "section": "Permitted Disclosures",
            "findings": findings
        }

    def _checkTermAndDuration(self, ndaData: Dict[str, Any]) -> Dict[str, Any]:
        """Check term and survival duration."""
        findings = []
        termYears = ndaData.get("term_years")
        survivalYears = ndaData.get("survival_years")
        isPerpetual = ndaData.get("is_perpetual", False)

        if isPerpetual:
            hasTradeSecretJustification = ndaData.get("trade_secret_justification", False)
            if hasTradeSecretJustification:
                findings.append({
                    "severity": "yellow",
                    "finding": "Perpetual obligation with trade secret justification",
                    "recommendation": "Consider replacing with defined term plus trade secret carveout"
                })
            else:
                findings.append({
                    "severity": "red",
                    "finding": "Perpetual confidentiality obligation without trade secret justification",
                    "recommendation": "Replace with defined term (2-5 years). Offer trade secret carveout."
                })
        elif termYears is not None:
            if termYears > 10:
                findings.append({
                    "severity": "red",
                    "finding": f"Unreasonable term: {termYears} years (standard: {STANDARD_TERM_RANGE['min_years']}-{STANDARD_TERM_RANGE['max_years']} years)",
                    "recommendation": "Reduce to standard range"
                })
            elif termYears > STANDARD_TERM_RANGE["max_years"]:
                findings.append({
                    "severity": "yellow",
                    "finding": f"Term of {termYears} years exceeds standard range but within market range",
                    "recommendation": f"Consider negotiating down to {STANDARD_TERM_RANGE['max_years']} years"
                })
            else:
                findings.append({
                    "severity": "green",
                    "finding": f"Term of {termYears} years within standard range"
                })

        if survivalYears is not None:
            if survivalYears > 7:
                findings.append({
                    "severity": "yellow",
                    "finding": f"Survival period of {survivalYears} years exceeds market range",
                    "recommendation": f"Negotiate down to {STANDARD_SURVIVAL_RANGE['max_years']} years"
                })
            elif survivalYears >= STANDARD_SURVIVAL_RANGE["min_years"] and survivalYears <= STANDARD_SURVIVAL_RANGE["max_years"]:
                findings.append({
                    "severity": "green",
                    "finding": f"Survival period of {survivalYears} years within standard range"
                })

        return {
            "section": "Term and Duration",
            "findings": findings
        }

    def _checkReturnDestruction(self, ndaData: Dict[str, Any]) -> Dict[str, Any]:
        """Check return and destruction provisions."""
        findings = []
        returnDestruction = ndaData.get("return_destruction", {})

        hasObligation = returnDestruction.get("has_obligation", False)
        hasRetentionException = returnDestruction.get("has_retention_exception", False)
        requiresAffidavit = returnDestruction.get("requires_sworn_affidavit", False)

        if not hasObligation:
            findings.append({
                "severity": "yellow",
                "finding": "No explicit return/destruction obligation",
                "recommendation": "Add standard return or destroy provision"
            })

        if hasObligation and not hasRetentionException:
            findings.append({
                "severity": "yellow",
                "finding": "Return/destruction provision lacks retention exception for legal/compliance",
                "recommendation": "Add exception for copies required by law, regulation, or backup policies"
            })

        if requiresAffidavit:
            findings.append({
                "severity": "yellow",
                "finding": "Requires sworn affidavit for destruction certification (onerous)",
                "recommendation": "Negotiate down to officer certification"
            })

        if hasObligation and hasRetentionException and not requiresAffidavit:
            findings.append({
                "severity": "green",
                "finding": "Return/destruction provisions acceptable with retention exception"
            })

        return {
            "section": "Return and Destruction",
            "findings": findings
        }

    def _checkProblematicProvisions(self, ndaData: Dict[str, Any]) -> Dict[str, Any]:
        """Check for problematic provisions that should not be in an NDA."""
        findings = []
        found = ndaData.get("problematic_provisions", [])

        redProvisions = ["non_solicitation", "non_compete", "exclusivity",
                         "standstill", "broad_residuals", "ip_assignment",
                         "liquidated_damages"]
        yellowProvisions = ["audit_rights", "narrow_residuals"]

        for provision in found:
            if provision in redProvisions:
                findings.append({
                    "severity": "red",
                    "finding": f"Problematic provision found: {provision.replace('_', ' ')}",
                    "recommendation": self._getProvisionRecommendation(provision)
                })
            elif provision in yellowProvisions:
                findings.append({
                    "severity": "yellow",
                    "finding": f"Unusual provision found: {provision.replace('_', ' ')}",
                    "recommendation": self._getProvisionRecommendation(provision)
                })

        if not found:
            findings.append({
                "severity": "green",
                "finding": "No problematic provisions detected"
            })

        return {
            "section": "Problematic Provisions",
            "findings": findings,
            "provisions_found": found
        }

    def _checkGoverningLaw(self, ndaData: Dict[str, Any]) -> Dict[str, Any]:
        """Check governing law and jurisdiction."""
        findings = []
        jurisdiction = ndaData.get("governing_law", "")
        hasMandatoryArbitration = ndaData.get("has_mandatory_arbitration", False)
        jurisdictionAcceptable = ndaData.get("jurisdiction_acceptable", True)

        if not jurisdiction:
            findings.append({
                "severity": "yellow",
                "finding": "No governing law specified",
                "recommendation": "Add governing law clause with preferred jurisdiction"
            })
        elif not jurisdictionAcceptable:
            if hasMandatoryArbitration:
                findings.append({
                    "severity": "red",
                    "finding": f"Highly unfavorable jurisdiction ({jurisdiction}) with mandatory arbitration",
                    "recommendation": "Negotiate governing law to acceptable jurisdiction"
                })
            else:
                findings.append({
                    "severity": "yellow",
                    "finding": f"Non-preferred jurisdiction: {jurisdiction}",
                    "recommendation": "Negotiate to preferred jurisdiction if possible"
                })
        else:
            findings.append({
                "severity": "green",
                "finding": f"Governing law ({jurisdiction}) is acceptable"
            })

        if hasMandatoryArbitration and jurisdictionAcceptable:
            findings.append({
                "severity": "yellow",
                "finding": "Mandatory arbitration (litigation generally preferred for NDA disputes)",
                "recommendation": "Negotiate for litigation option"
            })

        return {
            "section": "Governing Law and Jurisdiction",
            "findings": findings
        }

    def _checkRemedies(self, ndaData: Dict[str, Any]) -> Dict[str, Any]:
        """Check remedies provisions."""
        findings = []
        hasInjunctiveRelief = ndaData.get("has_injunctive_relief", True)
        hasLiquidatedDamages = ndaData.get("has_liquidated_damages", False)
        isMutualRemedies = ndaData.get("is_mutual_remedies", True)
        ndaType = ndaData.get("nda_type", "mutual")

        if hasLiquidatedDamages:
            findings.append({
                "severity": "red",
                "finding": "Liquidated damages clause in NDA",
                "recommendation": "Remove liquidated damages provision entirely"
            })

        if ndaType == "mutual" and not isMutualRemedies:
            findings.append({
                "severity": "yellow",
                "finding": "Asymmetric remedies in mutual NDA",
                "recommendation": "Remedies should apply equally to both parties"
            })

        if hasInjunctiveRelief and not hasLiquidatedDamages:
            findings.append({
                "severity": "green",
                "finding": "Standard remedies provisions (injunctive relief acknowledgment)"
            })

        return {
            "section": "Remedies",
            "findings": findings
        }

    # --- Helper methods ---

    def _categorizeIssues(
        self,
        result: Dict[str, Any],
        redIssues: List,
        yellowIssues: List,
        greenNotes: List
    ) -> None:
        """Sort findings into red, yellow, green categories."""
        for finding in result.get("findings", []):
            severity = finding.get("severity", "green")
            entry = {
                "section": result["section"],
                "finding": finding["finding"],
                "recommendation": finding.get("recommendation")
            }
            if severity == "red":
                redIssues.append(entry)
            elif severity == "yellow":
                yellowIssues.append(entry)
            else:
                greenNotes.append(entry)

    def _getClassificationLabel(self, classification: str) -> str:
        """Get human-readable label for classification."""
        labels = {
            "GREEN": "Standard Approval - No counsel review required",
            "YELLOW": "Counsel Review Needed - Minor issues to address",
            "RED": "Significant Issues - Full legal review required"
        }
        return labels.get(classification, "Unknown")

    def _getRoutingRecommendation(
        self,
        classification: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get routing recommendation based on classification."""
        routingMap = {
            "GREEN": {
                "action": "Approve and route for signature per delegation of authority",
                "reviewer": "Standard signatory (delegation of authority)",
                "timeline": "Same day",
                "notes": "No counsel review required. Proceed with standard approval process."
            },
            "YELLOW": {
                "action": "Send to designated reviewer with specific issues flagged",
                "reviewer": "Designated NDA reviewer / Junior counsel",
                "timeline": "1-2 business days",
                "notes": "Counsel can likely resolve with minor redlines in a single review pass."
            },
            "RED": {
                "action": "Full legal review required. Prepare counterproposal or send standard form.",
                "reviewer": "Senior counsel / Head of legal",
                "timeline": "3-5 business days",
                "notes": "Do not sign. Requires negotiation, counterproposal with standard form NDA, or rejection."
            }
        }
        result = routingMap.get(classification, routingMap["RED"])
        result["classification"] = classification
        return result

    def _getProvisionRecommendation(self, provision: str) -> str:
        """Get specific recommendation for a problematic provision."""
        recommendations = {
            "non_solicitation": "Delete entirely. If counterparty insists, limit to targeted solicitation (12 months max).",
            "non_compete": "Delete entirely. Non-compete provisions do not belong in NDAs.",
            "exclusivity": "Delete. NDA should not restrict discussions with others.",
            "standstill": "Delete unless M&A context warrants it.",
            "broad_residuals": "Delete or narrow to unaided memory only, excluding trade secrets and patentable info.",
            "narrow_residuals": "Verify limited to unaided memory, excludes trade secrets and patents.",
            "ip_assignment": "Delete. NDA should not grant any IP rights.",
            "audit_rights": "Unusual in NDAs. Remove or limit scope with reasonable notice.",
            "liquidated_damages": "Delete entirely. Liquidated damages are inappropriate in standard NDAs."
        }
        return recommendations.get(provision, "Review and consider removal.")

    def _generateSummary(
        self,
        classification: str,
        ndaData: Dict[str, Any],
        redIssues: List,
        yellowIssues: List
    ) -> str:
        """Generate a text summary of the triage result."""
        counterparty = ndaData.get("counterparty", "Unknown")
        ndaType = ndaData.get("nda_type", "unknown")

        lines = [
            f"NDA TRIAGE SUMMARY",
            f"Counterparty: {counterparty}",
            f"Type: {ndaType}",
            f"Classification: {classification}",
            ""
        ]

        if classification == "GREEN":
            lines.append("This NDA meets standard criteria and can be approved through normal channels.")
        elif classification == "YELLOW":
            lines.append(f"This NDA has {len(yellowIssues)} issue(s) requiring counsel review:")
            for issue in yellowIssues:
                lines.append(f"  - [{issue['section']}] {issue['finding']}")
        else:
            lines.append(f"This NDA has {len(redIssues)} significant issue(s) requiring full legal review:")
            for issue in redIssues:
                lines.append(f"  - [{issue['section']}] {issue['finding']}")
            if yellowIssues:
                lines.append(f"\nAdditionally, {len(yellowIssues)} minor issue(s):")
                for issue in yellowIssues:
                    lines.append(f"  - [{issue['section']}] {issue['finding']}")

        return "\n".join(lines)


def main():
    """Main entry point for the NDA Triage STF."""
    try:
        inputData = readInput()
        userInput = inputData.get("input", {})

        operation = userInput.get("operation")
        if not operation:
            raise ValueError("Missing required field: operation")

        # API client is optional for most NDA triage operations
        apiClient = None
        try:
            apiClient = createApiClient(inputData)
        except Exception:
            logger.info("No API client available (non-DB operations only)")

        analyzer = NdaTriageAnalyzer(apiClient)

        if operation == "triage_nda":
            validateRequiredFields(userInput, ["nda_data"])
            result = analyzer.triageNda(ndaData=userInput["nda_data"])

        elif operation == "check_clause":
            validateRequiredFields(userInput, ["clause_type", "clause_data"])
            result = analyzer.checkClause(
                clauseType=userInput["clause_type"],
                clauseData=userInput["clause_data"]
            )

        elif operation == "get_routing_recommendation":
            validateRequiredFields(userInput, ["classification"])
            result = analyzer.getRoutingRecommendation(
                classification=userInput["classification"],
                context=userInput.get("context")
            )

        elif operation == "generate_checklist":
            result = analyzer.generateChecklist(
                ndaType=userInput.get("nda_type", "mutual")
            )

        elif operation == "describe":
            result = analyzer.describe()

        else:
            raise ValueError(
                f"Unknown operation: {operation}. "
                f"Valid operations: triage_nda, check_clause, "
                f"get_routing_recommendation, generate_checklist, describe"
            )

        writeOutput({
            "status": "success",
            "operation": operation,
            "data": result
        })

    except ValueError as e:
        logger.error(f"Validation error in NdaTriageAnalyzer: {str(e)}")
        writeError(e, "ValidationError")
    except Exception as e:
        logger.error(f"Unexpected error in NdaTriageAnalyzer: {str(e)}", exc_info=True)
        writeError(e)


if __name__ == "__main__":
    main()
