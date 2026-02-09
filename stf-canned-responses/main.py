#!/usr/bin/env python3
"""
D6E Docker STF: Canned Responses

Overview:
  Generates and manages templated responses for common legal inquiries.
  Identifies escalation triggers requiring individualized attention.

Main Operations:
  - generate_response: Generate a response from a template category
  - check_escalation: Check for escalation triggers before responding
  - list_templates: List available template categories
  - create_template: Create a new response template
  - customize_response: Customize a generated response with variables
  - describe: Return input schema and available operations

Limitations:
  - Provides legal workflow assistance, not legal advice
  - Templated responses should be reviewed before sending
  - Does not generate AI text; uses structured templates with variable substitution
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


# Template categories
TEMPLATE_CATEGORIES = [
    "dsr", "discovery_hold", "privacy_inquiry",
    "vendor_legal", "nda_request", "subpoena",
    "insurance_notification"
]

# Universal escalation triggers that apply to all categories
UNIVERSAL_ESCALATION_TRIGGERS = [
    "potential_litigation_or_investigation",
    "from_regulator_or_government",
    "creates_binding_commitment",
    "potential_criminal_liability",
    "media_attention",
    "unprecedented_situation",
    "conflicting_jurisdictions",
    "involves_executive_or_board"
]

# Category-specific escalation triggers
CATEGORY_ESCALATION_TRIGGERS = {
    "dsr": [
        "involves_minor",
        "data_under_litigation_hold",
        "requester_in_active_litigation",
        "employee_with_hr_matter",
        "overbroad_scope",
        "special_category_data"
    ],
    "discovery_hold": [
        "potential_criminal_liability",
        "unclear_preservation_scope",
        "conflicts_with_deletion_requirements",
        "prior_related_holds",
        "custodian_objects_to_scope"
    ],
    "vendor_legal": [
        "vendor_disputes_terms",
        "vendor_threatens_litigation",
        "affects_ongoing_negotiation",
        "regulatory_compliance_question"
    ],
    "subpoena": [
        "always_requires_counsel_review",
        "privilege_issues",
        "third_party_data_involved",
        "cross_border_production",
        "unreasonable_timeline"
    ]
}


class CannedResponseGenerator:
    """
    Manages and generates templated responses for common legal inquiries.
    """

    def __init__(self, apiClient=None):
        """
        Initialize response generator.

        Args:
            apiClient: Optional D6eApiClient for database operations
        """
        self.api = apiClient
        self.templates = self._loadDefaultTemplates()

    def generateResponse(
        self,
        category: str,
        subCategory: str,
        variables: Dict[str, str],
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """
        Generate a response from a template.

        Args:
            category: Template category (dsr, discovery_hold, etc.)
            subCategory: Specific template within category
            variables: Variable values for template substitution
            tone: Response tone (professional, formal, empathetic)

        Returns:
            Generated response with metadata
        """
        logger.info(f"Generating response for: {category}/{subCategory}")

        if category not in TEMPLATE_CATEGORIES:
            raise ValueError(
                f"Unknown category: {category}. "
                f"Valid categories: {', '.join(TEMPLATE_CATEGORIES)}"
            )

        categoryTemplates = self.templates.get(category, {})
        template = categoryTemplates.get(subCategory)

        if not template:
            availableSubs = list(categoryTemplates.keys())
            raise ValueError(
                f"Unknown sub-category: {subCategory} in {category}. "
                f"Available: {', '.join(availableSubs)}"
            )

        # Check for missing required variables
        requiredVars = template.get("required_variables", [])
        missingVars = [v for v in requiredVars if v not in variables]
        if missingVars:
            raise ValueError(
                f"Missing required variables: {', '.join(missingVars)}"
            )

        # Substitute variables in template
        responseBody = template["body"]
        subjectLine = template.get("subject", "")

        for varName, varValue in variables.items():
            placeholder = "{{" + varName + "}}"
            responseBody = responseBody.replace(placeholder, str(varValue))
            subjectLine = subjectLine.replace(placeholder, str(varValue))

        return {
            "response_id": generateId(),
            "timestamp": getCurrentTimestamp(),
            "category": category,
            "sub_category": subCategory,
            "subject": subjectLine,
            "body": responseBody,
            "tone": tone,
            "variables_used": variables,
            "follow_up_actions": template.get("follow_up_actions", []),
            "notes": template.get("notes", ""),
            "disclaimer": "This response was generated from a template. Review before sending."
        }

    def checkEscalation(
        self,
        category: str,
        triggers: List[str]
    ) -> Dict[str, Any]:
        """
        Check for escalation triggers before generating a response.

        Args:
            category: Template category
            triggers: List of detected trigger identifiers

        Returns:
            Escalation check result with recommendations
        """
        logger.info(f"Checking escalation triggers for category: {category}")

        universalMatches = [t for t in triggers if t in UNIVERSAL_ESCALATION_TRIGGERS]
        categoryTriggers = CATEGORY_ESCALATION_TRIGGERS.get(category, [])
        categoryMatches = [t for t in triggers if t in categoryTriggers]

        allMatches = universalMatches + categoryMatches
        shouldEscalate = len(allMatches) > 0

        # Subpoena always requires counsel review
        if category == "subpoena":
            shouldEscalate = True
            if "always_requires_counsel_review" not in allMatches:
                allMatches.append("always_requires_counsel_review")

        result = {
            "category": category,
            "should_escalate": shouldEscalate,
            "triggered_by": allMatches,
            "universal_triggers": universalMatches,
            "category_triggers": categoryMatches
        }

        if shouldEscalate:
            result["recommendation"] = {
                "action": "STOP - Do not generate templated response",
                "reason": f"Escalation trigger(s) detected: {', '.join(allMatches)}",
                "escalation_path": self._getEscalationPath(category, allMatches),
                "alternative": "Prepare DRAFT for counsel review (clearly marked as draft)"
            }
        else:
            result["recommendation"] = {
                "action": "PROCEED - Templated response appropriate",
                "note": "Review before sending"
            }

        return result

    def listTemplates(
        self,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List available template categories and sub-categories.

        Args:
            category: Optional specific category to list

        Returns:
            Available templates with metadata
        """
        if category:
            if category not in self.templates:
                raise ValueError(f"Unknown category: {category}")
            categoryTemplates = self.templates[category]
            return {
                "category": category,
                "templates": [
                    {
                        "sub_category": subCat,
                        "description": tmpl.get("description", ""),
                        "required_variables": tmpl.get("required_variables", []),
                        "escalation_triggers": CATEGORY_ESCALATION_TRIGGERS.get(category, [])
                    }
                    for subCat, tmpl in categoryTemplates.items()
                ]
            }

        return {
            "categories": [
                {
                    "category": cat,
                    "sub_categories": list(self.templates.get(cat, {}).keys()),
                    "template_count": len(self.templates.get(cat, {})),
                    "escalation_triggers": CATEGORY_ESCALATION_TRIGGERS.get(cat, [])
                }
                for cat in TEMPLATE_CATEGORIES
            ],
            "universal_escalation_triggers": UNIVERSAL_ESCALATION_TRIGGERS
        }

    def createTemplate(self, templateData: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new response template.

        Args:
            templateData: Template definition including:
                - category: Category name
                - sub_category: Sub-category name
                - description: Template description
                - subject: Email subject template
                - body: Response body template with {{variable}} placeholders
                - required_variables: List of required variable names
                - follow_up_actions: List of follow-up actions
                - escalation_triggers: List of triggers for this template

        Returns:
            Created template confirmation
        """
        logger.info(f"Creating template: {templateData.get('category')}/{templateData.get('sub_category')}")

        validateRequiredFields(templateData, ["category", "sub_category", "body"])

        category = templateData["category"]
        subCategory = templateData["sub_category"]

        newTemplate = {
            "description": templateData.get("description", ""),
            "subject": templateData.get("subject", ""),
            "body": templateData["body"],
            "required_variables": templateData.get("required_variables", []),
            "follow_up_actions": templateData.get("follow_up_actions", []),
            "notes": templateData.get("notes", ""),
            "created_at": getCurrentTimestamp()
        }

        if category not in self.templates:
            self.templates[category] = {}

        self.templates[category][subCategory] = newTemplate

        return {
            "template_id": generateId(),
            "category": category,
            "sub_category": subCategory,
            "status": "created",
            "template": newTemplate
        }

    def customizeResponse(
        self,
        responseBody: str,
        customizations: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Apply additional customizations to a generated response.

        Args:
            responseBody: Base response text
            customizations: Additional variable substitutions

        Returns:
            Customized response
        """
        customized = responseBody
        for varName, varValue in customizations.items():
            placeholder = "{{" + varName + "}}"
            customized = customized.replace(placeholder, str(varValue))

        # Check for remaining placeholders
        import re
        remaining = re.findall(r'\{\{(\w+)\}\}', customized)

        return {
            "customized_body": customized,
            "substitutions_applied": list(customizations.keys()),
            "remaining_placeholders": remaining,
            "is_complete": len(remaining) == 0
        }

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
                            "generate_response", "check_escalation", "list_templates",
                            "create_template", "customize_response", "describe"
                        ],
                        "description": "The operation to perform"
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "dsr", "discovery_hold", "privacy_inquiry",
                            "vendor_legal", "nda_request", "subpoena",
                            "insurance_notification"
                        ],
                        "description": "Template category"
                    },
                    "sub_category": {
                        "type": "string",
                        "description": "Specific template within the category"
                    },
                    "variables": {
                        "type": "object",
                        "description": "Variable values for template substitution (key-value pairs)"
                    },
                    "tone": {
                        "type": "string",
                        "enum": ["professional", "formal", "empathetic"],
                        "description": "Response tone"
                    },
                    "triggers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of detected escalation trigger identifiers"
                    },
                    "template_data": {
                        "type": "object",
                        "description": "Template definition for create_template",
                        "properties": {
                            "category": {"type": "string"},
                            "sub_category": {"type": "string"},
                            "description": {"type": "string"},
                            "subject": {"type": "string", "description": "Email subject template with {{variable}} placeholders"},
                            "body": {"type": "string", "description": "Response body template with {{variable}} placeholders"},
                            "required_variables": {"type": "array", "items": {"type": "string"}},
                            "follow_up_actions": {"type": "array", "items": {"type": "string"}},
                            "escalation_triggers": {"type": "array", "items": {"type": "string"}},
                            "notes": {"type": "string"}
                        },
                        "required": ["category", "sub_category", "body"]
                    },
                    "response_body": {
                        "type": "string",
                        "description": "Base response text for customization"
                    },
                    "customizations": {
                        "type": "object",
                        "description": "Additional variable substitutions for customize_response"
                    }
                },
                "required": ["operation"]
            },
            "operations": {
                "generate_response": {
                    "description": "Generate a templated response for common legal inquiries",
                    "required": ["category", "sub_category", "variables"],
                    "optional": ["tone"]
                },
                "check_escalation": {
                    "description": "Check for escalation triggers before generating a response",
                    "required": ["category", "triggers"],
                    "optional": []
                },
                "list_templates": {
                    "description": "List available template categories and sub-categories",
                    "required": [],
                    "optional": ["category"]
                },
                "create_template": {
                    "description": "Create a new response template",
                    "required": ["template_data"],
                    "optional": []
                },
                "customize_response": {
                    "description": "Apply additional customizations to a generated response body",
                    "required": ["response_body", "customizations"],
                    "optional": []
                },
                "describe": {
                    "description": "Return the input schema and available operations",
                    "required": [],
                    "optional": []
                }
            }
        }

    # --- Internal methods ---

    def _getEscalationPath(self, category: str, triggers: List[str]) -> str:
        """Get escalation path based on category and triggers."""
        if any(t in ["potential_criminal_liability", "from_regulator_or_government"] for t in triggers):
            return "Immediate escalation to General Counsel and outside counsel"
        if any(t in ["involves_executive_or_board", "media_attention"] for t in triggers):
            return "Escalate to General Counsel for handling"
        if category == "subpoena":
            return "Full counsel review required. Outside counsel recommended."
        return "Escalate to senior counsel for review and guidance"

    def _loadDefaultTemplates(self) -> Dict[str, Dict]:
        """Load default response templates."""
        return {
            "dsr": {
                "acknowledgment": {
                    "description": "Acknowledge receipt of a data subject request",
                    "subject": "Your Data {{request_type}} Request - Reference {{request_id}}",
                    "body": (
                        "Dear {{requester_name}},\n\n"
                        "We have received your request dated {{request_date}} to {{request_type}} "
                        "your personal data under {{regulation}}.\n\n"
                        "We are processing your request and will respond substantively by {{response_deadline}}.\n\n"
                        "If we need additional information to verify your identity or clarify your request, "
                        "we will contact you promptly.\n\n"
                        "For questions about this request, please contact {{contact_email}}.\n\n"
                        "Best regards,\n{{sender_name}}\n{{sender_title}}"
                    ),
                    "required_variables": [
                        "requester_name", "request_date", "request_type",
                        "regulation", "response_deadline", "request_id",
                        "contact_email", "sender_name", "sender_title"
                    ],
                    "follow_up_actions": [
                        "Log request in DSR register",
                        "Assign handler",
                        "Begin identity verification if needed",
                        "Set calendar reminder for response deadline"
                    ]
                },
                "identity_verification": {
                    "description": "Request identity verification from data subject",
                    "subject": "Identity Verification Required - Reference {{request_id}}",
                    "body": (
                        "Dear {{requester_name}},\n\n"
                        "Thank you for your data {{request_type}} request (Reference: {{request_id}}).\n\n"
                        "To protect your privacy and ensure we are responding to the rightful data subject, "
                        "we need to verify your identity before processing this request.\n\n"
                        "Please provide {{verification_method}}.\n\n"
                        "Once we have verified your identity, we will proceed with your request. "
                        "The response deadline will be calculated from the date we complete verification.\n\n"
                        "Best regards,\n{{sender_name}}\n{{sender_title}}"
                    ),
                    "required_variables": [
                        "requester_name", "request_type", "request_id",
                        "verification_method", "sender_name", "sender_title"
                    ],
                    "follow_up_actions": [
                        "Track verification status",
                        "Recalculate response deadline upon verification"
                    ]
                },
                "fulfillment": {
                    "description": "Fulfill a data subject request",
                    "subject": "Your Data {{request_type}} Request - Completed - Reference {{request_id}}",
                    "body": (
                        "Dear {{requester_name}},\n\n"
                        "We have completed processing your {{request_type}} request "
                        "(Reference: {{request_id}}) submitted on {{request_date}}.\n\n"
                        "{{fulfillment_details}}\n\n"
                        "If you have any questions or concerns about this response, "
                        "please contact {{contact_email}}.\n\n"
                        "You also have the right to lodge a complaint with {{supervisory_authority}} "
                        "if you believe your data protection rights have not been respected.\n\n"
                        "Best regards,\n{{sender_name}}\n{{sender_title}}"
                    ),
                    "required_variables": [
                        "requester_name", "request_type", "request_id",
                        "request_date", "fulfillment_details", "contact_email",
                        "supervisory_authority", "sender_name", "sender_title"
                    ],
                    "follow_up_actions": [
                        "Update DSR register with completion",
                        "File response record",
                        "Close request"
                    ]
                }
            },
            "discovery_hold": {
                "initial_notice": {
                    "description": "Initial litigation hold notice to custodians",
                    "subject": "LEGAL HOLD NOTICE - {{matter_name}} - Action Required",
                    "body": (
                        "PRIVILEGED AND CONFIDENTIAL\n"
                        "ATTORNEY-CLIENT COMMUNICATION\n\n"
                        "Dear {{custodian_name}},\n\n"
                        "You are receiving this notice because you may possess documents, communications, "
                        "or data relevant to the matter referenced above.\n\n"
                        "PRESERVATION OBLIGATION:\n"
                        "Effective immediately, you must preserve all documents and electronically stored "
                        "information (ESI) related to:\n"
                        "- Subject matter: {{hold_scope}}\n"
                        "- Date range: {{start_date}} to present\n"
                        "- Document types: {{document_types}}\n\n"
                        "DO NOT delete, destroy, modify, or discard any potentially relevant materials.\n\n"
                        "This includes but is not limited to: emails, text messages, instant messages, "
                        "documents, spreadsheets, presentations, notes, calendars, voicemails, "
                        "and any other electronically stored information.\n\n"
                        "Please acknowledge receipt of this notice by {{acknowledgment_deadline}}.\n\n"
                        "Contact {{legal_contact}} with any questions.\n\n"
                        "{{sender_name}}\n{{sender_title}}"
                    ),
                    "required_variables": [
                        "matter_name", "custodian_name", "hold_scope",
                        "start_date", "document_types", "acknowledgment_deadline",
                        "legal_contact", "sender_name", "sender_title"
                    ],
                    "follow_up_actions": [
                        "Track acknowledgment receipt",
                        "Follow up with non-responsive custodians",
                        "Log hold in matter management system",
                        "Schedule periodic hold reminders"
                    ]
                },
                "reminder": {
                    "description": "Periodic hold reminder / reaffirmation",
                    "subject": "LEGAL HOLD REMINDER - {{matter_name}} - Reaffirmation Required",
                    "body": (
                        "PRIVILEGED AND CONFIDENTIAL\n\n"
                        "Dear {{custodian_name}},\n\n"
                        "This is a reminder that the legal hold for {{matter_name}} remains in effect.\n\n"
                        "You continue to be obligated to preserve all documents and ESI related to:\n"
                        "- {{hold_scope}}\n\n"
                        "Please reaffirm your compliance by {{reaffirmation_deadline}}.\n\n"
                        "Contact {{legal_contact}} with any questions.\n\n"
                        "{{sender_name}}"
                    ),
                    "required_variables": [
                        "matter_name", "custodian_name", "hold_scope",
                        "reaffirmation_deadline", "legal_contact", "sender_name"
                    ],
                    "follow_up_actions": [
                        "Track reaffirmation",
                        "Escalate non-responses"
                    ]
                },
                "release": {
                    "description": "Release litigation hold",
                    "subject": "LEGAL HOLD RELEASED - {{matter_name}}",
                    "body": (
                        "Dear {{custodian_name}},\n\n"
                        "The legal hold for {{matter_name}} has been released effective {{release_date}}.\n\n"
                        "You are no longer required to preserve documents related to this matter "
                        "beyond your normal retention obligations.\n\n"
                        "Please resume normal document retention practices for these materials.\n\n"
                        "Contact {{legal_contact}} with any questions.\n\n"
                        "{{sender_name}}"
                    ),
                    "required_variables": [
                        "matter_name", "custodian_name", "release_date",
                        "legal_contact", "sender_name"
                    ],
                    "follow_up_actions": [
                        "Update hold status in system",
                        "Document release decision",
                        "Notify IT/records team"
                    ]
                }
            },
            "nda_request": {
                "send_standard_form": {
                    "description": "Send organization's standard form NDA",
                    "subject": "Non-Disclosure Agreement - {{company_name}} and {{counterparty_name}}",
                    "body": (
                        "Dear {{contact_name}},\n\n"
                        "Thank you for your interest in discussing {{purpose}} with {{company_name}}.\n\n"
                        "Please find attached our standard mutual non-disclosure agreement for your review. "
                        "Key terms include:\n"
                        "- Type: Mutual NDA\n"
                        "- Term: {{term_years}} years\n"
                        "- Confidentiality survival: {{survival_years}} years\n"
                        "- Governing law: {{governing_law}}\n\n"
                        "Please review, sign, and return at your earliest convenience. "
                        "If you have any questions or require modifications, please let us know.\n\n"
                        "Best regards,\n{{sender_name}}\n{{sender_title}}"
                    ),
                    "required_variables": [
                        "contact_name", "counterparty_name", "company_name",
                        "purpose", "term_years", "survival_years",
                        "governing_law", "sender_name", "sender_title"
                    ],
                    "follow_up_actions": [
                        "Track execution status",
                        "Set reminder for follow-up if unsigned after 5 business days"
                    ]
                }
            },
            "privacy_inquiry": {
                "general_response": {
                    "description": "General response to privacy inquiry",
                    "subject": "RE: Privacy Inquiry - {{inquiry_topic}}",
                    "body": (
                        "Dear {{requester_name}},\n\n"
                        "Thank you for your inquiry regarding {{inquiry_topic}}.\n\n"
                        "{{response_details}}\n\n"
                        "For more information, please refer to our Privacy Notice at {{privacy_notice_url}}.\n\n"
                        "If you have additional questions, please contact our privacy team at {{privacy_email}}.\n\n"
                        "Best regards,\n{{sender_name}}\n{{sender_title}}"
                    ),
                    "required_variables": [
                        "requester_name", "inquiry_topic", "response_details",
                        "privacy_notice_url", "privacy_email",
                        "sender_name", "sender_title"
                    ],
                    "follow_up_actions": [
                        "Log inquiry in tracking system",
                        "Update FAQ if inquiry is common"
                    ]
                }
            },
            "vendor_legal": {
                "contract_status": {
                    "description": "Response to vendor contract status inquiry",
                    "subject": "RE: {{agreement_name}} - Status Update",
                    "body": (
                        "Dear {{contact_name}},\n\n"
                        "Thank you for your inquiry regarding the status of {{agreement_name}}.\n\n"
                        "{{status_details}}\n\n"
                        "{{next_steps}}\n\n"
                        "Best regards,\n{{sender_name}}\n{{sender_title}}"
                    ),
                    "required_variables": [
                        "contact_name", "agreement_name", "status_details",
                        "next_steps", "sender_name", "sender_title"
                    ],
                    "follow_up_actions": [
                        "Update contract management system",
                        "Set follow-up reminder"
                    ]
                }
            },
            "subpoena": {
                "acknowledgment": {
                    "description": "Acknowledge receipt of subpoena/legal process",
                    "subject": "RE: {{case_reference}} - Acknowledgment of Receipt",
                    "body": (
                        "Dear {{sender_attorney}},\n\n"
                        "We acknowledge receipt of the {{process_type}} served on {{date_served}} "
                        "in connection with {{case_reference}}.\n\n"
                        "We are reviewing the request and will respond within the time permitted "
                        "by applicable rules.\n\n"
                        "{{additional_notes}}\n\n"
                        "Regards,\n{{sender_name}}\n{{sender_title}}"
                    ),
                    "required_variables": [
                        "sender_attorney", "process_type", "date_served",
                        "case_reference", "sender_name", "sender_title"
                    ],
                    "notes": "CRITICAL: Subpoena responses ALWAYS require counsel review. This template is a starting framework only.",
                    "follow_up_actions": [
                        "Engage outside counsel immediately",
                        "Implement preservation hold if not already in place",
                        "Identify potentially responsive documents",
                        "Review for privilege"
                    ]
                }
            },
            "insurance_notification": {
                "initial_claim": {
                    "description": "Initial insurance claim notification",
                    "subject": "Notice of Claim - Policy {{policy_number}} - {{matter_description}}",
                    "body": (
                        "Dear {{claims_contact}},\n\n"
                        "We are writing to provide notice of a potential claim under "
                        "Policy No. {{policy_number}} (coverage period: {{coverage_period}}).\n\n"
                        "MATTER DESCRIPTION:\n{{matter_description}}\n\n"
                        "TIMELINE OF EVENTS:\n{{timeline}}\n\n"
                        "We request confirmation of coverage and assignment of a claims adjuster.\n\n"
                        "Please direct all correspondence regarding this claim to {{legal_contact}}.\n\n"
                        "Regards,\n{{sender_name}}\n{{sender_title}}"
                    ),
                    "required_variables": [
                        "claims_contact", "policy_number", "coverage_period",
                        "matter_description", "timeline", "legal_contact",
                        "sender_name", "sender_title"
                    ],
                    "follow_up_actions": [
                        "Confirm receipt with insurer",
                        "Track claim number",
                        "Calendar follow-up dates",
                        "Compile supporting documentation"
                    ]
                }
            }
        }


