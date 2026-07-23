CREATE TABLE IF NOT EXISTS 'wiki data'(
    'ID' INTEGER PRIMARY KEY AUTOINCREMENT,
    'Date' DATE, --YYYY-MM-DD
    'Time' TIME, --HH:MM:SS
    'Page_Titles' TEXT
);

CREATE UNIQUE INDEX uc_time
ON 'wiki data' (DATE, TIME);

-- Code Execution
-- sqlite3 job_data.db < sql_code/table_create.sql