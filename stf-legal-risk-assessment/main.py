#!/usr/bin/env python3
"""
D6E Docker STF: Legal Risk Assessment

Overview:
  Assesses and classifies legal risks using a severity-by-likelihood
  framework with escalation criteria and documentation generation.

Main Operations:
  - assess_risk: Perform full risk assessment with scoring
  - calculate_risk_score: Calculate risk score from severity and likelihood
  - generate_risk_memo: Generate structured risk assessment memo
  - create_risk_register_entry: Create risk register entry
  - get_escalation_recommendation: Get escalation guidance based on risk level
  - generate_risk_matrix: Generate risk matrix visualization

Limitations:
  - Provides legal workflow assistance, not legal advice
  - Risk assessments should be reviewed by qualified legal professionals
  - Framework is a starting point for organization-specific customization
"""

import sys
import os
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from utils import (
    logger, readInput, writeOutput, writeError,
    createApiClient, validateRequiredFields,
    generateId, getCurrentTimestamp, classifyRiskLevel
)


# Severity and likelihood scales
SEVERITY_SCALE = {
    1: {"label": "Negligible", "description": "Minor inconvenience; no material financial, operational, or reputational impact."},
    2: {"label": "Low", "description": "Limited impact; minor financial exposure (< 1% of relevant value); minor operational disruption."},
    3: {"label": "Moderate", "description": "Meaningful impact; material financial exposure (1-5% of relevant value); noticeable disruption."},
    4: {"label": "High", "description": "Significant impact; substantial financial exposure (5-25% of relevant value); significant disruption."},
    5: {"label": "Critical", "description": "Severe impact; major financial exposure (> 25% of relevant value); fundamental disruption."}
}

LIKELIHOOD_SCALE = {
    1: {"label": "Remote", "description": "Highly unlikely; no known precedent; would require exceptional circumstances."},
    2: {"label": "Unlikely", "description": "Could occur but not expected; limited precedent; requires specific triggering events."},
    3: {"label": "Possible", "description": "May occur; some precedent exists; triggering events are foreseeable."},
    4: {"label": "Likely", "description": "Probably will occur; clear precedent; triggering events are common."},
    5: {"label": "Almost Certain", "description": "Expected to occur; strong precedent or pattern; triggering events are present."}
}

RISK_CATEGORIES = [
    "Contract", "Regulatory", "Litigation", "IP",
    "Data Privacy", "Employment", "Corporate", "Other"
]


