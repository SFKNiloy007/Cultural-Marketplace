-- Migration: add_complaint.sql
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema='public' AND table_name='complaint'
    ) THEN
        CREATE TABLE Complaint (
            complaint_id SERIAL PRIMARY KEY,
            order_id INT NOT NULL REFERENCES "Order"(order_id) ON DELETE CASCADE,
            customer_id INT NOT NULL REFERENCES Customer(customer_id) ON DELETE RESTRICT,
            type VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        );
        CREATE INDEX idx_complaint_customer ON Complaint(customer_id);
        CREATE INDEX idx_complaint_order ON Complaint(order_id);
        CREATE INDEX idx_complaint_status ON Complaint(status);
    END IF;
END $$;