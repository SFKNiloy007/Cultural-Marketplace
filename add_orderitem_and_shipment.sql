-- Migration: Add missing tables OrderItem and Shipment
-- Safe to run multiple times; will skip if already exists

-- Create OrderItem table if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'orderitem' AND table_schema = 'public'
    ) THEN
        CREATE TABLE OrderItem (
            order_item_id SERIAL PRIMARY KEY,
            order_id INT NOT NULL REFERENCES "Order"(order_id) ON DELETE CASCADE,
            product_id INT NOT NULL REFERENCES Product(product_id) ON DELETE RESTRICT,
            quantity INT NOT NULL CHECK (quantity > 0),
            price DECIMAL(10, 2) NOT NULL
        );
        -- Helpful index for joins
        CREATE INDEX idx_orderitem_order_id ON OrderItem(order_id);
        CREATE INDEX idx_orderitem_product_id ON OrderItem(product_id);
    END IF;
END$$;

-- Create Shipment table if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'shipment' AND table_schema = 'public'
    ) THEN
        CREATE TABLE Shipment (
            shipment_id SERIAL PRIMARY KEY,
            order_id INT UNIQUE NOT NULL REFERENCES "Order"(order_id) ON DELETE CASCADE,
            courier_service VARCHAR(100),
            shipped_date TIMESTAMP WITHOUT TIME ZONE,
            tracking_number VARCHAR(100)
        );
        CREATE INDEX idx_shipment_order_id ON Shipment(order_id);
        CREATE INDEX idx_shipment_tracking_number ON Shipment(tracking_number);
    END IF;
END$$;