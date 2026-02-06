# D6E Legal STF Suite

Docker-based State Transition Functions (STFs) for legal workflows on the D6E platform.

## Overview

This repository contains 6 Docker STFs implementing legal workflows based on the [Anthropic Knowledge Work Plugins - Legal](https://github.com/anthropics/knowledge-work-plugins/tree/main/legal):

| STF | Description | Key Operations |
| --- | --- | --- |
| **stf-nda-triage** | Screen and classify incoming NDAs | Triage, clause check, routing, checklist |
| **stf-contract-review** | Review contracts against playbook | Full review, clause analysis, redlines, deviation classification |
| **stf-legal-risk-assessment** | Assess legal risks with framework | Risk scoring, memo, register, escalation, matrix |
| **stf-compliance** | Privacy regulation compliance | DPA review, DSR processing, timelines, regulation overview |
| **stf-canned-responses** | Template response management | Response generation, escalation check, template management |
| **stf-meeting-briefing** | Meeting preparation and tracking | Briefings, action items, checklists, follow-ups |

## Quick Start

### 1. Build All Images

```bash
./scripts/build-all.sh
```

Or build individually:

```bash
cp -r shared stf-nda-triage/shared
cd stf-nda-triage
docker build -t stf-nda-triage:latest .
```

### 2. Test an STF

```bash
echo '{
  "workspace_id": "test-ws",
  "stf_id": "test-stf",
  "caller": null,
  "api_url": "http://localhost:8080",
  "api_token": "test-token",
  "input": {
    "operation": "generate_checklist",
    "nda_type": "mutual"
  },
  "sources": {}
}' | docker run --rm -i stf-nda-triage:latest
```

## Project Structure

```
d6e-docker-stf-legal/
├── docs/
│   └── OPERATIONS.md               # Full operations reference
├── shared/
│   └── utils.py                     # Shared utilities for all STFs
├── stf-nda-triage/                  # NDA screening and classification
├── stf-contract-review/             # Contract review against playbook
├── stf-legal-risk-assessment/       # Risk assessment framework
├── stf-compliance/                  # Privacy compliance operations
├── stf-canned-responses/            # Template response management
├── stf-meeting-briefing/            # Meeting prep and action tracking
├── scripts/
│   └── build-all.sh                 # Build all Docker images
└── README.md
```

## STF Input/Output Format

### Input (via stdin)

```json
{
  "workspace_id": "UUID",
  "stf_id": "UUID",
  "caller": "UUID | null",
  "api_url": "http://api:8080",
  "api_token": "internal_token",
  "input": {
    "operation": "operation_name",
    ...parameters
  },
  "sources": {
    "previous_step": { "output": {...} }
  }
}
```

### Output (via stdout)

**Success:**

```json
{
  "output": {
    "status": "success",
    "operation": "operation_name",
    "data": {...}
  }
}
```

**Error:**

```json
{
  "error": "Error message",
  "type": "ErrorType"
}
```

## Operations Summary

### stf-nda-triage

| Operation | Required Params | Description |
| --- | --- | --- |
| `triage_nda` | `nda_data` | Full NDA triage with classification |
| `check_clause` | `clause_type`, `clause_data` | Check specific clause |
| `get_routing_recommendation` | `classification` | Get routing for classification |
| `generate_checklist` | - | Generate screening checklist |

### stf-contract-review

| Operation | Required Params | Description |
| --- | --- | --- |
| `review_contract` | `contract_data` | Full contract review |
| `analyze_clause` | `clause_type`, `clause_details` | Analyze specific clause |
| `generate_redline` | `clause_type`, `current_language`, `issue_description` | Generate redline suggestion |
| `classify_deviation` | `clause_type`, `deviation_type` | Classify deviation severity |
| `generate_review_summary` | `deviations`, `contract_data` | Generate review summary |

### stf-legal-risk-assessment

| Operation | Required Params | Description |
| --- | --- | --- |
| `assess_risk` | `risk_data` | Full risk assessment |
| `calculate_risk_score` | `severity`, `likelihood` | Calculate risk score |
| `generate_risk_memo` | `assessment_data` | Generate risk memo |
| `create_risk_register_entry` | `risk_data` | Create register entry |
| `get_escalation_recommendation` | `risk_level` | Get escalation guidance |
| `generate_risk_matrix` | - | Generate risk matrix |

### stf-compliance

| Operation | Required Params | Description |
| --- | --- | --- |
| `review_dpa` | `dpa_data` | Review DPA against checklist |
| `process_dsr` | `dsr_data` | Process data subject request |
| `get_response_timeline` | `regulation`, `date_received` | Get response timeline |
| `check_exemptions` | `dsr_data` | Check DSR exemptions |
| `generate_dpa_checklist` | - | Generate DPA checklist |
| `get_regulation_overview` | `regulation` | Get regulation overview |

### stf-canned-responses

| Operation | Required Params | Description |
| --- | --- | --- |
| `generate_response` | `category`, `sub_category`, `variables` | Generate response |
| `check_escalation` | `category`, `triggers` | Check escalation triggers |
| `list_templates` | - | List available templates |
| `create_template` | `template_data` | Create new template |
| `customize_response` | `response_body`, `customizations` | Customize response |

### stf-meeting-briefing

| Operation | Required Params | Description |
| --- | --- | --- |
| `generate_briefing` | `meeting_data` | Generate meeting briefing |
| `create_action_items` | `action_data` | Create action items |
| `get_meeting_prep_checklist` | `meeting_type` | Get prep checklist |
| `track_action_items` | `tracking_data` | Update action items |
| `generate_follow_up` | `follow_up_data` | Generate follow-up |

## Key Design Decisions

### All Operations are Database-Free

Unlike the finance STF suite, all legal operations work without database access. This is because:
- Legal analysis is primarily rule-based evaluation against standard criteria
- Templates and frameworks are embedded in the STF code
- Input data (contract terms, NDA clauses, etc.) is provided directly in the request

Database access (via D6E SQL API) is available for future operations that may need to store/retrieve:
- Risk register entries
- Template libraries
- Action item tracking
- Audit trails

### Rule-Based Analysis

The STFs implement structured frameworks from the legal skills:
- NDA screening uses a checklist-based evaluation against standard criteria
- Contract review applies playbook positions to classify deviations
- Risk assessment uses the severity × likelihood matrix (1-25 score)
- Compliance checks DPA elements against GDPR Article 28 requirements

### Classification Systems

| STF | System | Levels |
| --- | --- | --- |
| NDA Triage | Traffic light | GREEN (approve), YELLOW (review), RED (reject/negotiate) |
| Contract Review | Deviation severity | GREEN (acceptable), YELLOW (negotiate), RED (escalate) |
| Risk Assessment | Risk matrix | GREEN (1-4), YELLOW (5-9), ORANGE (10-15), RED (16-25) |
| Compliance | Compliance status | Compliant, Needs Attention, Non-Compliant |
| Canned Responses | Escalation check | Proceed / Escalate |

## Development

### Adding a New STF

1. Create directory: `stf-new-function/`
2. Copy structure from existing STF
3. Implement `main.py` with operation handlers
4. Create `Dockerfile`, `requirements.txt`, `README.md`
5. Add to `scripts/build-all.sh`
6. Add to `.github/workflows/docker-publish.yml`

### Testing Locally

```bash
# Build
docker build -t my-stf:latest .

# Test with sample input
cat test-input.json | docker run --rm -i my-stf:latest

# Debug mode
docker run --rm -it --entrypoint /bin/bash my-stf:latest
```

## References

- [D6E Platform Documentation](https://docs.d6e.ai)
- [Anthropic Knowledge Work Plugins - Legal](https://github.com/anthropics/knowledge-work-plugins/tree/main/legal)
- [D6E Finance STF Suite](https://github.com/d6e-ai/d6e-docker-stf-finance)
