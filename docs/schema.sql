-- MySQL 8 reference schema (mirrors app/models). Normal workflow: flask db migrate / upgrade.
-- Use this file to review the design or to create tables manually.
SET NAMES utf8mb4;

CREATE TABLE users (
  id INT NOT NULL AUTO_INCREMENT,
  email VARCHAR(254) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(16) NOT NULL DEFAULT 'candidate',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  failed_logins INT NOT NULL DEFAULT 0,
  locked_until DATETIME NULL,
  last_login_at DATETIME NULL,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email),
  CONSTRAINT ck_users_role CHECK (role IN ('candidate','administrator'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE resumes (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  stored_name VARCHAR(64) NOT NULL,
  original_name_enc VARBINARY(1024) NOT NULL,
  sha256 VARCHAR(64) NOT NULL,
  detected_mime VARCHAR(100) NOT NULL,
  size_bytes INT NOT NULL,
  scan_status VARCHAR(16) NOT NULL DEFAULT 'clean',
  wrapped_dek VARBINARY(128) NOT NULL,
  nonce VARBINARY(12) NOT NULL,
  uploaded_at DATETIME NOT NULL,
  delete_after DATETIME NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_resumes_stored_name (stored_name),
  KEY ix_resumes_user_uploaded (user_id, uploaded_at),
  KEY ix_resumes_sha256 (sha256),
  KEY ix_resumes_delete_after (delete_after),
  CONSTRAINT fk_resumes_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT ck_resumes_scan CHECK (scan_status IN ('clean','unscanned'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE candidate_profiles (
  id INT NOT NULL AUTO_INCREMENT,
  resume_id INT NOT NULL,
  user_id INT NOT NULL,
  profile_enc MEDIUMBLOB NOT NULL,
  parser_version VARCHAR(32) NOT NULL,
  resume_quality_score FLOAT NULL,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_profiles_resume (resume_id),
  KEY ix_profiles_user (user_id),
  CONSTRAINT fk_profiles_resume FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE CASCADE,
  CONSTRAINT fk_profiles_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT ck_profiles_quality CHECK (resume_quality_score IS NULL OR resume_quality_score BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE skills (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  category VARCHAR(50) NOT NULL,
  aliases TEXT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_by INT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_skills_name (name),
  KEY ix_skills_category (category),
  CONSTRAINT fk_skills_creator FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE candidate_skills (
  id INT NOT NULL AUTO_INCREMENT,
  profile_id INT NOT NULL,
  skill_id INT NOT NULL,
  source_type VARCHAR(16) NOT NULL,
  confidence FLOAT NOT NULL DEFAULT 1,
  evidence_enc VARBINARY(4096) NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_candidate_skill (profile_id, skill_id),
  KEY ix_cskills_skill (skill_id),
  CONSTRAINT fk_cskills_profile FOREIGN KEY (profile_id) REFERENCES candidate_profiles (id) ON DELETE CASCADE,
  CONSTRAINT fk_cskills_skill FOREIGN KEY (skill_id) REFERENCES skills (id) ON DELETE CASCADE,
  CONSTRAINT ck_cskill_source CHECK (source_type IN ('explicit','inferred')),
  CONSTRAINT ck_cskill_conf CHECK (confidence BETWEEN 0 AND 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE job_descriptions (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  title VARCHAR(200) NOT NULL,
  organization VARCHAR(200) NULL,
  text_enc MEDIUMBLOB NOT NULL,
  is_public TINYINT(1) NOT NULL DEFAULT 0,
  status VARCHAR(10) NOT NULL DEFAULT 'open',
  threshold INT NOT NULL DEFAULT 60,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  KEY ix_jobs_user_created (user_id, created_at),
  KEY ix_jobs_public (is_public, status),
  CONSTRAINT ck_jobs_status CHECK (status IN ('open','closed')),
  CONSTRAINT ck_jobs_threshold CHECK (threshold BETWEEN 0 AND 100),
  CONSTRAINT fk_jobs_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE job_requirements (
  id INT NOT NULL AUTO_INCREMENT,
  job_id INT NOT NULL,
  skill_id INT NULL,
  requirement_text VARCHAR(500) NOT NULL,
  kind VARCHAR(24) NOT NULL,
  strength VARCHAR(12) NOT NULL,
  evidence_span VARCHAR(500) NULL,
  PRIMARY KEY (id),
  KEY ix_jobreq_job (job_id),
  KEY ix_jobreq_skill (skill_id),
  CONSTRAINT fk_jobreq_job FOREIGN KEY (job_id) REFERENCES job_descriptions (id) ON DELETE CASCADE,
  CONSTRAINT fk_jobreq_skill FOREIGN KEY (skill_id) REFERENCES skills (id) ON DELETE SET NULL,
  CONSTRAINT ck_jobreq_strength CHECK (strength IN ('mandatory','preferred','optional')),
  CONSTRAINT ck_jobreq_kind CHECK (kind IN ('skill','tool','qualification','experience','certification','responsibility','domain'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE assessments (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  profile_id INT NOT NULL,
  job_id INT NOT NULL,
  final_score FLOAT NOT NULL,
  weights_used JSON NOT NULL,
  model_version VARCHAR(96) NOT NULL,
  meta JSON NULL,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  KEY ix_assessments_user_created (user_id, created_at),
  KEY ix_assessments_profile (profile_id),
  KEY ix_assessments_job (job_id),
  CONSTRAINT fk_assess_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_assess_profile FOREIGN KEY (profile_id) REFERENCES candidate_profiles (id) ON DELETE CASCADE,
  CONSTRAINT fk_assess_job FOREIGN KEY (job_id) REFERENCES job_descriptions (id) ON DELETE CASCADE,
  CONSTRAINT ck_assessment_score CHECK (final_score BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE assessment_details (
  id INT NOT NULL AUTO_INCREMENT,
  assessment_id INT NOT NULL,
  component VARCHAR(40) NOT NULL,
  score FLOAT NOT NULL,
  weight FLOAT NOT NULL,
  contribution FLOAT NOT NULL,
  explanation JSON NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_detail_component (assessment_id, component),
  CONSTRAINT fk_detail_assessment FOREIGN KEY (assessment_id) REFERENCES assessments (id) ON DELETE CASCADE,
  CONSTRAINT ck_detail_score CHECK (score BETWEEN 0 AND 100),
  CONSTRAINT ck_detail_weight CHECK (weight BETWEEN 0 AND 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE recommendations (
  id INT NOT NULL AUTO_INCREMENT,
  assessment_id INT NOT NULL,
  role_name VARCHAR(100) NOT NULL,
  `rank` INT NOT NULL,
  fit_score FLOAT NOT NULL DEFAULT 0,
  evidence_level VARCHAR(16) NOT NULL DEFAULT 'emerging',
  matching_skills JSON NULL,
  missing_skills JSON NULL,
  suggested_certs JSON NULL,
  roadmap JSON NULL,
  PRIMARY KEY (id),
  KEY ix_reco_assessment_rank (assessment_id, `rank`),
  CONSTRAINT fk_reco_assessment FOREIGN KEY (assessment_id) REFERENCES assessments (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE audit_logs (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id INT NULL,
  action VARCHAR(64) NOT NULL,
  resource_type VARCHAR(32) NULL,
  resource_id INT NULL,
  ip_hash VARCHAR(32) NOT NULL DEFAULT '',
  outcome VARCHAR(16) NOT NULL,
  detail VARCHAR(255) NOT NULL DEFAULT '',
  prev_hash VARCHAR(64) NOT NULL,
  row_hash VARCHAR(64) NOT NULL,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  KEY ix_audit_action (action),
  KEY ix_audit_user_created (user_id, created_at),
  KEY ix_audit_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
