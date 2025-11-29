-- DDL SCRIPT FOR LOCAL ARTISAN E-MARKETPLACE
-- DATABASE: PostgreSQL

-- -----------------------------------------------------------
-- 1. USER ACCOUNTS (Parent Class for Authentication)
-- -----------------------------------------------------------
CREATE TABLE "User" (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    registration_date TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- -----------------------------------------------------------
-- 2. SPECIALIZED USERS (Artisan and Customer - Inheritance)
-- -----------------------------------------------------------

CREATE TABLE Artisan (
    artisan_id INT PRIMARY KEY, -- FK to User
    village_origin VARCHAR(100),
    digital_literacy_level INT CHECK (digital_literacy_level BETWEEN 1 AND 3),
    -- Inheritance Foreign Key
    FOREIGN KEY (artisan_id) REFERENCES "User"(user_id) ON DELETE CASCADE
);

CREATE TABLE Customer (
    customer_id INT PRIMARY KEY, -- FK to User
    shipping_address TEXT,
    -- Inheritance Foreign Key
    FOREIGN KEY (customer_id) REFERENCES "User"(user_id) ON DELETE CASCADE
);

-- -----------------------------------------------------------
-- 3. FINANCIAL SYSTEMS (Digital Wallet - 1:1)
-- -----------------------------------------------------------

CREATE TABLE DigitalWallet (
    wallet_id SERIAL PRIMARY KEY,
    artisan_id INT UNIQUE NOT NULL, -- FK to Artisan
    current_balance DECIMAL(12, 2) DEFAULT 0.00,
    last_payout_date DATE,
    -- Foreign Key Constraint
    FOREIGN KEY (artisan_id) REFERENCES Artisan(artisan_id) ON DELETE CASCADE
);

-- -----------------------------------------------------------
-- 4. PRODUCT CATALOG (Inventory Management)
-- -----------------------------------------------------------

CREATE TABLE Product (
    product_id SERIAL PRIMARY KEY,
    artisan_id INT NOT NULL, -- FK to Artisan (Who lists the product)
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    stock_quantity INT NOT NULL CHECK (stock_quantity >= 0), -- CRITICAL for Inventory Lock
    cultural_motif VARCHAR(100), -- E.g., Nayantara, Tater Shari
    
    FOREIGN KEY (artisan_id) REFERENCES Artisan(artisan_id) ON DELETE RESTRICT
);

-- -----------------------------------------------------------
-- 5. ORDERS (The Sales Request)
-- -----------------------------------------------------------

CREATE TABLE "Order" (
    order_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL, -- FK to Customer (Who made the purchase)
    order_date TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) NOT NULL, -- E.g., 'Pending Payment', 'Shipped', 'Delivered'
    tracking_id VARCHAR(50), -- From logistics partner

    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id) ON DELETE RESTRICT
);

-- -----------------------------------------------------------
-- 6. TRANSACTION LOG (Proof of Payment - 1:1 with Order)
-- -----------------------------------------------------------

CREATE TABLE "Transaction" (
    transaction_id VARCHAR(255) PRIMARY KEY, -- Unique ID from bKash/Payment Gateway
    order_id INT UNIQUE NOT NULL, -- FK to Order
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL, -- E.g., 'bKash', 'Card'
    transaction_date TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (order_id) REFERENCES "Order"(order_id) ON DELETE CASCADE
);

-- -----------------------------------------------------------
-- 7. RATING & REVIEW (Accountability)
-- -----------------------------------------------------------

CREATE TABLE Rating (
    rating_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL, -- FK to Customer (Who submitted the rating)
    order_id INT UNIQUE NOT NULL, -- FK to Order (What was rated)
    score INT NOT NULL CHECK (score BETWEEN 1 AND 5),
    review_text TEXT,

    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id) ON DELETE RESTRICT,
    FOREIGN KEY (order_id) REFERENCES "Order"(order_id) ON DELETE CASCADE
);