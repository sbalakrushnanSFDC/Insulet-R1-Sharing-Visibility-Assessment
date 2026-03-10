# Insulet R1 — Salesforce Sharing, Visibility & Access-Control Assessment

> **Org:** Insulet Corporation — DevInt2 Sandbox (Unlimited Edition)  
> **Org ID:** `00Dbb000006gUxVEAU` | **Instance:** `omnipod--devint2.sandbox.my.salesforce.com`  
> **Assessment Date:** March 9, 2026 | **API Version:** 66.0

A comprehensive, evidence-based assessment of **all** Salesforce sharing, visibility, and access-control mechanisms in the Insulet DevInt2 sandbox. Every finding is tied to a specific evidence source (live SOQL query, Tooling API result, or local metadata file) with an explicit confidence level.

---

## What This Repository Contains

```
.
├── README.md                          ← You are here — overview, how-to, quick findings
├── docs/
│   ├── SHARING_ACCESS_ASSESSMENT.md   ← Full 7-deliverable assessment report (53 KB)
│   ├── EXECUTION_PLAN.md              ← Phased execution plan used to drive the assessment
│   └── ORG_INVENTORY.md               ← Org metadata inventory snapshot (component counts, packages)
└── scripts/
    ├── field_reference_report.py      ← Reports which metadata types reference each custom field
    └── find_unreferenced_fields.py    ← Identifies custom fields not referenced in any metadata
```

---

## Assessment Deliverables (inside `docs/SHARING_ACCESS_ASSESSMENT.md`)

| # | Deliverable | Description |
|---|-------------|-------------|
| 1 | **Executive Summary** | Design philosophy, key drivers, top risks, priority recommendations |
| 2 | **Detailed Narrative Assessment** | Full mechanism analysis: OWD, territories, sharing rules, Apex sharing, implicit sharing, Experience Cloud |
| 3 | **Visual Models** | 5 Mermaid diagrams — role hierarchy, territory structure, access architecture, Apex sharing flow, persona map |
| 4 | **Object View by Persona Matrix** | Markdown table + CSV — which personas can do what on each object |
| 5 | **Persona View by Object/Records/Fields Matrix** | Markdown table + CSV — per-persona data access picture |
| 6 | **Sharing Mechanism Catalog** | All 27 sharing mechanisms found, with evidence source and confidence level |
| 7 | **Findings & Recommendations** | 15 findings prioritized Critical / High / Medium / Low with remediation guidance |

---

## Quick Reference: Key Findings

### CRITICAL

| # | Finding | Evidence |
|---|---------|----------|
| F-001 | `Odaseva_Service_User_Permissions` grants **ViewAll + ModifyAll + ManageUsers + AuthorApex** to a custom (non-profile) perm set — full system bypass | Live SOQL: `SELECT Name, PermissionsModifyAllData FROM PermissionSet WHERE PermissionsModifyAllData = true` |
| F-002 | 7 OrgSync staging objects (`OrgSync_Patient_Staging__c`, `OrgSync_Physician_Staging__c`, `OrgSync_ASPN_Staging__c`, `OrgSync_Consent_Staging__c`, `OrgSync_Mule_Errors__c`, `Clinic_Grouping__c`) have **Internal OWD = Public Read/Write** — all 200+ internal users can see patient/consent data | EntityDefinition Tooling API |

### HIGH

| # | Finding | Evidence |
|---|---------|----------|
| F-003 | `enableSecureGuestAccess = false` — Trainer Portal guest user not restricted | `Sharing.settings-meta.xml` |
| F-004 | `Development_Support_Core_Access` and `Functional_Analyst_Core_Access` grant **ViewAllData=true** to ~14 business users | Live SOQL: PermissionSet bypass query |
| F-005 | `CTI_Integration_Access` and `Query_AllFiles` grant **ViewAllData=true** to integration roles | Live SOQL |
| F-006 | 177 System Administrator users in sandbox — production admin count needs review | User census SOQL |

### Summary Metrics

| Metric | Value | Evidence |
|--------|-------|----------|
| Total active users | 200+ (limited query) | User SOQL |
| Admin-profile users (sandbox) | 177 | User SOQL |
| External Trainer community users | 68 | User SOQL |
| Rule-based Account share records | **677,313** | AccountShare aggregate |
| Territory-based Account shares | 1,876 | AccountShare aggregate |
| Manual Account shares | 68 | AccountShare aggregate |
| Permission sets with ViewAllData | 9 | PermissionSet SOQL |
| Permission sets with ModifyAllData | 2 (Odaseva + Admin profile) | PermissionSet SOQL |
| Sharing mechanisms identified | 27 | Catalog (Deliverable 6) |
| Findings raised | 15 (2 Critical, 4 High, 5 Medium, 4 Low) | Assessment |

