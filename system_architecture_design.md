# BlindWatch AI: Production-Grade System Architecture Design

This document details the refactored, multi-tenant modular architecture of BlindWatch AI, transitioning from a monolithic application into a domain-driven microservices platform.

---

## 1. Full System Architecture

BlindWatch AI is structured as a distributed microservice network coordinate system. The frontend Next.js client interacts with API gateways that route calls to individual isolated services, while heavy frame telemetry is communicated via high-throughput message buses.

```mermaid
graph TD
    Client[Next.js Frontend Client]
    Gateway[Kong / API Gateway]
    Bus[Kafka Event Bus / Message Broker]
    Cache[(Redis Cache & Session State)]
    DB[(PostgreSQL Tenant DBs)]
    Storage[(MinIO Binary Storage)]

    Client -->|REST & WebSockets| Gateway
    Gateway --> Auth[Auth Service]
    Gateway --> Camera[Camera Service]
    Gateway --> Vision[Vision Service]
    Gateway --> Privacy[Privacy Service]
    Gateway --> Event[Event Service]
    Gateway --> Audit[Audit Service]
    Gateway --> Analytics[Analytics Service]
    Gateway --> Simulator[Simulator Service]
    Gateway --> Gov[Identity Governance Service]

    Auth & Camera & Vision & Privacy & Event & Audit & Analytics & Simulator & Gov --> Bus
    Auth & Camera & Vision & Privacy & Event & Audit & Analytics & Simulator & Gov --> DB
    Auth & Camera & Vision & Privacy & Event & Audit & Analytics & Simulator & Gov --> Cache
    Event & Audit & Analytics --> Storage
```

---

## 2. Service Architecture

Each service operates in a shared-nothing boundary, exposing a private database context and communicating asynchronously through Pydantic event schemas.

| Service | Primary Responsibility | Data Store Ownership | Key Abstractions |
| :--- | :--- | :--- | :--- |
| **Auth Service** | Authentication, JWT management, RBAC enforcement | PostgreSQL (`users`, `roles`, `permissions`, `sessions`) | User, Role, Permission |
| **Camera Service** | Camera nodes setup, RTSP configuration, health telemetry | PostgreSQL (`cameras`, `camera_groups`, `camera_status`) | Camera, CameraGroup |
| **Vision Service** | Frame analysis, YOLO tracking, face coordinates isolation | PostgreSQL (`vision_jobs`, `detections`, `entity_tracks`), Redis (coordinates) | VisionJob, Detection, EntityTrack |
| **Privacy Service** | Dynamic masking, privacy score calculation, CCPA rules | PostgreSQL (`privacy_scores`, `compliance_rules`, `privacy_events`) | PrivacyScore, ComplianceRule |
| **Event Service** | Anomaly classification, timeline tracking, evidence | PostgreSQL (`events`, `event_evidence`, `event_timelines`), MinIO (snapshots) | ThreatEvent, ThreatEvidence |
| **Audit Service** | Cryptographic ledger, transaction history, session checks | PostgreSQL (`audit_logs`, `audit_sessions`, `approval_history`) | AuditLog, AuditSession |
| **Analytics Service**| Trend compilation, camera efficiency indexing | PostgreSQL (`analytics_snapshots`, `trend_reports`) | AnalyticsSnapshot, TrendReport |
| **Simulator Service**| Privacy vs safety simulation, hypothetical scoring | PostgreSQL (`simulation_runs`, `simulation_results`) | SimulationRun, SimulationResult |
| **Identity Gov** | Decryption petition review, dual-key XOR key management | PostgreSQL (`identity_requests`, `approvals`, `reveal_sessions`) | IdentityRequest, Approval |

---

## 3. Database Relationships

To maintain multi-tenant routing, every table is isolated with a indexed `tenant_id` column. Inside the SQL level, relationships link entities within the same tenant.

