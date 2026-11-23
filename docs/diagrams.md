# Diagrams (updated for the final design)
The architecture, DFD, use-case, class, sequence, activity and deployment diagrams from Phase 2 remain valid. This file adds the final ER diagram.
Render the Mermaid blocks at mermaid.live, or in VS Code with a Mermaid extension, and export PNG or SVG for the thesis.

```mermaid
erDiagram
  users ||--o{ resumes : uploads
  users ||--o{ job_descriptions : creates
  users ||--o{ assessments : owns
  resumes ||--o| candidate_profiles : parsed_into
  candidate_profiles ||--o{ candidate_skills : has
  skills ||--o{ candidate_skills : classifies
  skills ||--o{ job_requirements : referenced_by
  job_descriptions ||--o{ job_requirements : contains
  candidate_profiles ||--o{ assessments : evaluated_in
  job_descriptions ||--o{ assessments : evaluated_against
  assessments ||--o{ assessment_details : broken_into
  assessments ||--o{ recommendations : yields
  users {
    int id PK
    string email UK
    string password_hash
    string role
    int failed_logins
    datetime locked_until
  }
  resumes {
    int id PK
    int user_id FK
    string stored_name UK
    blob original_name_enc
    string sha256
    string scan_status
    blob wrapped_dek
    blob nonce
    datetime delete_after
  }
  candidate_profiles {
    int id PK
    int resume_id FK
    int user_id FK
    blob profile_enc
    float resume_quality_score
  }
  skills {
    int id PK
    string name UK
    string category
    text aliases
    bool is_active
  }
  candidate_skills {
    int id PK
    int profile_id FK
    int skill_id FK
    string source_type
    float confidence
  }
  job_descriptions {
    int id PK
    int user_id FK
    string title
    blob text_enc
  }
  job_requirements {
    int id PK
    int job_id FK
    int skill_id FK
    string kind
    string strength
  }
  assessments {
    int id PK
    int user_id FK
    int profile_id FK
    int job_id FK
    float final_score
    json weights_used
    string model_version
    json meta
  }
  assessment_details {
    int id PK
    int assessment_id FK
    string component
    float score
    float weight
    float contribution
    json explanation
  }
  recommendations {
    int id PK
    int assessment_id FK
    string role_name
    int rank
    float fit_score
    string evidence_level
    json roadmap
  }
  audit_logs {
    bigint id PK
    int user_id
    string action
    string outcome
    string prev_hash
    string row_hash
  }
```
Note: `audit_logs.user_id` is intentionally not a foreign key, so audit rows are unchanged when an account is erased.
