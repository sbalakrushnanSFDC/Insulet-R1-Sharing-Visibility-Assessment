# Salesforce Sharing & Access-Control Assessment — Execution Plan

**Target Org:** Insulet DevInt2 Sandbox (`devint2`) | **API Version:** 66.0  
**Date Approved:** March 9, 2026 | **Status:** COMPLETED — all phases executed

---

## Overview

A five-phase evidence-based execution plan for assessing all Salesforce sharing, visibility, and access-control mechanisms. Each phase builds on the previous one, moving from foundational org-wide controls through identity and object access, to record-level visibility, and finally synthesis into deliverables.

**Evidence hierarchy used:**
1. Live SOQL / Tooling API queries (highest confidence)
2. Local metadata snapshot (high confidence — point-in-time snapshot)
3. Apex code review (high confidence)
4. Inferred from mechanism interactions (medium confidence — flagged explicitly)

---

## Phase 1: Org-Wide Baseline & Foundational Controls ✅

**Goal:** Establish the foundational sharing model — OWD defaults, external sharing model, territory management configuration, hierarchy settings, and org-level security controls.

### 1A — Organization-Wide Defaults

| Action | Tool | Status |
|--------|------|--------|
| Read `Sharing.settings-meta.xml` | Local metadata | ✅ |
| Read `Territory2.settings-meta.xml` | Local metadata | ✅ |
| Read `Security.settings-meta.xml` | Local metadata | ✅ |
| Read `Account.settings-meta.xml`, `Communities.settings-meta.xml` | Local metadata | ✅ |
| Query `Organization` object for default access levels | SOQL | ✅ |
| Query `EntityDefinition` Tooling API — OWD for all 720 objects | Tooling API | ✅ |

**Key findings:**
- Account, Contact, Opportunity, Lead, Case = Private/Private (correct baseline)
- 7 OrgSync staging objects = **ReadWrite** internally (CRITICAL risk)
- External Sharing Model: enabled
- Secure Guest Access: **disabled** (HIGH risk)
- Admin Login As Any User: enabled

### 1B — Territory Management 2.0

| Action | Tool | Status |
|--------|------|--------|
| Query `Territory2Model` | SOQL | ✅ |
| Query `Territory2` (active model) | SOQL | ✅ |
| Query `Territory2Type` | SOQL | ✅ |
| Count `UserTerritory2Association` | SOQL | ✅ |

**Key findings:**
- 1 active model: `Insulet_Territories` (activated Dec 11, 2025)
- 3 planning models (Q3_2025, New_Territory_model, PHTEST)
- 100 territories, 6 types (Sales_Geography, Sales_Pediatric, Trainer, Kaiser, All_Consumer_Accounts, Geo_Test1)
- 110 active user-territory associations
- Account=Edit, Contact=Edit, Lead=Read; Opportunity filter **disabled**

### 1C — Installed Packages & Licenses

| Action | Tool | Status |
|--------|------|--------|
| Read `installed-packages.json` | Local org-details | ✅ |
| Query `UserLicense` | SOQL | ✅ |
| Query `PermissionSetLicense` | SOQL | ✅ |

**Key findings:**
- 18 installed packages (Amazon Connect, AppOmni, Conga, DocuSign, Marketing Cloud, OmniStudio, Odaseva, OrgSync-CDC, Nebula Logger)
- Salesforce Full: 329 / 2,523 used
- Customer Community Plus: 68 / 4,125 used
- Guest User License: 1 / 25 used

---

## Phase 2: Identity, Persona & Role Extraction ✅

**Goal:** Map every user persona, their profile, permission set assignments, role hierarchy, public groups, and queues.

### 2A — User Census

| Action | Tool | Status |
|--------|------|--------|
| Query active `User` with Profile + Role | SOQL (200 rows) | ✅ |

**Key findings:**
- 200 rows returned (query limit) — full picture in INVENTORY.md
- External Trainer: 68, Sales: 66, IT: 26, Service: 24, Marketing: 5
- User types: Standard=129, PowerCustomerSuccess=68, AutomatedProcess=2

### 2B — Permission Set Assignments & PSG Composition

| Action | Tool | Status |
|--------|------|--------|
| Query `PermissionSetAssignment` (active users, non-profile) | SOQL (331 records) | ✅ |
| Query `PermissionSetGroupComponent` | SOQL (181 records) | ✅ |
| Query `PermissionSetGroup` for muting perm sets | SOQL | ✅ |

**Key findings:**
- 27 custom PSGs; top assignments: Third_Party_Trainers (26), Training_Coordinators (21), Clinical_Services_Manager (13)
- All major business PSGs compose: Core_Access + HealthCloudFoundation + OmniStudioExecution + SSO_enabled
- Development_Support PSG includes `IT_Modify_all` (broad permissions)

### 2C — Role Hierarchy

