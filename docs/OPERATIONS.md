# D6E Legal STF - Operations Reference

All operations across all 6 Legal STFs. Every operation works without database access.

## stf-nda-triage

### triage_nda

Full NDA triage evaluation with GREEN/YELLOW/RED classification.

**Input:**
```json
{
  "operation": "triage_nda",
  "nda_data": {
    "nda_type": "mutual",
    "counterparty": "Acme Corp",
    "confidential_info_scope": "reasonable",
    "carveouts_present": ["public_knowledge", "prior_possession", "independent_development", "third_party_receipt", "legal_compulsion"],
    "permitted_disclosures": ["employees", "contractors_advisors", "legal_regulatory"],
    "term_years": 2,
    "survival_years": 3,
    "governing_law": "Delaware",
    "jurisdiction_acceptable": true,
    "has_mandatory_arbitration": false,
    "problematic_provisions": [],
    "return_destruction": {
      "has_obligation": true,
      "has_retention_exception": true,
      "requires_sworn_affidavit": false
    }
  }
}
```

### check_clause

Check a specific NDA clause.

**Input:**
```json
{
  "operation": "check_clause",
  "clause_type": "carveouts",
  "clause_data": {
    "carveouts_present": ["public_knowledge", "prior_possession"]
  }
}
```

### get_routing_recommendation

Get routing based on classification.

**Input:**
```json
{
  "operation": "get_routing_recommendation",
  "classification": "YELLOW"
}
```

### generate_checklist

Generate blank NDA screening checklist.

**Input:**
```json
{
  "operation": "generate_checklist",
  "nda_type": "mutual"
}
```

---

## stf-contract-review

### review_contract

Full contract review against playbook.

**Input:**
```json
{
  "operation": "review_contract",
  "contract_data": {
    "contract_type": "SaaS",
    "our_side": "customer",
    "counterparty": "Vendor Corp",
    "clauses": {
      "limitation_of_liability": {
        "cap_type": "fixed",
        "cap_months_of_fees": 12,
        "is_mutual": true,
        "has_consequential_exclusion": true
      },
      "data_protection": {
        "processes_personal_data": true,
        "has_dpa": true,
        "breach_notification_hours": 48,
        "has_subprocessor_notification": true,
        "has_deletion_provision": true
      }
    }
  }
}
```

### analyze_clause

Analyze a specific clause type.

**Input:**
```json
{
  "operation": "analyze_clause",
  "clause_type": "limitation_of_liability",
  "clause_details": {
    "cap_type": "uncapped"
  },
  "our_side": "customer"
}
```

### generate_redline

Generate redline suggestion.

**Input:**
```json
{
  "operation": "generate_redline",
  "clause_type": "limitation_of_liability",
  "current_language": "Vendor's liability shall be unlimited.",
  "issue_description": "uncapped_liability",
  "priority": "must_have"
}
```

### classify_deviation

Classify deviation severity.

**Input:**
```json
{
  "operation": "classify_deviation",
  "clause_type": "data_protection",
  "deviation_type": "no_dpa_with_personal_data"
}
```

---

## stf-legal-risk-assessment

### assess_risk

Full risk assessment.

**Input:**
```json
{
  "operation": "assess_risk",
  "risk_data": {
    "description": "Vendor processing EU personal data without adequate transfer mechanism",
    "category": "Data Privacy",
    "severity": 4,
    "likelihood": 3,
    "contributing_factors": ["No SCCs in place", "Data transfers to US"],
    "mitigating_factors": ["Vendor has SOC 2 certification"],
    "financial_exposure": "$500,000"
  }
}
```

### calculate_risk_score

Calculate risk score from severity and likelihood.

**Input:**
```json
{
  "operation": "calculate_risk_score",
  "severity": 4,
  "likelihood": 3
}
```

### generate_risk_matrix

Generate full risk matrix visualization.

**Input:**
```json
{
  "operation": "generate_risk_matrix"
}
```

---

## stf-compliance

### review_dpa

Review DPA against compliance checklist.

