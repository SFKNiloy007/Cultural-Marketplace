-- Migration: Add image support to Product table
-- Run this in pgAdmin or psql to add image column

ALTER TABLE Product 
ADD COLUMN image_url VARCHAR(500);

-- Optional: Set a default placeholder image for existing products
UPDATE Product 
SET image_url = '/static/uploads/placeholder.jpg' 
WHERE image_url IS NULL;