| Action | Tool | Status |
|--------|------|--------|
| Query `UserRole` | SOQL (26 roles) | ✅ |
| Read 24 `.role-meta.xml` files | Local metadata | ✅ |

**Key findings:**
- 14 internal roles in sales/clinical hierarchy
- 12 Customer Portal roles (individual portal-user roles for External Trainers, named after usernames)
- Director_of_Sales is the root of the primary sales hierarchy

### 2D — Public Groups & Queues

| Action | Tool | Status |
|--------|------|--------|
| Query `Group` (Regular + Queue + Role + RoleAndSubordinates) | SOQL (93 records) | ✅ |
| Query `QueueSobject` | SOQL (19 records) | ✅ |

**Key findings:**
- 16 queues; 11 named public groups (Field Sales GM/RBD, Field Sales TM/DSM, Inside Sales Rep/Manager, etc.)
- Queue objects: Lead (8), Task (10), Case (1), Reimbursement__c (1)
- Portal Users group exists (used for community members)

---

## Phase 3: Object & Field-Level Access Mapping ✅

**Goal:** Extract CRUD permissions, FLS grants, View All Data / Modify All Data, and field-level security.

### 3A — Object-Level CRUD

| Action | Tool | Status |
|--------|------|--------|
| Query `ObjectPermissions` (standard API, non-Tooling) | SOQL (2,000 records returned) | ✅ |

**Key findings:**
- Campaign: 17 perm sets/profiles grant ViewAll (highest)
- Account: 15 perm sets/profiles grant ViewAll
- OrgSync staging objects: 8-10 each (no sharing needed due to ReadWrite OWD)

### 3B — Field-Level Security

| Action | Tool | Status |
|--------|------|--------|
| Scoped query on `FieldPermissions` via local metadata XML | Local profiles + perm sets | Partial ✅ |

*Note: Full FLS extraction for all 615 objects requires batched queries; key objects reviewed via profile/perm set XML.*

### 3C — System Bypass Permissions

| Action | Tool | Status |
|--------|------|--------|
| Query `PermissionSet` WHERE ViewAllData=true OR ModifyAllData=true | SOQL (13 records returned) | ✅ |

**Key findings — PermissionSets with system bypass:**

| Permission Set | ViewAll | ModifyAll | API | AuthApex | ManageUsers |
|---------------|---------|-----------|-----|----------|-------------|
| Odaseva_Service_User_Permissions | ✅ | **✅** | ✅ | **✅** | **✅** |
| CTI_Integration_Access | ✅ | ❌ | ✅ | ❌ | ❌ |
| Query_AllFiles | ✅ | ❌ | ❌ | ❌ | ❌ |
| Development_Support_Core_Access | ✅ | ❌ | ❌ | ❌ | ❌ |
| Functional_Analyst_Core_Access | ✅ | ❌ | ❌ | ❌ | ❌ |
| Development_Support (PSG) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Functional_Analyst (PSG) | ✅ | ❌ | ❌ | ❌ | ❌ |
| sfdc_a360_sfcrm_data_extract | ✅ | ❌ | ✅ | ❌ | ❌ |
| Admin Profile (profile-owned) | ✅ | ✅ | ✅ | ✅ | ✅ |

### 3D — Record Types

| Action | Tool | Status |
|--------|------|--------|
| Query `RecordType WHERE IsActive = true` | SOQL (60 active RecordTypes) | ✅ |

**Key findings:**
- Account: 6 types (Patient, Patient_Delegate, Provider, Trainer, PersonAccount = Person Accounts; Practice, Pharmacy = business)
- Case: 3 types; Lead: 3 types; Opportunity: 1 type (NCS_Opportunity)
- Training__c: 3 types (CPT_Training, E_Learning, Live_Training) — Apex sharing logic scoped to Live_Training only

---

## Phase 4: Record-Level Visibility Discovery ✅

**Goal:** Discover all sharing rules, Apex managed sharing, manual shares, implicit sharing, and Experience Cloud sharing.

### 4A — Sharing Rule Evidence

| Action | Tool | Status |
|--------|------|--------|
| Aggregate AccountShare by RowCause | SOQL | ✅ |
| Aggregate OpportunityShare by RowCause | SOQL | ✅ |
| Aggregate CaseShare by RowCause | SOQL | ✅ |
| Sample AccountShare WHERE RowCause = 'Rule' | SOQL (50 records) | ✅ |

**Sharing rule volume:**

| Object | Rule Shares | Owner Shares | Territory Shares | Manual Shares |
|--------|------------|-------------|----------------|--------------|
| Account | 677,313 | 129,959 | 1,876 + 180 T2Manual | 68 |
| Opportunity | 2,406 | 2,406 | 1 (T2Forecast) | 0 |
| Case | 294 | 477 | 0 | 0 (1 RelPortal) |

*Note: Sharing rule XML definitions not in local metadata snapshot — to-do: add to project manifest.*

### 4B — Apex Managed Sharing