**Input:**
```json
{
  "operation": "review_dpa",
  "dpa_data": {
    "counterparty": "Cloud Provider Inc",
    "required_elements": {
      "subject_matter_and_duration": true,
      "nature_and_purpose": true,
      "type_of_personal_data": true,
      "categories_of_data_subjects": true,
      "controller_obligations_and_rights": true
    },
    "processor_obligations": {
      "process_on_instructions_only": true,
      "confidentiality_commitment": true,
      "security_measures": true,
      "sub_processor_requirements": true,
      "data_subject_rights_assistance": true,
      "security_breach_assistance": true,
      "deletion_or_return_on_termination": false,
      "audit_rights": true,
      "breach_notification": true
    },
    "breach_notification_hours": 48,
    "sub_processor_authorization": "general_with_notice"
  }
}
```

### process_dsr

Process data subject request.

**Input:**
```json
{
  "operation": "process_dsr",
  "dsr_data": {
    "request_type": "erasure",
    "regulation": "GDPR",
    "requester_name": "Jane Doe",
    "date_received": "2025-01-15",
    "identity_verified": true,
    "subject_to_litigation_hold": false,
    "special_category_data": false
  }
}
```

### get_regulation_overview

Get overview of a privacy regulation.

**Input:**
```json
{
  "operation": "get_regulation_overview",
  "regulation": "GDPR"
}
```

---

## stf-canned-responses

### generate_response

Generate templated response.

**Input:**
```json
{
  "operation": "generate_response",
  "category": "dsr",
  "sub_category": "acknowledgment",
  "variables": {
    "requester_name": "John Doe",
    "request_date": "2025-01-15",
    "request_type": "access",
    "regulation": "GDPR",
    "response_deadline": "2025-02-14",
    "request_id": "DSR-2025-001",
    "contact_email": "privacy@company.com",
    "sender_name": "Privacy Team",
    "sender_title": "Data Protection Officer"
  }
}
```

### check_escalation

Check escalation triggers.

**Input:**
```json
{
  "operation": "check_escalation",
  "category": "dsr",
  "triggers": ["involves_minor", "special_category_data"]
}
```

### list_templates

List available templates.

**Input:**
```json
{
  "operation": "list_templates"
}
```

---

## stf-meeting-briefing

### generate_briefing

Generate meeting briefing.

**Input:**
```json
{
  "operation": "generate_briefing",
  "meeting_data": {
    "meeting_title": "Vendor Contract Negotiation - Acme Corp",
    "meeting_type": "deal_review",
    "date_time": "2025-02-01T14:00:00-05:00",
    "duration": "60 minutes",
    "location": "Conference Room A / Zoom",
    "your_role": "negotiator",
    "participants": [
      {"name": "John Smith", "organization": "Our Company", "role": "Legal Counsel", "key_interests": "Liability cap, data protection"},
      {"name": "Jane Doe", "organization": "Acme Corp", "role": "VP Legal", "key_interests": "Quick execution, broad indemnification"}
    ],
    "agenda": ["Review open contract issues", "Discuss liability cap", "Data protection terms"],
    "talking_points": ["Liability cap must be at least 12 months of fees", "DPA required before processing begins"],
    "red_lines": ["No uncapped liability", "Must include DPA"]
  }
}
```

### get_meeting_prep_checklist

Get preparation checklist.

**Input:**
```json
{
  "operation": "get_meeting_prep_checklist",
  "meeting_type": "deal_review"
}
```

### create_action_items

Create action items from meeting.

**Input:**
```json
{
  "operation": "create_action_items",
  "action_data": {
    "meeting_title": "Vendor Contract Negotiation",
    "meeting_date": "2025-02-01",
    "items": [
      {"description": "Send redline of Section 4.2", "owner": "John Smith", "deadline": "2025-02-03", "priority": "High", "type": "legal_team"},
      {"description": "Review DPA template", "owner": "Jane Doe", "deadline": "2025-02-05", "priority": "Medium", "type": "external"}
    ]
  }
}
```