```mermaid
erDiagram
    TENANT {
        string tenant_id PK
        string name
    }
    
    USER {
        int id PK
        string tenant_id FK
        string username
        string hashed_password
        string role
    }
    
    CAMERA {
        int id PK
        string tenant_id FK
        string name
        string rtsp_url
        string status
    }
    
    ANONYMOUS_ENTITY {
        string entity_id PK
        string tenant_id FK
        string last_location
        float risk_score
    }
    
    ENTITY_TRACK {
        int id PK
        string tenant_id FK
        string entity_id FK
        int location_x
        int location_y
    }
    
    THREAT_EVENT {
        int id PK
        string tenant_id FK
        string event_id PK
        string event_type
        string entity_id FK
        float risk_score
        string status
    }
    
    IDENTITY_REQUEST {
        int id PK
        string tenant_id FK
        string request_id PK
        int requester_id FK
        string entity_id FK
        string encrypted_identity
        string auditor_key_share
        string admin_key_share
        string status
    }

    TENANT ||--o{ USER : "owns"
    TENANT ||--o{ CAMERA : "registers"
    TENANT ||--o{ ANONYMOUS_ENTITY : "tracks"
    ANONYMOUS_ENTITY ||--o{ ENTITY_TRACK : "generates"
    ANONYMOUS_ENTITY ||--o{ THREAT_EVENT : "implicates"
    USER ||--o{ IDENTITY_REQUEST : "petitions"
    ANONYMOUS_ENTITY ||--o{ IDENTITY_REQUEST : "targets"
```

---

## 4. Domain Relationships

Domain boundaries dictate that **Identity Governance** is completely decoupled from standard visual ingestion. 표준 감시 및 실시간 추적 도메인은 오직 `entity_id`를 매개로만 협력합니다.

```mermaid
stateDiagram-v2
    [*] --> SurveillanceDomain : Camera Ingest
    SurveillanceDomain --> TrackingDomain : Stream Frames
    TrackingDomain --> ThreatDetectionDomain : Generate Telemetry (Anonymous Entity ID)
    ThreatDetectionDomain --> PrivacyIntelligenceDomain : Calculate Risks
    PrivacyIntelligenceDomain --> AuditDomain : Log Compliance
    
    state IdentityGovernanceDomain {
        [*] --> PetitionFiling : Officer Request
        PetitionFiling --> AuditorSign : Key Share A
        PetitionFiling --> AdminSign : Key Share B
        AuditorSign --> ReconstructKey : Both Approved
        AdminSign --> ReconstructKey
        ReconstructKey --> DecryptIdentity : Lease Granted
    }
    
    TrackingDomain --> IdentityGovernanceDomain : Target Subject ID (Only on authorization)
```

---

## 5. Event Architecture

Message broker events drive async workflows. Pydantic specifications define events exchanged over Kafka:

```
Camera Feed Ingest (RTSP)
    ↓
[Event: FrameReceived] (Surveillance Service)
    ↓
[Event: EntityDetected] (Vision Service -> payload: {entity_id, bounding_box, frame_id})
    ↓
[Event: TrackingUpdated] (Tracking Service -> updates Redis tracks)
    ↓
[Event: AnomalyClassified] (Threat Service -> payload: {event_type, risk_score})
    ↓
[Event: ComplianceIndexCalculated] (Privacy Service -> updates scores)
    ↓
[Event: AuditLogged] (Audit Service -> updates SHA-256 Chain)
```

---

## 6. Storage Architecture

Data classification mandates three specialized storage tiers:

1. **Transactional Data (PostgreSQL)**
   * User directory, credentials, camera indexes, threat profiles, and logs.
   * Row-level security (RLS) restricts database operations strictly to matches on the caller's JWT `tenant_id`.
2. **Active States (Redis Cluster)**
   * Live websocket locations, active user sessions, video chunk frames, and threat queues.
3. **Binary Assets (MinIO Object Storage)**
   * Encrypted evidence frames, security recordings clips, and exported reports.

---

## 7. WebSocket Architecture

WebSockets deliver real-time streams to the portal console:

* `/ws/live-feed`: Streams frame coordinates, active bounding boxes, and camera offline events.
* `/ws/alerts`: Streams security breaches and escalated threat events.
* `/ws/dashboard`: Streams real-time system safety metrics, privacy scores, and ledger updates.

