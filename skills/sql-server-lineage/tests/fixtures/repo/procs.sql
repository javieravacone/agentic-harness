-- Deployment scripts kept in the repository.
CREATE OR ALTER PROCEDURE [dw].[LoadPositions]
AS
BEGIN
    SELECT 1;
END
GO

ALTER PROC dw.CalcPnL AS SELECT 1;
GO

CREATE PROCEDURE dw.Legacy
AS SELECT 1;
GO

CREATE TABLE dw.Positions (Id int NOT NULL);
