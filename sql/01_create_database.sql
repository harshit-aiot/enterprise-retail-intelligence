-- =============================================================================
-- 01_create_database.sql
-- Enterprise Retail Intelligence & Decision Engine
-- Phase 6: MySQL Database
--
-- Creates the enterprise_bi database with proper settings.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS enterprise_bi
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE enterprise_bi;

-- Confirm creation
SELECT
    SCHEMA_NAME           AS `database`,
    DEFAULT_CHARACTER_SET_NAME AS `charset`,
    DEFAULT_COLLATION_NAME      AS `collation`
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME = 'enterprise_bi';