---

## 8. Frontend Module Architecture

The Next.js client is refactored into modular components, isolating business logic from views:

```
src/
├── app/
│   ├── portal/
│   │   ├── monitoring/      # Camera grid, RTSP streams, feeds
│   │   ├── events/          # AI alerts, explaining reasoning
│   │   ├── privacy/         # Transparency metrics, retention scope
│   │   ├── simulator/       # Policies modeling, sandboxed run
│   │   └── audit/           # Cryptographic chain verify dashboard
├── components/              # Shared UI components
├── config.ts                # API endpoint mappings
└── hooks/                   # Custom fetching and WS streams
```

---

## 9. Core Product Rule: Zero-Knowledge Identity Governance

The design strictly enforces: **Identity Is A Privileged Resource, Not Standard Data.**

* Standard tracking datasets only ever reference the hashed `entity_id` (e.g. `Entity_2B8C`).
* The biological details (name, SSN, or clearance) are stored in an encrypted block.
* Keys are sharded as XOR shares across Admin and Auditor accounts. Decryption is only possible during an active, dual-signed lease window.

---

## 10. Volume 2: Complete Database Design (PostgreSQL)

This section outlines the production-ready PostgreSQL relational schema layout designed for high scalability (up to 10,000 cameras and 1 million daily events).

### Database Rules
* **Primary Keys**: Every table uses a globally unique `UUID` as its primary identifier.
* **Audit Columns**: Every table contains `created_at TIMESTAMP` and `updated_at TIMESTAMP` tracking fields.
* **Multi-Tenancy**: Every table is partitioned or filtered via a required `tenant_id UUID` column.
* **Soft Delete**: Critical operational directories (`users`, `cameras`, `events`, `identity_requests`, `anonymous_entities`) include `is_deleted BOOLEAN` fields.

```mermaid
erDiagram
    users {
        uuid id PK
        uuid tenant_id
        varchar email UNIQUE
        varchar username
        text password_hash
        varchar full_name
        varchar phone
        uuid role_id FK
        varchar status
        boolean mfa_enabled
        timestamp last_login
        timestamp created_at
        timestamp updated_at
        boolean is_deleted
    }
    roles {
        uuid id PK
        varchar name
        text description
        timestamp created_at
    }
    permissions {
        uuid id PK
        varchar permission_key UNIQUE
        text description
        timestamp created_at
    }
    role_permissions {
        uuid id PK
        uuid role_id FK
        uuid permission_id FK
    }
    cameras {
        uuid id PK
        uuid tenant_id
        varchar name
        varchar location
        varchar camera_type
        text stream_url
        varchar status
        float health_score
        timestamp last_heartbeat
        timestamp created_at
        timestamp updated_at
        boolean is_deleted
    }
    anonymous_entities {
        uuid id PK
        uuid tenant_id
        text entity_hash UNIQUE
        timestamp first_seen
        timestamp last_seen
        uuid camera_id FK
        varchar status
        float behavior_score
        float risk_score
        timestamp created_at
        timestamp updated_at
        boolean is_deleted
    }
    events {
        uuid id PK
        uuid tenant_id
        varchar event_type
        uuid camera_id FK
        uuid entity_id FK
        float risk_score
        float confidence
        varchar severity
        varchar status
        timestamp created_at
        timestamp updated_at
        boolean is_deleted
    }
    identity_requests {
        uuid id PK
        uuid tenant_id
        uuid event_id FK
        uuid requester_id FK
        text justification
        varchar case_number
        varchar status
        timestamp requested_at
        timestamp created_at
        timestamp updated_at
        boolean is_deleted
    }
    
    users ||--o{ identity_requests : "requests"
    roles ||--o{ users : "assigns"
    roles ||--|{ role_permissions : "contains"
    permissions ||--|{ role_permissions : "granted-to"
    cameras ||--o{ anonymous_entities : "detects"
    anonymous_entities ||--o{ events : "generates"
    events ||--o{ identity_requests : "escalates"
```

### Table Definitions

