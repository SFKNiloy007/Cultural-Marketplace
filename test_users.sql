-- TEST USERS FOR ARTISAN E-MARKETPLACE
-- Run this after creating the main schema.sql tables

-- ==================== PASSWORD HASHES ====================
-- All passwords are hashed with bcrypt
-- Plain text passwords:
--   12345 (for all test users for easy testing)

-- ==================== CREATE TEST USERS ====================

-- 1. Test Artisan User
INSERT INTO "User" (email, password_hash, is_active)
VALUES ('test.artisan@uni.edu', '$2b$12$mNbb9QBzG2bb/Cvq5/i8vuOHC.ydYMxOrAn4xR.sbrUTEmindjZDa', TRUE)
ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash;

-- Create Artisan profile (using the user_id as artisan_id)
INSERT INTO Artisan (artisan_id, village_origin, digital_literacy_level)
SELECT user_id, 'Tangail', 2
FROM "User" 
WHERE email = 'test.artisan@uni.edu'
ON CONFLICT (artisan_id) DO NOTHING;

-- Create Digital Wallet for Artisan
INSERT INTO DigitalWallet (artisan_id, current_balance, last_payout_date)
SELECT user_id, 0.00, NULL
FROM "User" 
WHERE email = 'test.artisan@uni.edu'
ON CONFLICT (artisan_id) DO NOTHING;

-- 2. Test Customer/Buyer User
INSERT INTO "User" (email, password_hash, is_active)
VALUES ('test.buyer@uni.edu', '$2b$12$UMURwK1RAWqTvDiUYrDyHOZY1U1LAW74IukTPlDYQkL/NLTHOni9.', TRUE)
ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash;

-- Create Customer profile
INSERT INTO Customer (customer_id, shipping_address)
SELECT user_id, '123 University Avenue, Dhaka, Bangladesh'
FROM "User" 
WHERE email = 'test.buyer@uni.edu'
ON CONFLICT (customer_id) DO NOTHING;

-- 3. Test Admin User (admin can be just a User without Artisan/Customer profile)
INSERT INTO "User" (email, password_hash, is_active)
VALUES ('admin@marketplace.com', '$2b$12$cYhTEtxX3X2pRj7STCwFpO2RhxJDPrXnLGPQh9r/IaaR4m2Srwesi', TRUE)
ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash;

-- ==================== SAMPLE PRODUCTS ====================

-- Add some sample products from the artisan
INSERT INTO Product (artisan_id, name, price, stock_quantity, cultural_motif)
SELECT 
    user_id,
    'Handwoven Nakshi Kantha',
    2500.00,
    10,
    'Nayantara'
FROM "User" 
WHERE email = 'test.artisan@uni.edu';

INSERT INTO Product (artisan_id, name, price, stock_quantity, cultural_motif)
SELECT 
    user_id,
    'Traditional Jamdani Saree',
    8500.00,
    5,
    'Paisley'
FROM "User" 
WHERE email = 'test.artisan@uni.edu';

INSERT INTO Product (artisan_id, name, price, stock_quantity, cultural_motif)
SELECT 
    user_id,
    'Clay Pottery Set',
    1200.00,
    15,
    'Traditional'
FROM "User" 
WHERE email = 'test.artisan@uni.edu';

-- ==================== VERIFICATION ====================

-- Check that users were created successfully
SELECT 
    u.user_id,
    u.email,
    CASE 
        WHEN a.artisan_id IS NOT NULL THEN 'Artisan'
        WHEN c.customer_id IS NOT NULL THEN 'Customer'
        ELSE 'Admin/Basic User'
    END as user_type
FROM "User" u
LEFT JOIN Artisan a ON u.user_id = a.artisan_id
LEFT JOIN Customer c ON u.user_id = c.customer_id
WHERE u.email IN ('test.artisan@uni.edu', 'test.buyer@uni.edu', 'admin@marketplace.com');

-- Check products
SELECT p.product_id, p.name, p.price, p.stock_quantity, u.email as artisan_email
FROM Product p
JOIN "User" u ON p.artisan_id = u.user_id;
