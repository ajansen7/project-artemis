-- Binary artifact storage: add storage paths for DOCX and PDF
-- Stores Supabase Storage URLs (artifacts/applications/{job-slug}/{file})
-- alongside local filesystem paths in resume_pdf_path for cloud sync.

ALTER TABLE applications ADD COLUMN IF NOT EXISTS resume_docx_path TEXT;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS resume_pdf_path_storage TEXT;