#### 1. Identity & Role Governance
* **`users`**: Main user catalog. Soft delete enabled.
* **`roles`**: System roles (e.g. `admin`, `auditor`, `officer`, `viewer`).
* **`permissions`**: Access key descriptors (e.g., `camera.read`, `identity.reveal`).
* **`role_permissions`**: Joins roles to specific permission keys.

#### 2. Surveillance & Camera Nodes
* **`cameras`**: Camera catalog (type options: `WEBCAM`, `RTSP`, `VIDEO_UPLOAD`). Soft delete enabled.
* **`camera_groups`**: Organizational groups of cameras.
* **`camera_group_members`**: Mapping table linking cameras to groups.

#### 3. Vision tracking & Detections
* **`anonymous_entities`**: Subject directory. Zero identity data stored. Soft delete enabled.
* **`behavior_signatures`**: Detailed movement and behavior telemetry signatures in JSONB format.
* **`detections`**: Raw YOLO bounding-box telemetry.

#### 4. Anomaly & Event Processing
* **`events`**: Alerts list (type options: `THEFT`, `INTRUSION`, `WEAPON`, `FIRE`, `PANIC`, `VIOLENCE`, `MEDICAL`). Soft delete enabled.
* **`event_timelines`**: Historical frame step tracking for events.
* **`event_evidence`**: Files containing evidence (image, video, report).
* **`event_explanations`**: Explainable AI weights and textual decision tree reasons.

#### 5. Privacy Intelligence
* **`privacy_scores`**: Calculated compliance metrics over time.
* **`compliance_rules`**: Legal or policy constraint parameters.
* **`exposure_risks`**: Flagged vulnerabilities and privacy leakage alerts.

#### 6. Identity Decryption Governance
* **`identity_requests`**: Petitions for temporary identity decryptions. Soft delete enabled.
* **`approvals`**: Multi-signature decision blocks.
* **`identity_reveal_sessions`**: Reveal lease windows and temporary decryptions.

#### 7. Audit & Logs
* **`audit_logs`**: System audit logs ledger.

#### 8. Analytics & Reporting
* **`analytics_snapshots`**: Aggregated day snapshots.
* **`threat_trends`**: Trend statistics.
* **`reports`**: Compilation PDF/CSV files list. Soft delete enabled.

#### 9. Simulator Sandbox
* **`simulation_runs`**: Sandbox runs metadata.
* **`simulation_results`**: Comparative performance indicators.

#### 10. Alerts & Notifications
* **`notifications`**: Live alert banners push notifications.

### Performance Database Indexes
```sql
CREATE INDEX idx_events_created_at ON events(created_at DESC);
CREATE INDEX idx_events_event_type ON events(event_type);
CREATE INDEX idx_anon_entity_hash ON anonymous_entities(entity_hash);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_ident_req_status ON identity_requests(status);
CREATE INDEX idx_priv_score_calc ON privacy_scores(calculated_at DESC);
```

---

## 11. Volume 3: Complete REST API Specification + Button Mappings

This section details the REST API endpoints and direct user interface button mappings across the BlindWatch modular microservices, adhering strictly to versioned paths, audit logging, and role-based policies.

### API Gateway / Routing Rules
* Prefix format: `/api/v1/`
* Security: Validated JWT + Role Permissions.
* Audit Trails: Write operations automatically log to `audit_logs` before returning the HTTP response.

### 1. Authentication & Security Endpoints
* **`POST /api/v1/auth/login`**: Authenticate credentials, log session, and issue JWT token.
  * **Button Mapping**: `Login` Button
* **`POST /api/v1/auth/refresh`**: Refresh expired JWT token using the refresh token.
* **`POST /api/v1/auth/logout`**: Terminate session, invalidate JWT, and record audit log.

### 2. User Management Endpoints (Admin Only)
* **`GET /api/v1/users`**: List all users within the tenant.
* **`POST /api/v1/users`**: Create a new tenant user. Records audit log.
* **`PUT /api/v1/users/{id}`**: Update user details.
* **`DELETE /api/v1/users/{id}`**: Soft-delete a user record (`is_deleted = true`).

