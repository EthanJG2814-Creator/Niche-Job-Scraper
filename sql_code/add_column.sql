-- ALTER TABLE "wiki data"
-- ADD Network_Performance integer;

ALTER TABLE "HEB DATA"
ADD BANDWIDTH TEXT;

-- sqlite3 job_data.db < sql_code/add_column.sql