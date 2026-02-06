#!/usr/bin/env python3
"""
D6E Docker STF: Meeting Briefing

Overview:
  Prepares structured briefings for meetings with legal relevance
  and tracks resulting action items.

Main Operations:
  - generate_briefing: Generate structured meeting briefing
  - create_action_items: Create action items from meeting outcomes
  - get_meeting_prep_checklist: Get preparation checklist by meeting type
  - track_action_items: Update and track action item status
  - generate_follow_up: Generate post-meeting follow-up summary

Limitations:
  - Provides legal workflow assistance, not legal advice
  - Briefings should be reviewed for accuracy before use
  - Context from connected sources must be provided in input
"""

import sys
import os
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from utils import (
    logger, readInput, writeOutput, writeError,
    createApiClient, validateRequiredFields,
    generateId, getCurrentTimestamp
)


# Meeting types and their prep needs
MEETING_TYPES = {
    "deal_review": {
        "label": "Deal Review",
        "key_prep": [
            "Contract status and open issues",
            "Counterparty history",
            "Negotiation strategy",
            "Approval requirements",
            "Comparable deals"
        ]
    },
    "board_committee": {
        "label": "Board / Committee Meeting",
        "key_prep": [
            "Legal department update",
            "Risk register highlights",
            "Pending matters",
            "Regulatory developments",
            "Resolution drafts"
        ]
    },
    "vendor_call": {
        "label": "Vendor Call",
        "key_prep": [
            "Agreement status",
            "Open issues",
            "Performance metrics",
            "Relationship history",
            "Negotiation objectives"
        ]
    },
    "team_sync": {
        "label": "Team Sync",
        "key_prep": [
            "Workload status",
            "Priority matters",
            "Resource needs",
            "Upcoming deadlines"
        ]
    },
    "client_customer": {
        "label": "Client / Customer Meeting",
        "key_prep": [
            "Agreement terms",
            "Support history",
            "Open issues",
            "Relationship context"
        ]
    },
    "regulatory": {
        "label": "Regulatory / Government Meeting",
        "key_prep": [
            "Matter background",
            "Compliance status",
            "Prior communications",
            "Counsel briefing",
            "Privilege considerations"
        ]
    },
    "litigation": {
        "label": "Litigation / Dispute",
        "key_prep": [
            "Case status",
            "Recent developments",
            "Strategy",
            "Settlement parameters"
        ]
    },
    "cross_functional": {
        "label": "Cross-Functional Meeting",
        "key_prep": [
            "Legal implications of decisions",
            "Risk assessment",
            "Compliance requirements"
        ]
    }
}

# Action item priorities
ACTION_PRIORITIES = ["High", "Medium", "Low"]
ACTION_STATUSES = ["Open", "In Progress", "Completed", "Overdue", "Cancelled"]
ACTION_TYPES = ["legal_team", "business_team", "external", "follow_up_meeting"]


