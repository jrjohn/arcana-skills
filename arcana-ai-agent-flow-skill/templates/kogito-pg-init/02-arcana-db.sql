-- Separate database for the arcana-cloud-rust read-API's own tables
-- (users / oauth / audit). Kept apart from the engine's `workflow` DB and the
-- Data Index's `dataindex` DB so each component owns its schema.
CREATE DATABASE arcana;
