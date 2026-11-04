-- 04_jobs.sql -> jobs.csv   (run with -d msdb)
-- SQL Agent jobs and their steps: what runs, in which order, against which database.
-- The command is cut at 4000 characters so sqlcmd -W can be used; command_truncated = 1 marks it.
-- Line breaks, tabs and the '|' separator are replaced so each step stays on one line.
SET NOCOUNT ON;

SELECT
    j.name                           AS job_name,
    CAST(j.enabled AS tinyint)       AS job_enabled,
    st.step_id,
    st.step_name,
    st.subsystem,
    st.database_name,
    CAST(
        REPLACE(REPLACE(REPLACE(REPLACE(LEFT(st.command, 4000),
            CHAR(13), ' '), CHAR(10), ' '), CHAR(9), ' '), '|', '/')
        AS nvarchar(4000))           AS command,
    CASE WHEN LEN(st.command) > 4000 THEN 1 ELSE 0 END AS command_truncated
FROM msdb.dbo.sysjobs AS j
JOIN msdb.dbo.sysjobsteps AS st
    ON st.job_id = j.job_id
ORDER BY j.name, st.step_id;