| Action | Tool | Status |
|--------|------|--------|
| Grep all Apex classes for `__Share`, `RowCause`, `AccessLevel` | Code grep (45 files matched) | ✅ |
| Read `ObservationSharingHandler.cls` | Local metadata | ✅ |
| Read `TrainingSharingHandler.cls` | Local metadata | ✅ |
| Read `OrgSync_Patient_ACRService.cls` | Local metadata | ✅ |

**Key findings:**
- 45 Apex classes reference sharing/AccessLevel patterns
- 2 dedicated sharing handlers use `without sharing` inner classes + `AccessLevel.SYSTEM_MODE`
- Multiple OrgSync classes use SYSTEM_MODE for integration DML operations
- `ScheduledPermissionAssigner` dynamically assigns permission sets (needs review)

### 4C — Manual Shares

| Action | Tool | Status |
|--------|------|--------|
| Query AccountShare WHERE RowCause = 'Manual' LIMIT 10 | SOQL | ✅ |

**Key finding:** 68 manual Account shares exist; user-to-account grants with Edit access; no lifecycle governance identified.

### 4D — Implicit Sharing

| Action | Tool | Status |
|--------|------|--------|
| Read Account.settings-meta.xml (Account Teams, multi-account contacts) | Local metadata | ✅ |
| AccountShare RowCause=ImplicitParent aggregate | SOQL | ✅ |
| AccountShare RowCause=PortalImplicit aggregate | SOQL | ✅ |

**Key findings:**
- ImplicitParent: 1,905 AccountShare records (Contact/Opp/Case child access via Account)
- PortalImplicit: 68 (matches External Trainer community user count)
- Account Teams: DISABLED
- Multi-account contacts: ENABLED (via AccountContactRelation, managed by OrgSync_Patient_ACRService)

### 4E — Experience Cloud

| Action | Tool | Status |
|--------|------|--------|
| Query `Network` | SOQL (1 record) | ✅ |
| Query `Profile WHERE UserType IN ('Guest','PowerCustomerSuccess')` | SOQL (2 profiles) | ✅ |
| Read `Communities.settings-meta.xml` | Local metadata | ✅ |

**Key findings:**
- 1 live network: "Trainer Portal" (`/TrainerPortalvforcesite`)
- 2 community-type profiles: External Trainer (68 active PowerCustomerSuccess users) + Trainer Portal Profile (Guest)
- Secure Guest Access = **disabled** — HIGH risk
- Community user visibility = disabled (users can't see each other)
- Apex sharing (TrainingSharingHandler) is the primary mechanism for community user record access — not Sharing Sets

### 4F — Restriction / Scoping Rules

| Action | Tool | Status |
|--------|------|--------|
| Check for SharingRestrictionRule / ScopingRule metadata | Metadata inspection | ✅ |

**Key finding:** No Restriction Rules or Scoping Rules found in this org.

---

## Phase 5: Effective Access Synthesis & Deliverable Generation ✅

**Goal:** Synthesize all evidence into 7 deliverables.

### Deliverables Generated

| Deliverable | Output Location | Status |
|-------------|----------------|--------|
| Executive Summary | `docs/SHARING_ACCESS_ASSESSMENT.md` §1 | ✅ |
| Detailed Narrative Assessment | `docs/SHARING_ACCESS_ASSESSMENT.md` §2 | ✅ |
| Visual Models (5 Mermaid diagrams) | `docs/SHARING_ACCESS_ASSESSMENT.md` §3 | ✅ |
| Object View by Persona Matrix + CSV | `docs/SHARING_ACCESS_ASSESSMENT.md` §4 | ✅ |
| Persona View by Object/Records/Fields + CSV | `docs/SHARING_ACCESS_ASSESSMENT.md` §5 | ✅ |
| Sharing Mechanism Catalog (27 mechanisms) | `docs/SHARING_ACCESS_ASSESSMENT.md` §6 | ✅ |
| Findings & Recommendations (15 items) | `docs/SHARING_ACCESS_ASSESSMENT.md` §7 | ✅ |

---

## Queries Not Fully Executed (Gaps)

| Query / Action | Reason | Workaround Used |
|----------------|--------|----------------|
| Full FLS for all 615 objects | Query governor limits; would require 615 batched calls | Key objects reviewed via local metadata XML |
| `SharingRules` metadata retrieval | Not in local metadata snapshot; no manifest entry | AccountShare aggregate evidence used to confirm rules exist |
| `SharingSet` query | Object not accessible in this sandbox context | Architecture inferred from community user profile + PortalImplicit shares |
| `PermissionSetAssignment` full dataset | Query returned 331 records (may be paginated) | Top assignments captured; PSG composition used to fill gaps |
| `ObjectPermissions` via Tooling API | Unsupported via Tooling API in this org | Standard REST API used instead (2,000 records returned) |

---

*Execution plan authored and executed by AI Architect Assessment | March 9, 2026*
