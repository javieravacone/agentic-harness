-- 05_dynamic_sql.sql -> dynamic_sql.csv
-- Modules whose dependencies the catalog cannot see: dynamic SQL and pass-through queries.
-- A flag means "review manually", not "broken". EXEC @rc = proc is not flagged on purpose.
SET NOCOUNT ON;

SELECT
    DB_NAME()                AS database_name,
    s.name                   AS schema_name,
    o.name                   AS object_name,
    CASE WHEN UPPER(m.definition) LIKE '%SP[_]EXECUTESQL%' THEN 1 ELSE 0 END AS uses_sp_executesql,
    CASE WHEN UPPER(m.definition) LIKE '%EXEC(%'
           OR UPPER(m.definition) LIKE '%EXEC (%'
           OR UPPER(m.definition) LIKE '%EXECUTE(%'
           OR UPPER(m.definition) LIKE '%EXECUTE (%' THEN 1 ELSE 0 END AS uses_exec_string,
    CASE WHEN UPPER(m.definition) LIKE '%OPENQUERY%'
           OR UPPER(m.definition) LIKE '%OPENROWSET%'
           OR UPPER(m.definition) LIKE '%OPENDATASOURCE%' THEN 1 ELSE 0 END AS uses_openquery
FROM sys.sql_modules AS m
JOIN sys.objects AS o
    ON o.object_id = m.object_id
JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
WHERE o.is_ms_shipped = 0
  AND (
        UPPER(m.definition) LIKE '%SP[_]EXECUTESQL%'
     OR UPPER(m.definition) LIKE '%EXEC(%'
     OR UPPER(m.definition) LIKE '%EXEC (%'
     OR UPPER(m.definition) LIKE '%EXECUTE(%'
     OR UPPER(m.definition) LIKE '%EXECUTE (%'
     OR UPPER(m.definition) LIKE '%OPENQUERY%'
     OR UPPER(m.definition) LIKE '%OPENROWSET%'
     OR UPPER(m.definition) LIKE '%OPENDATASOURCE%'
  )
ORDER BY s.name, o.name;
