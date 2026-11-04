-- 01_objects.sql -> objects.csv
-- Every user object that can take part in lineage. Read-only: catalog metadata only.
SET NOCOUNT ON;

SELECT
    DB_NAME()                               AS database_name,
    s.name                                  AS schema_name,
    o.name                                  AS object_name,
    RTRIM(o.type)                           AS object_type,
    o.type_desc                             AS type_desc,
    CONVERT(varchar(19), o.modify_date, 126) AS modify_date
FROM sys.objects AS o
JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
WHERE o.is_ms_shipped = 0
  AND o.type IN ('U', 'V', 'P', 'FN', 'IF', 'TF', 'TR', 'SN')
ORDER BY s.name, o.name;