### 3. Camera Node Governance Endpoints
* **`POST /api/v1/cameras`**: Register a new camera node. Launches corresponding vision track job.
  * **Button Mapping**: `Add Camera` Button
* **`GET /api/v1/cameras`**: Fetch all cameras for the current tenant.
* **`GET /api/v1/cameras/{id}`**: Fetch details of a single camera.
* **`PUT /api/v1/cameras/{id}`**: Edit stream configuration or settings.
* **`DELETE /api/v1/cameras/{id}`**: Delete camera node.
* **`POST /api/v1/cameras/{id}/test`**: Validate RTSP connection status.
  * **Button Mapping**: `Test Connection` Button

### 4. Live Vision Feeds
* **`GET /api/v1/live-feed/{camera_id}`**: Restructure stream frames for HTTP stream preview.
* **`WS /ws/live-feed/{camera_id}`**: Push real-time base64 frame stream and bounding-box telemetries.
  * **Button Mapping**: `Pause Feed` / `Resume Feed` / `Fullscreen Feed` (handled frontend-side)

### 5. Entity Surveillance Profiles
* **`GET /api/v1/entities`**: List tracked anonymous entities and current risk ratings.
* **`GET /api/v1/entities/{id}`**: Fetch behavior metrics, movement path history, and risk trends.

### 6. Threat Event Lifecycle
* **`GET /api/v1/events`**: Fetch anomaly alerts. Filters: `status`, `severity`, `event_type`, `date`.
* **`GET /api/v1/events/{id}`**: Fetch full event parameters.
* **`POST /api/v1/events/{id}/escalate`**: Move event into active supervisor escalation queues.
  * **Button Mapping**: `Escalate` Button
* **`POST /api/v1/events/{id}/dismiss`**: Set event status to `DISMISSED` (false positive).
  * **Button Mapping**: `Dismiss` Button

### 7. AI Explanations & Evidence
* **`GET /api/v1/events/{id}/evidence`**: Retrieve evidentiary frame snapshots or short video loops.
  * **Button Mapping**: `View Evidence` Button
* **`GET /api/v1/evidence/{id}/download`**: Direct download link to original evidence attachment file.
* **`GET /api/v1/events/{id}/explanation`**: Fetch XAI decision rationale and weights.
  * **Button Mapping**: `Explain Decision` Button

### 8. Privacy Dashboards & Audits
* **`GET /api/v1/privacy/dashboard`**: Fetch compliance posture score and active data leaks status.
* **`POST /api/v1/privacy/assessment`**: Trigger dynamic GDPR/CCPA automated rules check.
  * **Button Mapping**: `Run Assessment` Button
* **`GET /api/v1/privacy/exposure-risks`**: Fetch list of currently flagged tracking risks.
* **`GET /api/v1/privacy/compliance`**: Query active regulation constraints config.

### 9. Identity Reveal Approval Workflows
* **`POST /api/v1/identity-requests`**: File request for temporary zero-knowledge key decryption.
  * **Button Mapping**: `Request Identity` Button
* **`GET /api/v1/identity-requests`**: Retrieve current reveal petitions history.
* **`POST /api/v1/identity-requests/{id}/auditor-approve`**: Record first-signature approval.
  * **Button Mapping**: `Approve` (Auditor Screen) Button
* **`POST /api/v1/identity-requests/{id}/auditor-reject`**: Record auditor rejection.
* **`POST /api/v1/identity-requests/{id}/admin-approve`**: Record second-signature approval.

### 10. Audit Trails & Logs Ledger
* **`GET /api/v1/audit/logs`**: Query ledger database logs. Filters: `user`, `action`, `date`.
* **`GET /api/v1/audit/logs/{id}`**: View detailed payload block of single audit transaction.

### 11. Dashboard Analytics & Trends
* **`GET /api/v1/analytics/dashboard`**: Consolidated metrics.
* **`GET /api/v1/analytics/threat-trends`**: Chronological trend mappings.
* **`GET /api/v1/analytics/camera-effectiveness`**: Camera performance comparison indexes.
* **`GET /api/v1/analytics/privacy-trends`**: History of calculated compliance scores.
* **`GET /api/v1/analytics/heatmaps`**: Coordinate dwell-time visual arrays.