---

## Org Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                    INSULET DEVINT2 SANDBOX                       │
│                  Unlimited Edition │ USA870S                     │
├─────────────────────────────────────────────────────────────────┤
│  OWD BASELINE                                                    │
│  Account / Contact / Opportunity / Lead / Case = PRIVATE        │
│  OrgSync staging objects = PUBLIC READ/WRITE  ← RISK            │
├─────────────────────────────────────────────────────────────────┤
│  TERRITORY MANAGEMENT 2.0 (Active: Insulet_Territories)         │
│  100 territories │ 6 types │ 110 user assignments               │
│  Account=Edit, Contact=Edit, Lead=Read, Opp/Case=None           │
├─────────────────────────────────────────────────────────────────┤
│  SHARING RULES  ← Primary record-access mechanism               │
│  AccountShare Rule: 677,313 │ OppShare Rule: 2,406              │
│  CaseShare Rule: 294                                            │
├─────────────────────────────────────────────────────────────────┤
│  APEX MANAGED SHARING                                           │
│  TrainingSharingHandler  → Training accepted → Account share    │
│  ObservationSharingHandler → Delegate change → Account share    │
├─────────────────────────────────────────────────────────────────┤
│  EXPERIENCE CLOUD                                               │
│  Trainer Portal (Live) │ 68 External Trainer users              │
│  Customer Community Plus license                                │
├─────────────────────────────────────────────────────────────────┤
│  PERSONA MODEL                                                  │
│  35 Profiles │ 51 Permission Sets │ 27 Permission Set Groups    │
│  26-node Role Hierarchy │ 16 Queues │ 11 Public Groups          │
└─────────────────────────────────────────────────────────────────┘
```

---

## How This Assessment Was Conducted

### Methodology

All findings are evidence-based. No assumptions were made without a corroborating query or metadata artifact. The assessment used four data sources in priority order:

1. **Live SOQL queries** via Salesforce DX MCP (`run_soql_query` tool)
2. **Tooling API queries** for EntityDefinition (OWD), ObjectPermissions, PermissionSet bypass checks
3. **Local metadata snapshot** (`insulet-devint2-metadata-snapshot` project) for profiles, permission sets, permission set groups, roles, settings files, and Apex class code
4. **Share record aggregates** for evidence of active sharing mechanisms

### Prerequisites

```bash
# Salesforce CLI v2.x
sf --version

# Authenticated org alias
sf org display --target-org devint2

# Python 3.9+ (for analysis scripts)
python3 --version
```

### Reproduce the SOQL Evidence

Every query used in the assessment can be re-run against any org:

```bash
# OWD for all objects
sf data query --target-org devint2 --use-tooling-api \
  --query "SELECT QualifiedApiName, InternalSharingModel, ExternalSharingModel \
           FROM EntityDefinition WHERE IsCustomizable = true ORDER BY QualifiedApiName"

# Org-level defaults
sf data query --target-org devint2 \
  --query "SELECT DefaultAccountAccess, DefaultContactAccess, DefaultOpportunityAccess, \
           DefaultLeadAccess, DefaultCaseAccess FROM Organization"

# Permission sets with system bypass
sf data query --target-org devint2 \
  --query "SELECT Name, PermissionsViewAllData, PermissionsModifyAllData, PermissionsManageUsers \
           FROM PermissionSet WHERE PermissionsViewAllData = true OR PermissionsModifyAllData = true"

# Account sharing by mechanism
sf data query --target-org devint2 \
  --query "SELECT RowCause, COUNT(Id) FROM AccountShare GROUP BY RowCause"

# Active territory model
sf data query --target-org devint2 \
  --query "SELECT Id, DeveloperName, State, ActivatedDate FROM Territory2Model"

# Experience Cloud networks
sf data query --target-org devint2 \
  --query "SELECT Id, Name, Status, UrlPathPrefix FROM Network"

# Permission set group composition
sf data query --target-org devint2 \
  --query "SELECT PermissionSetGroup.DeveloperName, PermissionSet.Name \
           FROM PermissionSetGroupComponent ORDER BY PermissionSetGroup.DeveloperName"
