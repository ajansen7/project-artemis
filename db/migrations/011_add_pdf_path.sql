-- Add resume_pdf_path to track the generated PDF location for each application
ALTER TABLE applications ADD COLUMN IF NOT EXISTS resume_pdf_path TEXT;
