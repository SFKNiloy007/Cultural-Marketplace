from database import engine
from sqlalchemy import text

create_sql = """
CREATE TABLE IF NOT EXISTS Shipment (
    shipment_id SERIAL PRIMARY KEY,
    order_id INT UNIQUE NOT NULL REFERENCES "Order"(order_id) ON DELETE CASCADE,
    courier_service VARCHAR(100) NOT NULL,
    shipped_date TIMESTAMP NOT NULL,
    tracking_number VARCHAR(64)
);
"""

with engine.connect() as conn:
    conn.execute(text(create_sql))
    conn.commit()
    print("✅ Shipment table ready")
