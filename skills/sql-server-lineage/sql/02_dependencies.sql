-- 02_dependencies.sql -> dependencies.csv
-- Who references whom, for the whole database, at object level.
-- Does not fail on broken objects. Does not see dynamic SQL or temporary tables (see 05).
SET NOCOUNT ON;

SELECT DISTINCT
    DB_NAME()                          AS database_name,
    OBJECT_SCHEMA_NAME(d.referencing_id) AS referencing_schema,
    OBJECT_NAME(d.referencing_id)        AS referencing_name,
    RTRIM(o.type)                      AS referencing_type,
    d.referenced_server_name,
    d.referenced_database_name,
    COALESCE(
        d.referenced_schema_name,
        -- Resolve one-part names only inside this database.
        CASE WHEN d.referenced_database_name IS NULL AND d.referenced_server_name IS NULL
             THEN OBJECT_SCHEMA_NAME(d.referenced_id) END
    )                                  AS referenced_schema,
    d.referenced_entity_name           AS referenced_name,
    CAST(d.is_caller_dependent AS tinyint) AS is_caller_dependent,
    CAST(d.is_ambiguous AS tinyint)        AS is_ambiguous
FROM sys.sql_expression_dependencies AS d
JOIN sys.objects AS o
    ON o.object_id = d.referencing_id
WHERE d.referencing_class = 1   -- objects and columns; DDL triggers are out of scope
  AND o.is_ms_shipped = 0
ORDER BY referencing_schema, referencing_name, referenced_schema, referenced_name;