class MeetingBriefingGenerator:
    """
    Generates meeting briefings and manages action items.
    """

    def __init__(self, apiClient=None):
        """
        Initialize briefing generator.

        Args:
            apiClient: Optional D6eApiClient for database operations
        """
        self.api = apiClient

    def generateBriefing(self, meetingData: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a structured meeting briefing.

        Args:
            meetingData: Meeting details including:
                - meeting_title: Title of the meeting
                - meeting_type: Type (deal_review, board_committee, etc.)
                - date_time: Date and time with timezone
                - duration: Expected duration
                - location: Physical location or video link
                - your_role: Role in meeting (advisor, presenter, negotiator, observer)
                - participants: List of participant objects
                - agenda: List of agenda items
                - background: Background context text
                - open_issues: List of open issues
                - key_documents: List of relevant documents
                - legal_considerations: Legal issues relevant to meeting
                - talking_points: Suggested talking points
                - questions_to_raise: Questions to ask
                - decisions_needed: Decisions requiring resolution
                - red_lines: Non-negotiable positions (for negotiation meetings)
                - prior_meeting_followup: Outstanding items from prior meetings

        Returns:
            Structured briefing document
        """
        logger.info(f"Generating briefing for: {meetingData.get('meeting_title', 'unknown')}")

        meetingType = meetingData.get("meeting_type", "general")
        typeInfo = MEETING_TYPES.get(meetingType, {"label": "General Meeting", "key_prep": []})

        # Build briefing structure
        briefing = {
            "briefing_id": generateId(),
            "generated_at": getCurrentTimestamp(),
            "meeting_details": {
                "title": meetingData.get("meeting_title", "Untitled Meeting"),
                "type": meetingType,
                "type_label": typeInfo["label"],
                "date_time": meetingData.get("date_time", "TBD"),
                "duration": meetingData.get("duration", "TBD"),
                "location": meetingData.get("location", "TBD"),
                "your_role": meetingData.get("your_role", "advisor")
            },
            "participants": self._formatParticipants(meetingData.get("participants", [])),
            "agenda": self._formatAgenda(meetingData.get("agenda", [])),
            "background_and_context": meetingData.get("background", ""),
            "key_documents": meetingData.get("key_documents", []),
            "open_issues": self._formatOpenIssues(meetingData.get("open_issues", [])),
            "legal_considerations": meetingData.get("legal_considerations", ""),
            "talking_points": meetingData.get("talking_points", []),
            "questions_to_raise": meetingData.get("questions_to_raise", []),
            "decisions_needed": meetingData.get("decisions_needed", []),
            "red_lines": meetingData.get("red_lines", []),
            "prior_meeting_followup": meetingData.get("prior_meeting_followup", []),
            "preparation_gaps": meetingData.get("preparation_gaps", []),
            "prep_checklist": typeInfo["key_prep"]
        }

        # Add type-specific sections
        if meetingType == "deal_review":
            briefing["deal_specific"] = self._buildDealSection(meetingData)
        elif meetingType == "board_committee":
            briefing["board_specific"] = self._buildBoardSection(meetingData)
        elif meetingType == "regulatory":
            briefing["regulatory_specific"] = self._buildRegulatorySection(meetingData)

        # Generate text format
        briefing["text_format"] = self._generateTextBriefing(briefing)

        return briefing

    def createActionItems(self, actionData: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create action items from meeting outcomes.

        Args:
            actionData: Action items data including:
                - meeting_title: Meeting these items came from
                - meeting_date: Date of the meeting
                - items: List of action item objects with:
                    - description: What needs to be done
                    - owner: Person responsible
                    - deadline: Due date (YYYY-MM-DD)
                    - priority: High, Medium, Low
                    - type: legal_team, business_team, external, follow_up_meeting
                    - dependencies: Optional dependencies
                    - notes: Optional notes

        Returns:
            Created action items with IDs and tracking info
        """
        logger.info(f"Creating action items for: {actionData.get('meeting_title', 'unknown')}")

        items = actionData.get("items", [])
        createdItems = []

        for item in items:
            priority = item.get("priority", "Medium")
            if priority not in ACTION_PRIORITIES:
                priority = "Medium"

            actionType = item.get("type", "legal_team")
            if actionType not in ACTION_TYPES:
                actionType = "legal_team"

            createdItem = {
                "action_id": generateId(),
                "description": item.get("description", ""),
                "owner": item.get("owner", "Unassigned"),
                "deadline": item.get("deadline", "TBD"),
                "priority": priority,
                "type": actionType,
                "type_label": actionType.replace("_", " ").title(),
                "status": "Open",
                "dependencies": item.get("dependencies", []),
                "notes": item.get("notes", ""),
                "created_at": getCurrentTimestamp(),
                "meeting_reference": actionData.get("meeting_title", "")
            }
            createdItems.append(createdItem)

        # Sort by priority
        priorityOrder = {"High": 0, "Medium": 1, "Low": 2}
        createdItems.sort(key=lambda x: priorityOrder.get(x["priority"], 1))

        # Summary statistics
        summary = {
            "total_items": len(createdItems),
            "by_priority": {
                "high": len([i for i in createdItems if i["priority"] == "High"]),
                "medium": len([i for i in createdItems if i["priority"] == "Medium"]),
                "low": len([i for i in createdItems if i["priority"] == "Low"])
            },
            "by_type": {
                t: len([i for i in createdItems if i["type"] == t])
                for t in ACTION_TYPES
            },
            "owners": list(set(i["owner"] for i in createdItems if i["owner"] != "Unassigned"))
        }

        return {
            "meeting_title": actionData.get("meeting_title", ""),
            "meeting_date": actionData.get("meeting_date", ""),
            "items": createdItems,
            "summary": summary,
            "text_format": self._formatActionItemsText(
                actionData.get("meeting_title", ""),
                actionData.get("meeting_date", ""),
                createdItems
            )
        }

    def getMeetingPrepChecklist(self, meetingType: str) -> Dict[str, Any]:
        """
        Get preparation checklist by meeting type.

        Args:
            meetingType: Type of meeting

        Returns:
            Preparation checklist with items
        """
        if meetingType not in MEETING_TYPES:
            raise ValueError(
                f"Unknown meeting type: {meetingType}. "
                f"Valid types: {', '.join(MEETING_TYPES.keys())}"
            )

        typeInfo = MEETING_TYPES[meetingType]

        checklist = {
            "meeting_type": meetingType,
            "type_label": typeInfo["label"],
            "prep_items": [
                {"item": prep, "status": "pending"}
                for prep in typeInfo["key_prep"]
            ],
            "general_prep": [
                {"item": "Review meeting agenda", "status": "pending"},
                {"item": "Identify key participants and their interests", "status": "pending"},
                {"item": "Gather relevant documents", "status": "pending"},
                {"item": "Prepare talking points", "status": "pending"},
                {"item": "List questions to raise", "status": "pending"},
                {"item": "Review prior meeting notes and action items", "status": "pending"},
                {"item": "Identify decisions needed", "status": "pending"}
            ]
        }

        return checklist

    def trackActionItems(self, trackingData: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update and track action item status.

        Args:
            trackingData: Tracking updates including:
                - items: List of items with action_id and new_status
                - notes: Optional notes on updates

        Returns:
            Updated action items
        """
        logger.info("Tracking action item updates")

        updates = trackingData.get("items", [])
        results = []

        for update in updates:
            actionId = update.get("action_id")
            newStatus = update.get("new_status", "Open")

            if newStatus not in ACTION_STATUSES:
                raise ValueError(
                    f"Invalid status: {newStatus}. "
                    f"Valid statuses: {', '.join(ACTION_STATUSES)}"
                )

            results.append({
                "action_id": actionId,
                "new_status": newStatus,
                "updated_at": getCurrentTimestamp(),
                "updated_by": update.get("updated_by", "system"),
                "notes": update.get("notes", "")
            })

        return {
            "updates": results,
            "update_count": len(results),
            "timestamp": getCurrentTimestamp()
        }

    def generateFollowUp(self, followUpData: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate post-meeting follow-up summary.

        Args:
            followUpData: Follow-up data including:
                - meeting_title: Title of the meeting
                - meeting_date: Date of the meeting
                - attendees: List of attendees
                - key_decisions: List of decisions made
                - action_items: List of action items
                - next_meeting: Optional next meeting details
                - notes: Additional notes

        Returns:
            Structured follow-up document
        """
        logger.info(f"Generating follow-up for: {followUpData.get('meeting_title', 'unknown')}")

        followUp = {
            "follow_up_id": generateId(),
            "generated_at": getCurrentTimestamp(),
            "meeting_title": followUpData.get("meeting_title", ""),
            "meeting_date": followUpData.get("meeting_date", ""),
            "attendees": followUpData.get("attendees", []),
            "key_decisions": followUpData.get("key_decisions", []),
            "action_items": followUpData.get("action_items", []),
            "next_meeting": followUpData.get("next_meeting"),
            "notes": followUpData.get("notes", "")
        }

        followUp["text_format"] = self._generateFollowUpText(followUp)

        return followUp

    # --- Internal methods ---

    def _formatParticipants(self, participants: List[Dict]) -> List[Dict]:
        """Format participant list with structure."""
        formatted = []
        for p in participants:
            formatted.append({
                "name": p.get("name", "Unknown"),
                "organization": p.get("organization", ""),
                "role": p.get("role", ""),
                "key_interests": p.get("key_interests", ""),
                "notes": p.get("notes", "")
            })
        return formatted

    def _formatAgenda(self, agenda: List) -> List[Dict]:
        """Format agenda items."""
        formatted = []
        for i, item in enumerate(agenda, 1):
            if isinstance(item, str):
                formatted.append({"number": i, "topic": item, "context": ""})
            elif isinstance(item, dict):
                formatted.append({
                    "number": i,
                    "topic": item.get("topic", ""),
                    "context": item.get("context", ""),
                    "time_allocation": item.get("time_allocation", "")
                })
        return formatted

    def _formatOpenIssues(self, issues: List) -> List[Dict]:
        """Format open issues."""
        formatted = []
        for issue in issues:
            if isinstance(issue, str):
                formatted.append({
                    "issue": issue,
                    "status": "Open",
                    "owner": "TBD",
                    "priority": "Medium"
                })
            elif isinstance(issue, dict):
                formatted.append({
                    "issue": issue.get("issue", ""),
                    "status": issue.get("status", "Open"),
                    "owner": issue.get("owner", "TBD"),
                    "priority": issue.get("priority", "Medium"),
                    "notes": issue.get("notes", "")
                })
        return formatted

    def _buildDealSection(self, meetingData: Dict) -> Dict:
        """Build deal-review specific section."""
        return {
            "deal_summary": meetingData.get("deal_summary", ""),
            "deal_value": meetingData.get("deal_value", ""),
            "contract_status": meetingData.get("contract_status", ""),
            "outstanding_issues": meetingData.get("outstanding_issues", []),
            "approval_requirements": meetingData.get("approval_requirements", []),
            "counterparty_dynamics": meetingData.get("counterparty_dynamics", "")
        }

    def _buildBoardSection(self, meetingData: Dict) -> Dict:
        """Build board/committee specific section."""
        return {
            "legal_update": meetingData.get("legal_update", ""),
            "risk_highlights": meetingData.get("risk_highlights", []),
            "regulatory_update": meetingData.get("regulatory_update", ""),
            "pending_approvals": meetingData.get("pending_approvals", []),
            "litigation_summary": meetingData.get("litigation_summary", "")
        }

    def _buildRegulatorySection(self, meetingData: Dict) -> Dict:
        """Build regulatory meeting specific section."""
        return {
            "regulatory_body": meetingData.get("regulatory_body", ""),
            "matter_history": meetingData.get("matter_history", ""),
            "compliance_posture": meetingData.get("compliance_posture", ""),
            "counsel_coordination": meetingData.get("counsel_coordination", ""),
            "privilege_considerations": meetingData.get("privilege_considerations", "")
        }

    def _generateTextBriefing(self, briefing: Dict) -> str:
        """Generate text format of the briefing."""
        details = briefing["meeting_details"]
        lines = [
            "## Meeting Brief",
            "",
            f"**Meeting**: {details['title']}",
            f"**Date/Time**: {details['date_time']}",
            f"**Duration**: {details['duration']}",
            f"**Location**: {details['location']}",
            f"**Your Role**: {details['your_role']}",
            ""
        ]

        if briefing["participants"]:
            lines.append("### Participants")
            for p in briefing["participants"]:
                lines.append(f"- **{p['name']}** ({p.get('organization', '')}) - {p.get('role', '')} - Interests: {p.get('key_interests', 'N/A')}")
            lines.append("")

        if briefing["agenda"]:
            lines.append("### Agenda")
            for item in briefing["agenda"]:
                lines.append(f"{item['number']}. {item['topic']}" + (f" - {item['context']}" if item.get('context') else ""))
            lines.append("")

        if briefing["background_and_context"]:
            lines.append("### Background and Context")
            lines.append(briefing["background_and_context"])
            lines.append("")

        if briefing["talking_points"]:
            lines.append("### Talking Points")
            for tp in briefing["talking_points"]:
                lines.append(f"- {tp}")
            lines.append("")

        if briefing["decisions_needed"]:
            lines.append("### Decisions Needed")
            for d in briefing["decisions_needed"]:
                lines.append(f"- {d}")
            lines.append("")

        if briefing["red_lines"]:
            lines.append("### Red Lines / Non-Negotiables")
            for rl in briefing["red_lines"]:
                lines.append(f"- {rl}")
            lines.append("")

        return "\n".join(lines)

    def _formatActionItemsText(
        self,
        meetingTitle: str,
        meetingDate: str,
        items: List[Dict]
    ) -> str:
        """Format action items as text table."""
        lines = [
            f"## Action Items from {meetingTitle} - {meetingDate}",
            "",
            "| # | Action Item | Owner | Deadline | Priority | Status |",
            "|---|-------------|-------|----------|----------|--------|"
        ]

        for i, item in enumerate(items, 1):
            lines.append(
                f"| {i} | {item['description']} | {item['owner']} | "
                f"{item['deadline']} | {item['priority']} | {item['status']} |"
            )

        return "\n".join(lines)

    def _generateFollowUpText(self, followUp: Dict) -> str:
        """Generate follow-up text."""
        lines = [
            f"## Meeting Follow-Up: {followUp['meeting_title']}",
            f"**Date**: {followUp['meeting_date']}",
            f"**Attendees**: {', '.join(followUp.get('attendees', []))}",
            ""
        ]

        if followUp["key_decisions"]:
            lines.append("### Key Decisions")
            for d in followUp["key_decisions"]:
                lines.append(f"- {d}")
            lines.append("")

        if followUp["action_items"]:
            lines.append("### Action Items")
            for item in followUp["action_items"]:
                if isinstance(item, dict):
                    lines.append(f"- [{item.get('priority', 'M')}] {item.get('description', '')} (Owner: {item.get('owner', 'TBD')}, Due: {item.get('deadline', 'TBD')})")
                else:
                    lines.append(f"- {item}")
            lines.append("")

        if followUp.get("next_meeting"):
            lines.append(f"### Next Meeting: {followUp['next_meeting']}")

        return "\n".join(lines)


def main():
    """Main entry point for the Meeting Briefing STF."""
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

        generator = MeetingBriefingGenerator(apiClient)

        if operation == "generate_briefing":
            validateRequiredFields(userInput, ["meeting_data"])
            result = generator.generateBriefing(
                meetingData=userInput["meeting_data"]
            )

        elif operation == "create_action_items":
            validateRequiredFields(userInput, ["action_data"])
            result = generator.createActionItems(
                actionData=userInput["action_data"]
            )

        elif operation == "get_meeting_prep_checklist":
            validateRequiredFields(userInput, ["meeting_type"])
            result = generator.getMeetingPrepChecklist(
                meetingType=userInput["meeting_type"]
            )

        elif operation == "track_action_items":
            validateRequiredFields(userInput, ["tracking_data"])
            result = generator.trackActionItems(
                trackingData=userInput["tracking_data"]
            )

        elif operation == "generate_follow_up":
            validateRequiredFields(userInput, ["follow_up_data"])
            result = generator.generateFollowUp(
                followUpData=userInput["follow_up_data"]
            )

        else:
            raise ValueError(
                f"Unknown operation: {operation}. "
                f"Valid operations: generate_briefing, create_action_items, "
                f"get_meeting_prep_checklist, track_action_items, generate_follow_up"
            )

        writeOutput({
            "status": "success",
            "operation": operation,
            "data": result
        })

    except ValueError as e:
        logger.error(f"Validation error in MeetingBriefingGenerator: {str(e)}")
        writeError(e, "ValidationError")
    except Exception as e:
        logger.error(f"Unexpected error in MeetingBriefingGenerator: {str(e)}", exc_info=True)
        writeError(e)


if __name__ == "__main__":
    main()
