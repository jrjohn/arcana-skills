-- Separate database for Kogito Data Index (its hibernate tables must not collide
-- with the engine's flyway-managed process_instances tables in the 'workflow' DB).
CREATE DATABASE dataindex;
