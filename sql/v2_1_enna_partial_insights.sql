-- Enna: correct unknown vs zero in verified Meta Threads post insights.
-- Previous NOT NULL DEFAULT 0 columns made any unreturned metric look like a
-- measured zero. Preserve existing rows, constraints and RLS; only relax
-- missing values in future provider snapshots. SQL NULL means "not returned".
ALTER TABLE public.threads_metrics
    ALTER COLUMN views DROP DEFAULT,
    ALTER COLUMN views DROP NOT NULL,
    ALTER COLUMN likes DROP DEFAULT,
    ALTER COLUMN likes DROP NOT NULL,
    ALTER COLUMN replies DROP DEFAULT,
    ALTER COLUMN replies DROP NOT NULL,
    ALTER COLUMN reposts DROP DEFAULT,
    ALTER COLUMN reposts DROP NOT NULL,
    ALTER COLUMN quotes DROP DEFAULT,
    ALTER COLUMN quotes DROP NOT NULL;