class LegalRiskAssessor:
    """
    Assesses and classifies legal risks using severity x likelihood framework.
    """

    def __init__(self, apiClient=None):
        """
        Initialize risk assessor.

        Args:
            apiClient: Optional D6eApiClient for database operations
        """
        self.api = apiClient

    def assessRisk(self, riskData: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform full risk assessment.

        Args:
            riskData: Risk details including:
                - description: Risk description
                - category: Risk category
                - severity: Severity rating (1-5)
                - likelihood: Likelihood rating (1-5)
                - context: Background and context
                - contributing_factors: List of factors increasing risk
                - mitigating_factors: List of factors decreasing risk
                - financial_exposure: Optional estimated financial exposure
                - matter_reference: Optional matter reference

        Returns:
            Complete risk assessment with classification and recommendations
        """
        logger.info(f"Assessing risk: {riskData.get('description', 'unknown')[:50]}")

        severity = riskData.get("severity", 3)
        likelihood = riskData.get("likelihood", 3)

        if not (1 <= severity <= 5):
            raise ValueError(f"Severity must be 1-5, got: {severity}")
        if not (1 <= likelihood <= 5):
            raise ValueError(f"Likelihood must be 1-5, got: {likelihood}")

        riskScore = severity * likelihood
        riskLevel = classifyRiskLevel(riskScore)

        severityInfo = SEVERITY_SCALE[severity]
        likelihoodInfo = LIKELIHOOD_SCALE[likelihood]

        recommendedActions = self._getRecommendedActions(riskLevel["color"])
        escalation = self._getEscalationGuidance(riskLevel["color"], riskData)
        mitigationOptions = self._suggestMitigations(
            riskData.get("category", "Other"),
            riskLevel["color"],
            riskData
        )
        monitoringPlan = self._getMonitoringPlan(riskLevel["color"])

        return {
            "assessment_id": generateId(),
            "timestamp": getCurrentTimestamp(),
            "risk_description": riskData.get("description", ""),
            "category": riskData.get("category", "Other"),
            "matter_reference": riskData.get("matter_reference"),
            "severity": {
                "rating": severity,
                "label": severityInfo["label"],
                "description": severityInfo["description"]
            },
            "likelihood": {
                "rating": likelihood,
                "label": likelihoodInfo["label"],
                "description": likelihoodInfo["description"]
            },
            "risk_score": riskScore,
            "risk_level": riskLevel,
            "contributing_factors": riskData.get("contributing_factors", []),
            "mitigating_factors": riskData.get("mitigating_factors", []),
            "financial_exposure": riskData.get("financial_exposure"),
            "recommended_actions": recommendedActions,
            "escalation": escalation,
            "mitigation_options": mitigationOptions,
            "monitoring_plan": monitoringPlan
        }

    def calculateRiskScore(
        self,
        severity: int,
        likelihood: int
    ) -> Dict[str, Any]:
        """
        Calculate risk score from severity and likelihood.

        Args:
            severity: Severity rating (1-5)
            likelihood: Likelihood rating (1-5)

        Returns:
            Risk score with classification
        """
        if not (1 <= severity <= 5):
            raise ValueError(f"Severity must be 1-5, got: {severity}")
        if not (1 <= likelihood <= 5):
            raise ValueError(f"Likelihood must be 1-5, got: {likelihood}")

        score = severity * likelihood
        level = classifyRiskLevel(score)

        return {
            "severity": {"rating": severity, "label": SEVERITY_SCALE[severity]["label"]},
            "likelihood": {"rating": likelihood, "label": LIKELIHOOD_SCALE[likelihood]["label"]},
            "risk_score": score,
            "risk_level": level
        }

    def generateRiskMemo(self, assessmentData: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured risk assessment memo.

        Args:
            assessmentData: Full assessment data or risk input data

        Returns:
            Structured memo in text and structured format
        """
        logger.info("Generating risk memo")

        # If raw input, perform assessment first
        if "risk_score" not in assessmentData:
            assessmentData = self.assessRisk(assessmentData)

        memo = self._formatMemo(assessmentData)

        return {
            "memo_id": generateId(),
            "generated_at": getCurrentTimestamp(),
            "structured_memo": assessmentData,
            "text_memo": memo
        }

    def createRiskRegisterEntry(self, riskData: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a risk register entry.

        Args:
            riskData: Risk details

        Returns:
            Structured risk register entry
        """
        logger.info("Creating risk register entry")

        severity = riskData.get("severity", 3)
        likelihood = riskData.get("likelihood", 3)
        score = severity * likelihood
        level = classifyRiskLevel(score)

        return {
            "risk_id": generateId(),
            "date_identified": getCurrentTimestamp(),
            "description": riskData.get("description", ""),
            "category": riskData.get("category", "Other"),
            "severity": {
                "rating": severity,
                "label": SEVERITY_SCALE.get(severity, {}).get("label", "Unknown")
            },
            "likelihood": {
                "rating": likelihood,
                "label": LIKELIHOOD_SCALE.get(likelihood, {}).get("label", "Unknown")
            },
            "risk_score": score,
            "risk_level": level["color"],
            "risk_label": level["label"],
            "owner": riskData.get("owner", "Unassigned"),
            "mitigations": riskData.get("mitigations", []),
            "status": "Open",
            "review_date": riskData.get("review_date"),
            "notes": riskData.get("notes", "")
        }

    def getEscalationRecommendation(
        self,
        riskLevel: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Get escalation recommendation based on risk level.

        Args:
            riskLevel: GREEN, YELLOW, ORANGE, or RED
            context: Optional additional context

        Returns:
            Escalation recommendation with specific guidance
        """
        return self._getEscalationGuidance(riskLevel.upper(), context or {})

    def generateRiskMatrix(self) -> Dict[str, Any]:
        """
        Generate risk matrix visualization data.

        Returns:
            Risk matrix structure with all cells and their risk levels
        """
        matrix = []
        for severity in range(5, 0, -1):
            row = []
            for likelihood in range(1, 6):
                score = severity * likelihood
                level = classifyRiskLevel(score)
                row.append({
                    "severity": severity,
                    "likelihood": likelihood,
                    "score": score,
                    "color": level["color"],
                    "label": level["label"]
                })
            matrix.append(row)

        # Text representation
        textMatrix = self._generateTextMatrix()

        return {
            "matrix": matrix,
            "severity_scale": SEVERITY_SCALE,
            "likelihood_scale": LIKELIHOOD_SCALE,
            "risk_levels": {
                "GREEN": {"range": "1-4", "label": "Low Risk"},
                "YELLOW": {"range": "5-9", "label": "Medium Risk"},
                "ORANGE": {"range": "10-15", "label": "High Risk"},
                "RED": {"range": "16-25", "label": "Critical Risk"}
            },
            "text_representation": textMatrix
        }

    # --- Internal methods ---

    def _getRecommendedActions(self, riskColor: str) -> List[Dict[str, Any]]:
        """Get recommended actions for a risk level."""
        actionsMap = {
            "GREEN": [
                {"action": "Accept", "description": "Acknowledge risk and proceed with standard controls"},
                {"action": "Document", "description": "Record in risk register for tracking"},
                {"action": "Monitor", "description": "Include in periodic reviews (quarterly or annually)"}
            ],
            "YELLOW": [
                {"action": "Mitigate", "description": "Implement specific controls to reduce exposure"},
                {"action": "Monitor actively", "description": "Review monthly or as triggers occur"},
                {"action": "Document thoroughly", "description": "Record risk, mitigations, and rationale"},
                {"action": "Assign owner", "description": "Ensure specific person is responsible"},
                {"action": "Brief stakeholders", "description": "Inform relevant business stakeholders"}
            ],
            "ORANGE": [
                {"action": "Escalate to senior counsel", "description": "Brief head of legal or designated senior counsel"},
                {"action": "Develop mitigation plan", "description": "Create specific, actionable plan"},
                {"action": "Brief leadership", "description": "Inform relevant business leaders"},
                {"action": "Set weekly review", "description": "Review weekly or at defined milestones"},
                {"action": "Consider outside counsel", "description": "Engage specialized advice if needed"},
                {"action": "Define contingency plan", "description": "Plan for risk materialization"}
            ],
            "RED": [
                {"action": "Immediate escalation", "description": "Brief General Counsel, C-suite, and/or Board"},
                {"action": "Engage outside counsel", "description": "Retain specialized outside counsel immediately"},
                {"action": "Establish response team", "description": "Dedicated team with clear roles"},
                {"action": "Consider insurance notification", "description": "Notify insurers if applicable"},
                {"action": "Activate crisis management", "description": "If reputational risk is involved"},
                {"action": "Preserve evidence", "description": "Implement litigation hold if proceedings possible"},
                {"action": "Daily review", "description": "Active management until resolved or reduced"}
            ]
        }
        return actionsMap.get(riskColor, actionsMap["YELLOW"])

    def _getEscalationGuidance(self, riskColor: str, riskData: Dict) -> Dict[str, Any]:
        """Get escalation guidance based on risk level and context."""
        category = riskData.get("category", "Other")

        # Check for mandatory outside counsel triggers
        mandatoryOutsideCounsel = [
            "active_litigation", "government_investigation",
            "criminal_exposure", "securities_issues", "board_level"
        ]
        triggers = riskData.get("escalation_triggers", [])
        needsOutsideCounsel = any(t in mandatoryOutsideCounsel for t in triggers)

        guidanceMap = {
            "GREEN": {
                "escalation_required": False,
                "escalation_to": "No escalation required",
                "outside_counsel": False,
                "review_cadence": "Quarterly",
                "reporting": "Standard risk register"
            },
            "YELLOW": {
                "escalation_required": False,
                "escalation_to": "Team lead / Assigned risk owner",
                "outside_counsel": False,
                "review_cadence": "Monthly",
                "reporting": "Team risk review meetings"
            },
            "ORANGE": {
                "escalation_required": True,
                "escalation_to": "Senior Counsel / Head of Legal",
                "outside_counsel": needsOutsideCounsel or category in ["Litigation", "Regulatory"],
                "review_cadence": "Weekly",
                "reporting": "Senior leadership briefing"
            },
            "RED": {
                "escalation_required": True,
                "escalation_to": "General Counsel / C-Suite / Board (as appropriate)",
                "outside_counsel": True,
                "review_cadence": "Daily or more frequent",
                "reporting": "Board risk reporting"
            }
        }

        guidance = guidanceMap.get(riskColor, guidanceMap["ORANGE"])
        guidance["risk_level"] = riskColor

        if needsOutsideCounsel:
            guidance["outside_counsel_reason"] = (
                f"Mandatory engagement: {', '.join(t for t in triggers if t in mandatoryOutsideCounsel)}"
            )

        return guidance

    def _suggestMitigations(
        self,
        category: str,
        riskColor: str,
        riskData: Dict
    ) -> List[Dict[str, Any]]:
        """Suggest mitigation options based on category and risk level."""
        mitigations = []

        categoryMitigations = {
            "Contract": [
                {"option": "Negotiate protective terms", "effectiveness": "High", "effort": "Medium"},
                {"option": "Add indemnification provisions", "effectiveness": "High", "effort": "Medium"},
                {"option": "Limit liability exposure", "effectiveness": "High", "effort": "Low"},
                {"option": "Include termination rights", "effectiveness": "Medium", "effort": "Low"}
            ],
            "Regulatory": [
                {"option": "Engage compliance audit", "effectiveness": "High", "effort": "High"},
                {"option": "Implement compliance program", "effectiveness": "High", "effort": "High"},
                {"option": "Retain regulatory counsel", "effectiveness": "High", "effort": "Medium"},
                {"option": "Self-report if appropriate", "effectiveness": "Medium", "effort": "Medium"}
            ],
            "Litigation": [
                {"option": "Preserve evidence (litigation hold)", "effectiveness": "High", "effort": "Medium"},
                {"option": "Retain litigation counsel", "effectiveness": "High", "effort": "High"},
                {"option": "Explore early resolution", "effectiveness": "Medium", "effort": "Medium"},
                {"option": "Assess insurance coverage", "effectiveness": "Medium", "effort": "Low"}
            ],
            "IP": [
                {"option": "Conduct freedom-to-operate analysis", "effectiveness": "High", "effort": "High"},
                {"option": "Secure IP registrations", "effectiveness": "High", "effort": "Medium"},
                {"option": "License necessary rights", "effectiveness": "High", "effort": "Medium"},
                {"option": "Implement IP monitoring", "effectiveness": "Medium", "effort": "Low"}
            ],
            "Data Privacy": [
                {"option": "Conduct data mapping", "effectiveness": "High", "effort": "High"},
                {"option": "Implement technical safeguards", "effectiveness": "High", "effort": "High"},
                {"option": "Update privacy notices", "effectiveness": "Medium", "effort": "Low"},
                {"option": "Execute DPA with processors", "effectiveness": "High", "effort": "Medium"}
            ]
        }

        mitigations = categoryMitigations.get(category, [
            {"option": "Conduct detailed analysis", "effectiveness": "Medium", "effort": "Medium"},
            {"option": "Seek specialized advice", "effectiveness": "High", "effort": "Medium"},
            {"option": "Implement controls", "effectiveness": "Medium", "effort": "Medium"}
        ])

        # Add recommended flag
        for m in mitigations:
            m["recommended"] = m["effectiveness"] == "High" or riskColor in ["ORANGE", "RED"]

        return mitigations

    def _getMonitoringPlan(self, riskColor: str) -> Dict[str, Any]:
        """Get monitoring plan based on risk level."""
        plans = {
            "GREEN": {
                "review_frequency": "Quarterly or annually",
                "escalation_triggers": ["Risk score increases", "New information emerges"],
                "reporting": "Include in periodic risk register review"
            },
            "YELLOW": {
                "review_frequency": "Monthly or as triggers occur",
                "escalation_triggers": ["Score increases to ORANGE/RED", "Triggering event occurs", "Conditions change materially"],
                "reporting": "Report to risk owner and team lead"
            },
            "ORANGE": {
                "review_frequency": "Weekly or at defined milestones",
                "escalation_triggers": ["Score increases to RED", "Mitigation plan fails", "New material information"],
                "reporting": "Brief senior leadership weekly"
            },
            "RED": {
                "review_frequency": "Daily or more frequent",
                "escalation_triggers": ["Immediate escalation already in place", "Monitor for resolution or further deterioration"],
                "reporting": "Active management with daily status updates to executive team"
            }
        }
        return plans.get(riskColor, plans["YELLOW"])

    def _formatMemo(self, assessment: Dict) -> str:
        """Format assessment as text memo."""
        lines = [
            "## Legal Risk Assessment",
            "",
            f"**Date**: {assessment.get('timestamp', getCurrentTimestamp())}",
            f"**Matter**: {assessment.get('risk_description', 'N/A')}",
            f"**Category**: {assessment.get('category', 'Other')}",
            "",
            "### Risk Analysis",
            "",
            f"#### Severity: {assessment.get('severity', {}).get('rating', 'N/A')} - {assessment.get('severity', {}).get('label', 'N/A')}",
            assessment.get('severity', {}).get('description', ''),
            "",
            f"#### Likelihood: {assessment.get('likelihood', {}).get('rating', 'N/A')} - {assessment.get('likelihood', {}).get('label', 'N/A')}",
            assessment.get('likelihood', {}).get('description', ''),
            "",
            f"#### Risk Score: {assessment.get('risk_score', 'N/A')} - {assessment.get('risk_level', {}).get('color', 'N/A')} ({assessment.get('risk_level', {}).get('label', 'N/A')})",
            "",
            "### Contributing Factors",
        ]

        for factor in assessment.get("contributing_factors", []):
            lines.append(f"- {factor}")

        lines.append("")
        lines.append("### Mitigating Factors")

        for factor in assessment.get("mitigating_factors", []):
            lines.append(f"- {factor}")

        lines.append("")
        lines.append("### Recommended Actions")

        for action in assessment.get("recommended_actions", []):
            lines.append(f"- **{action['action']}**: {action['description']}")

        return "\n".join(lines)

    def _generateTextMatrix(self) -> str:
        """Generate text-based risk matrix."""
        lines = [
            "                    LIKELIHOOD",
            "                Remote  Unlikely  Possible  Likely  Almost Certain",
            "                  (1)     (2)       (3)      (4)        (5)",
            "SEVERITY"
        ]

        for severity in range(5, 0, -1):
            label = SEVERITY_SCALE[severity]["label"]
            scores = []
            for likelihood in range(1, 6):
                score = severity * likelihood
                level = classifyRiskLevel(score)
                scores.append(f"{score:>4}")
            row = f"{label:>10}({severity})  |{'   |'.join(scores)}     |"
            lines.append(row)

        return "\n".join(lines)


def main():
    """Main entry point for the Legal Risk Assessment STF."""
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

        assessor = LegalRiskAssessor(apiClient)

        if operation == "assess_risk":
            validateRequiredFields(userInput, ["risk_data"])
            result = assessor.assessRisk(riskData=userInput["risk_data"])

        elif operation == "calculate_risk_score":
            validateRequiredFields(userInput, ["severity", "likelihood"])
            result = assessor.calculateRiskScore(
                severity=int(userInput["severity"]),
                likelihood=int(userInput["likelihood"])
            )

        elif operation == "generate_risk_memo":
            validateRequiredFields(userInput, ["assessment_data"])
            result = assessor.generateRiskMemo(
                assessmentData=userInput["assessment_data"]
            )

        elif operation == "create_risk_register_entry":
            validateRequiredFields(userInput, ["risk_data"])
            result = assessor.createRiskRegisterEntry(
                riskData=userInput["risk_data"]
            )

        elif operation == "get_escalation_recommendation":
            validateRequiredFields(userInput, ["risk_level"])
            result = assessor.getEscalationRecommendation(
                riskLevel=userInput["risk_level"],
                context=userInput.get("context")
            )

        elif operation == "generate_risk_matrix":
            result = assessor.generateRiskMatrix()

        else:
            raise ValueError(
                f"Unknown operation: {operation}. "
                f"Valid operations: assess_risk, calculate_risk_score, "
                f"generate_risk_memo, create_risk_register_entry, "
                f"get_escalation_recommendation, generate_risk_matrix"
            )

        writeOutput({
            "status": "success",
            "operation": operation,
            "data": result
        })

    except ValueError as e:
        logger.error(f"Validation error in LegalRiskAssessor: {str(e)}")
        writeError(e, "ValidationError")
    except Exception as e:
        logger.error(f"Unexpected error in LegalRiskAssessor: {str(e)}", exc_info=True)
        writeError(e)


if __name__ == "__main__":
    main()
