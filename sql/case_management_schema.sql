-- In Azure SQL (e.g., "amlcases")
CREATE SCHEMA aml AUTHORIZATION dbo;
GO

CREATE TABLE aml.cases (
  case_id       UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
  alert_id      VARCHAR(128) NOT NULL UNIQUE,
  subject_id    VARCHAR(128) NOT NULL,
  typology      VARCHAR(64)  NOT NULL,
  risk_score    FLOAT        NOT NULL,
  status        VARCHAR(20)  NOT NULL DEFAULT 'Open', -- Open|InProgress|Closed
  assigned_to   VARCHAR(256) NULL,    -- UPN or group
  disposition   VARCHAR(50)  NULL,    -- SAR|NotSAR|Escalated|False_Positive
  created_ts    DATETIME2    NOT NULL DEFAULT SYSUTCDATETIME(),
  updated_ts    DATETIME2    NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE aml.case_events (
  event_id    BIGINT IDENTITY(1,1) PRIMARY KEY,
  case_id     UNIQUEIDENTIFIER NOT NULL,
  event_type  VARCHAR(64) NOT NULL,   -- Created|Assignment|Note|Disposition
  details_json NVARCHAR(MAX) NULL,
  created_ts  DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  created_by  VARCHAR(256) NULL,
  CONSTRAINT fk_case FOREIGN KEY (case_id) REFERENCES aml.cases(case_id)
);

CREATE INDEX IX_cases_status ON aml.cases(status);
CREATE INDEX IX_cases_assigned ON aml.cases(assigned_to);
CREATE INDEX IX_cases_disposition ON aml.cases(disposition);
CREATE INDEX IX_case_events_case_id ON aml.case_events(case_id);

-- Sample stored procedures for case management
GO
CREATE PROCEDURE aml.AssignCase
    @case_id UNIQUEIDENTIFIER,
    @assigned_to VARCHAR(256),
    @assigned_by VARCHAR(256)
AS
BEGIN
    UPDATE aml.cases 
    SET assigned_to = @assigned_to, updated_ts = SYSUTCDATETIME()
    WHERE case_id = @case_id;
    
    INSERT INTO aml.case_events (case_id, event_type, details_json, created_by)
    VALUES (@case_id, 'Assignment', 
            JSON_OBJECT('assigned_to', @assigned_to), 
            @assigned_by);
END;
GO

CREATE PROCEDURE aml.AddCaseNote
    @case_id UNIQUEIDENTIFIER,
    @note NVARCHAR(MAX),
    @created_by VARCHAR(256)
AS
BEGIN
    INSERT INTO aml.case_events (case_id, event_type, details_json, created_by)
    VALUES (@case_id, 'Note', 
            JSON_OBJECT('note', @note), 
            @created_by);
    
    UPDATE aml.cases 
    SET updated_ts = SYSUTCDATETIME()
    WHERE case_id = @case_id;
END;
GO

CREATE PROCEDURE aml.DispositionCase
    @case_id UNIQUEIDENTIFIER,
    @disposition VARCHAR(50),
    @reason NVARCHAR(MAX),
    @disposed_by VARCHAR(256)
AS
BEGIN
    UPDATE aml.cases 
    SET disposition = @disposition, 
        status = 'Closed', 
        updated_ts = SYSUTCDATETIME()
    WHERE case_id = @case_id;
    
    INSERT INTO aml.case_events (case_id, event_type, details_json, created_by)
    VALUES (@case_id, 'Disposition', 
            JSON_OBJECT('disposition', @disposition, 'reason', @reason), 
            @disposed_by);
END;
GO