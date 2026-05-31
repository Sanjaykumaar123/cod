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
