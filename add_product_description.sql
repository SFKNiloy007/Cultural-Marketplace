-- Migration: Add description field to Product table
-- Run this in pgAdmin or psql to add description column

ALTER TABLE Product 
ADD COLUMN description TEXT;

-- Optional: Set a default description for existing products
UPDATE Product 
SET description = 'No description provided' 
WHERE description IS NULL;