### 12. Simulator Sandbox
* **`POST /api/v1/simulator/run`**: Trigger simulator run config.
  * **Button Mapping**: `Run Simulation` Button
* **`GET /api/v1/simulator/history`**: Get prior run results comparisons.
* **`GET /api/v1/simulator/{id}`**: Retrieve full details of simulator run parameters and scores.

### 13. Reports Generator
* **`POST /api/v1/reports/generate`**: Trigger compilation PDF/CSV report generation.
  * **Button Mapping**: `Generate Report` Button
* **`GET /api/v1/reports/{id}/download`**: Retrieve compiled PDF report output.

### 14. Real-Time Push Notifications
* **`GET /api/v1/notifications`**: Query unread status logs.
* **`POST /api/v1/notifications/{id}/read`**: Mark message as read.

### 15. WebSocket Channels
* **`WS /ws/dashboard`**: Broad updates.
* **`WS /ws/alerts`**: Push urgent alerts.
* **`WS /ws/live-feed`**: Bounding box coordinates.

---

## 12. Volume 4: Complete Page-by-Page Frontend Specification

This section details the frontend specification for the BlindWatch AI platform. Designed as a production-grade enterprise security dashboard rather than a standard admin console, the UI draws inspiration from Palantir Gotham, CrowdStrike Falcon, Anduril Lattice, and Datadog.

### Theme & Design Aesthetics
* **Theme**: Sleek Dark Theme, rich HSL tailored color palette.
* **Styling**: Glassmorphism (`backdrop-filter: blur()`), glowing borders, smooth micro-animations, and dynamic transitions.
* **Global States**: Every page natively supports Loading, Empty, Error, and Success states.
* **Action Lifecycle**:
  ```
  User Action (Button/Input)
  ↓
  API Route Call (/api/v1/...)
  ↓
  Database Transaction (Atomic SQL)
  ↓
  Audit Trail Logged (Cryptographic Chain)
  ↓
  UI State Hot-Refresh
  ```

### Page Specifications

#### Page 1: Login Page
* **URL**: `/auth/login`
* **Components**:
  * **Brand Logo**: BlindWatch AI (sleek SVG logo mark).
  * **Email & Password Input Fields** with inline validators.
  * **Remember Me**: Custom styled checkbox.
  * **Login Button**: Triggers `POST /api/v1/auth/login`.
* **State Outcomes**:
  * *Success*: JWT session saved, redirect to `/dashboard`.
  * *Failure*: Toast alert ("Invalid Credentials").
  * *Forgot Password*: Accessible via modal request form.

#### Page 2: Enterprise Dashboard
* **URL**: `/dashboard`
* **Purpose**: Real-time visual posture of globally tracked cameras, threats, and privacy indexes.
* **Top Metric Cards** (sourced from `GET /api/v1/analytics/dashboard`):
  1. **Active Cameras Count**
  2. **Active Anonymous Entities**
  3. **Threat Alerts Today**
  4. **Dynamic Privacy Score**
  5. **Pending Identity Reveals**
  6. **Compliance Posture Index**
* **Live Interactive Widgets**:
  * **Real-time Threat Trend Chart**: Chronological feed connected to `WS /ws/dashboard`.
  * **Camera Health Topology Map**: Interactive camera nodes colored dynamically (Green: Active, Yellow: Warning, Red: Offline).
  * **Privacy Trend Graph**: Interactive SVG line chart rendering data of the last 30 days.
  * **Recent Events Grid**:
    * Columns: `Event`, `Severity`, `Risk`, `Status`, `Time`.
    * Interaction: Click row to slide open detailed Event Panel drawer.

