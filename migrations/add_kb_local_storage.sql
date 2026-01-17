-- Add local storage columns to kb_files table
ALTER TABLE kb_files 
ADD COLUMN local_file_path VARCHAR,
ADD COLUMN file_content TEXT;
