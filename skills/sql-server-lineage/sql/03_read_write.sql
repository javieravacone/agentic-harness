-- 03_read_write.sql -> read_write.csv
-- For every module, which referenced objects it reads (is_selected) and writes (is_updated).
-- sys.dm_sql_referenced_entities raises error 2020 on broken modules, so it runs one module
-- at a time inside TRY/CATCH; a failed module becomes one row with status 'error:<number>'.
SET NOCOUNT ON;

DECLARE @result TABLE (
    database_name            sysname     NOT NULL,
    referencing_schema       sysname     NOT NULL,
    referencing_name         sysname     NOT NULL,
    referenced_server_name   sysname     NULL,
    referenced_database_name sysname     NULL,
    referenced_schema        sysname     NULL,
    referenced_name          sysname     NULL,
    is_selected              tinyint     NULL,
    is_updated               tinyint     NULL,
    status                   varchar(40) NOT NULL
);

DECLARE @schema sysname, @name sysname, @qualified nvarchar(517);

DECLARE modules CURSOR LOCAL FAST_FORWARD FOR
    SELECT s.name, o.name
    FROM sys.objects AS o
    JOIN sys.schemas AS s
        ON s.schema_id = o.schema_id
    WHERE o.is_ms_shipped = 0
      AND o.type IN ('P', 'V', 'FN', 'IF', 'TF', 'TR')
    ORDER BY s.name, o.name;

OPEN modules;
FETCH NEXT FROM modules INTO @schema, @name;

WHILE @@FETCH_STATUS = 0
BEGIN
    SET @qualified = QUOTENAME(@schema) + N'.' + QUOTENAME(@name);

    BEGIN TRY
        INSERT INTO @result
        SELECT
            DB_NAME(),
            @schema,
            @name,
            r.referenced_server_name,
            r.referenced_database_name,
            COALESCE(
                r.referenced_schema_name,
                CASE WHEN r.referenced_database_name IS NULL AND r.referenced_server_name IS NULL
                     THEN OBJECT_SCHEMA_NAME(r.referenced_id) END
            ),
            r.referenced_entity_name,
            MAX(CAST(r.is_selected AS tinyint)),  -- object row and column rows combined
            MAX(CAST(r.is_updated AS tinyint)),
            'ok'
        FROM sys.dm_sql_referenced_entities(@qualified, N'OBJECT') AS r
        GROUP BY
            r.referenced_server_name,
            r.referenced_database_name,
            COALESCE(
                r.referenced_schema_name,
                CASE WHEN r.referenced_database_name IS NULL AND r.referenced_server_name IS NULL
                     THEN OBJECT_SCHEMA_NAME(r.referenced_id) END
            ),
            r.referenced_entity_name;
    END TRY
    BEGIN CATCH
        INSERT INTO @result (database_name, referencing_schema, referencing_name, status)
        VALUES (DB_NAME(), @schema, @name, 'error:' + CAST(ERROR_NUMBER() AS varchar(10)));
    END CATCH;

    FETCH NEXT FROM modules INTO @schema, @name;
END;

CLOSE modules;
DEALLOCATE modules;

SELECT
    database_name,
    referencing_schema,
    referencing_name,
    referenced_server_name,
    referenced_database_name,
    referenced_schema,
    referenced_name,
    is_selected,
    is_updated,
    status
FROM @result
ORDER BY referencing_schema, referencing_name, referenced_schema, referenced_name;