#### Page 3: Live Monitoring Surveillance Grid
* **URL**: `/live-monitoring`
* **Purpose**: Low-latency video feeds and anonymization monitoring.
* **Layout Grid**: Layout switcher supporting `4`, `8`, `16`, or `32` simultaneous streams.
* **Feed Cards**:
  * Contains: Camera Name, Online Status, FPS Counter, Entity Count.
  * Canvas Overlay: Displays anonymized bounding boxes with random Entity ID (e.g. `ENT_93A7`) and risk metrics.
  * Interaction Controls:
    * **Fullscreen**: Opens video viewport to maximum resolution.
    * **Pause Feed**: Stops rendering frame buffers (saves local resources).
    * **Capture Snapshot**: Triggers `POST /api/v1/camera/snapshot` to create evidence record.
    * **Camera Details**: Opens right-aligned inspection drawer showing metrics.

#### Page 4: Camera Management Node Manager
* **URL**: `/cameras`
* **Table**:
  * Columns: `Name`, `Type`, `Location`, `Health Score`, `Status`, `Actions`.
* **Action Triggers**:
  * **Add Camera Modal**: Dialog with fields for Name, Location, Camera Type, and Stream URL. Triggers `POST /api/v1/cameras`.
  * **Test Connection**: Triggers `POST /api/v1/cameras/{id}/test` to display success/failure indicator.
  * **Edit Configuration**: Modals targeting properties. Triggers `PUT /api/v1/cameras/{id}`.
  * **Delete Node**: Confirms soft deletion of the camera node. Triggers `DELETE /api/v1/cameras/{id}`.

#### Page 5: Events Center Alert Hub
* **URL**: `/events`
* **Main Table**:
  * Columns: `Event ID`, `Type`, `Risk Score`, `Confidence Level`, `Status`, `Time`.
  * Filter Panels: Date Range, Severity Level, Event Type, Resolution Status.
* **Action Triggers**:
  * **View Event Details**: Navigates user to corresponding `/events/{id}` page.
  * **Escalate**: Triggers `POST /api/v1/events/{id}/escalate`.
  * **Dismiss Alert**: Triggers `POST /api/v1/events/{id}/dismiss` to flag false positive.
  * **Generate Report**: Triggers `POST /api/v1/reports/generate`.

#### Page 6: Event Details Panel
* **URL**: `/events/{id}`
* **Content Sections**:
  * **Event Summary**: Main parameters, telemetry data, and location map.
  * **Lifecycle Timeline**: Chronological event logs.
  * **Evidence Gallery**: Image frame buffers, raw video loops, and captured snapshots.
  * **AI Explanation Dashboard**: Displays feature weights (e.g. Zone violation: 42%, Speed: 25%) mapping output of `GET /api/v1/events/{id}/explanation`.
  * **Entity Path Timeline**: Historical movement profile of coordinates for the anonymous subject.
* **Action Triggers**:
  * **Explain Decision**: Refreshes XAI visualization cards.
  * **Request Identity**: Opens overlay dialog requesting dual-key authorization to reveal subject's identity (`POST /api/v1/identity-requests`).

#### Page 7: Identity Reveal Governance
* **URL**: `/identity-requests`
* **Request Queue Table**:
  * Columns: `Request ID`, `Case Number`, `Requesting Officer`, `Status`, `Created At`.
* **Request Detail View**: Shows justification text, event details, and evidence attachments.
* **Dual Approval Action Triggers**:
  * **Auditor Approve / Reject**: Triggers `POST /api/v1/identity-requests/{id}/auditor-approve` or `/auditor-reject` (Auditor role only).
  * **Admin Approve / Reject**: Triggers `POST /api/v1/identity-requests/{id}/admin-approve` (Admin role only).

#### Page 8: Privacy Center Posture Dashboard
* **URL**: `/privacy`
* **Hero Metrics**: Large digital scores representing Privacy, Trust, Exposure, and Compliance indexes.
* **Interactive Visualization Widgets**:
  * **Privacy Radar Chart**: Slices scores across retention, sharing, and tracking factors.
  * **Exposure Breakdown Bar Chart**: Visualizes potential identity leak paths.
  * **GDPR Retention Impact Graph**: Computes optimization curves.
  * **Spatial Risk Heatmap**: Tracks location risks.
* **Action Triggers**:
  * **Run Assessment**: Triggers `POST /api/v1/privacy/assessment` to calculate values.
  * **Generate Compliance Report**: Triggers `POST /api/v1/reports/compliance`.