def main():
    """Main entry point for the Canned Responses STF."""
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

        generator = CannedResponseGenerator(apiClient)

        if operation == "generate_response":
            validateRequiredFields(userInput, ["category", "sub_category", "variables"])
            result = generator.generateResponse(
                category=userInput["category"],
                subCategory=userInput["sub_category"],
                variables=userInput["variables"],
                tone=userInput.get("tone", "professional")
            )

        elif operation == "check_escalation":
            validateRequiredFields(userInput, ["category", "triggers"])
            result = generator.checkEscalation(
                category=userInput["category"],
                triggers=userInput["triggers"]
            )

        elif operation == "list_templates":
            result = generator.listTemplates(
                category=userInput.get("category")
            )

        elif operation == "create_template":
            validateRequiredFields(userInput, ["template_data"])
            result = generator.createTemplate(
                templateData=userInput["template_data"]
            )

        elif operation == "customize_response":
            validateRequiredFields(userInput, ["response_body", "customizations"])
            result = generator.customizeResponse(
                responseBody=userInput["response_body"],
                customizations=userInput["customizations"]
            )

        elif operation == "describe":
            result = generator.describe()

        else:
            raise ValueError(
                f"Unknown operation: {operation}. "
                f"Valid operations: generate_response, check_escalation, "
                f"list_templates, create_template, customize_response, describe"
            )

        writeOutput({
            "status": "success",
            "operation": operation,
            "data": result
        })

    except ValueError as e:
        logger.error(f"Validation error in CannedResponseGenerator: {str(e)}")
        writeError(e, "ValidationError")
    except Exception as e:
        logger.error(f"Unexpected error in CannedResponseGenerator: {str(e)}", exc_info=True)
        writeError(e)


if __name__ == "__main__":
    main()