```

### Run the Analysis Scripts

```bash
# Identify unreferenced custom fields (fields in schema but not used in any metadata)
cd scripts
python3 find_unreferenced_fields.py \
  --metadata-dir ../insulet-devint2-metadata-snapshot/force-app/main/default \
  --output unreferenced_fields.csv

# Generate a field reference report (which metadata types reference each field)
python3 field_reference_report.py \
  --metadata-dir ../insulet-devint2-metadata-snapshot/force-app/main/default \
  --output field_reference_report.csv
```

---

## Sharing Mechanisms Identified (Summary)

| Category | Mechanisms | Count |
|----------|-----------|-------|
| **Baseline OWD** | Private, ControlledByParent, ReadWrite | 3 variants |
| **Role-Based** | Role Hierarchy (implicit upward) | 26 roles |
| **Territory** | TM2 Assignments, Territory2AssociationManual | 2 types |
| **Declarative** | Sharing Rules (Account/Opp/Case/Custom) | 680K+ share records |
| **Programmatic** | TrainingSharingHandler, ObservationSharingHandler, OrgSync SYSTEM_MODE | 2 dedicated + 43 supporting |
| **Manual** | AccountShare RowCause=Manual | 68 records |
| **Implicit** | ImplicitParent, PortalImplicit, RelatedPortalUser | 1,974 records |
| **Community** | Experience Cloud (Trainer Portal), ACR multi-account | 1 network |
| **Bypass** | ViewAllData (9 perm sets), ModifyAllData (2), without sharing Apex | Critical risk |
| **Queue** | 16 queues routing Lead/Task/Case/Reimbursement__c | 16 queues |

Full catalog with evidence sources → [`docs/SHARING_ACCESS_ASSESSMENT.md`](docs/SHARING_ACCESS_ASSESSMENT.md#deliverable-6--sharing-mechanism-catalog)

---

## Top Remediation Actions

```
Priority  Action
────────  ──────────────────────────────────────────────────────────────────
CRITICAL  1. Scope Odaseva_Service_User_Permissions: remove ManageUsers +
             AuthorApex; add IP restriction on the integration user account
CRITICAL  2. Change OWD on all OrgSync staging objects from ReadWrite→Private;
             grant access only to integration users via explicit permission set
HIGH      3. Enable Secure Guest Access in Sharing Settings
HIGH      4. Replace PermissionsViewAllData=true in Dev Support / Functional
             Analyst perm sets with per-object ViewAllRecords grants
HIGH      5. Add SharingRules metadata type to the project manifest and
             retrieve into source control for governance visibility
MEDIUM    6. Implement a scheduled cleanup job for manual AccountShare records
MEDIUM    7. Security code review of 45 Apex sharing classes — verify
             without sharing scope is narrowly bounded
LOW       8. Audit production System Administrator count; target <10 active
```

---

## Related Resources

- **Full Assessment Report:** [`docs/SHARING_ACCESS_ASSESSMENT.md`](docs/SHARING_ACCESS_ASSESSMENT.md)
- **Execution Plan:** [`docs/EXECUTION_PLAN.md`](docs/EXECUTION_PLAN.md)
- **Org Inventory:** [`docs/ORG_INVENTORY.md`](docs/ORG_INVENTORY.md)
- **Source Metadata Repo:** `insulet-devint2-metadata-snapshot` (private, local)
- **Salesforce Sharing Architecture Docs:** [developer.salesforce.com/docs/atlas.en-us.securityImplGuide](https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/)

---

## Assessment Scope & Limitations

| In Scope | Out of Scope / Limitations |
|----------|---------------------------|
| OWD (internal + external) for all 720 customizable objects | Production org (this is DevInt2 sandbox) |
| Territory Management 2.0 active model | Sharing rule XML definitions (not in local metadata snapshot) |
| All 35 profiles, 51 permission sets, 27 PSGs | FLS for all 615 objects (queried only for 8 key objects) |
| Role hierarchy (26 roles) | Reports and Dashboards folder visibility |
| 16 queues and 11 public groups | Platform Encryption / Shield configuration (separate assessment) |
| AccountShare / OpportunityShare / CaseShare aggregates | Login forensics / event log analysis |
| Apex sharing code review (45 classes) | SAML/SSO certificate details |
| Experience Cloud (Trainer Portal) | Restriction Rules / Scoping Rules (not found in this org) |
| 18 installed packages | Connected App OAuth scope enumeration |
| 9 bypass permission sets identified | |

---

*Prepared by AI Architect Assessment | Insulet Corporation | DevInt2 | March 2026*