#### Page 9: Cryptographic Audit Ledger
* **URL**: `/audit`
* **Purpose**: System-wide ledger listing every single transaction.
* **Table**:
  * Columns: `User`, `Action`, `Target Resource`, `Timestamp`, `Transaction Result`.
  * Filters: Date range picker, Actor username, Action type.
  * Interaction: Click row to reveal raw block details (including current SHA-256 block hash and link to previous block hash).

#### Page 10: Analytics Center Business Intelligence
* **URL**: `/analytics`
* **Interactive Chart Sections**:
  * **Threat Trends Over Time** (interactive line chart)
  * **High-Risk Spatial Areas** (dynamic bar/pie chart)
  * **Camera Sensor Effectiveness Index** (scatter plot)
  * **False Positive Discrepancy Margin** (deviation chart)
  * **GDPR Compliance Index Curves** (area chart)
  * **Anonymized Entity Flow Rate** (Sankey diagram)

#### Page 11: System Simulation Sandbox
* **URL**: `/simulator`
* **Purpose**: Sandbox environment to compare and predict privacy score outcomes based on policy changes.
* **Left Parameter Input Panel**:
  * Camera Count (1-10000 slider)
  * Retention Days (1-3650 slider)
  * Identity Storage (Boolean toggle)
  * System Sensitivity (1-100 slider)
  * Threat Density (1-100 slider)
  * **Action**: `Run Simulation` button triggers `POST /api/v1/simulator/run`.
* **Right Result Comparison Panel**:
  * Sim Output: Privacy, Safety, Trust, False Positives, and Bias indexes.
  * **Comparison Graph**: SVG area chart contrasting Traditional CCTV models vs. BlindWatch AI.

#### Page 12: Reports Archival Hub
* **URL**: `/reports`
* **Table**:
  * Columns: `Report Name`, `Type` (PDF/CSV), `Generated By`, `Date Created`, `Actions`.
* **Action Triggers**:
  * **Download**: Sourced via file attachments.
  * **Share**: Triggers copy to clipboard or internal notification share.
  * **Delete**: Soft deletes the report entry.

#### Page 13: Settings & Workspace Customization
* **URL**: `/settings`
* **Workspace Tabs**:
  * **General Settings**: System variables, localized timezone parameters, and branding.
  * **Security Governance**: Multi-Factor Authentication enforcement rules and encryption schema settings.
  * **Retention Policies**: Configure automatic TTL durations for video logs and telemetry database records.
  * **Notification Rules**: Channel mappings (Email, Slack, SMS alerts).
  * **API Access Keys**: Generate and rotate API credentials.
  * **User Management Tab** (Admin Only): User administration table.

#### Page 14: User Profile & Security Configuration
* **URL**: `/profile`
* **Content Sections**:
  * Personal Details edit form.
  * Active Role & Assigned Permission Keys (e.g. `camera.read`, `identity.reveal`).
  * Activity Log History list.
  * Change Password form & MFA onboarding configuration.

#### Page 15: Public Architecture & Product Landing Page
* **URL**: `/`
* **Sleek Dark Theme Sections**:
  * Hero component with particle background animations.
  * Problem statement (identity theft & privacy degradation in public video monitoring).
  * BlindWatch Solution overview.
  * Interactive Technical Architecture flow.
  * Live Interactive Demo showing blurring shields in action.
  * Dynamic Privacy-vs-Security comparison slider.
  * Pricing tables & contact capture form.

### Global Workspace Components
These components reside globally inside the main layout frame:
1. **Notification Center Drawer**: Real-time alerts feed.
2. **Universal Search Bar**: Search matching records for camera, alert, or audit transaction IDs.
3. **Role Switcher Dropdown (Admin Only)**: Switch current workspace role to Admin, Auditor, or Officer to mock access logs.
4. **Theme Toggle**: Switch between Dark theme and Ultra-dark theme presets.
5. **Activity Log Feed Bar**: Real-time text ticker listing incoming API Gateway queries.
6. **Help Assistant Widget**: Inline chatbot assistant.


