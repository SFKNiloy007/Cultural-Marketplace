# Cultural Artisan E-Marketplace System

## Mini Project Report

---

## 1. TITLE PAGE

**Project Title:** Cultural Artisan E-Marketplace System

**Student Name:** [Your Name]  
**Student ID:** [Your ID]

**Course Name:** Database Management Systems  
**Course Code:** CSE 347

**Instructor Name:** [Instructor Name]

**Department:** Computer Science and Engineering  
**University:** East West University

**Submission Date:** December 13, 2025

---

## 2. INTRODUCTION

The Cultural Artisan E-Marketplace is a web-based platform designed to connect local artisans with buyers through a digital marketplace. The system addresses the growing need for artisans to showcase and sell their traditional handicraft products in the digital economy while preserving cultural heritage.

The platform serves three distinct user types: **Buyers** who can browse and purchase artisan products, **Artisans** who can list and manage their products while tracking orders and payments, and **Administrators** who oversee platform operations including user verification and transaction monitoring.

**Main Objectives:**

- Provide a secure, user-friendly marketplace for cultural artisan products
- Enable artisans to manage their digital storefronts independently
- Facilitate transparent transactions with order tracking and payment history
- Implement robust admin controls for platform integrity and user verification

---

## 3. PROBLEM STATEMENT

Local artisans face significant challenges in reaching customers beyond their immediate geographical area. Traditional brick-and-mortar stores limit market reach, while existing generic e-commerce platforms lack features specific to artisan businesses such as cultural motif categorization, commission-based payment structures, and verification systems for authentic artisans.

**Key Problems Addressed:**

1. Limited market access for traditional artisans
2. Lack of specialized platforms for cultural handicraft products
3. Need for transparent commission-based payment systems
4. Requirement for artisan verification to ensure product authenticity
5. Insufficient order tracking and shipment management for handmade products

---

## 4. SYSTEM REQUIREMENTS

### 4.1 Functional Requirements

**For Buyers:**

- Browse products by cultural motifs and artisan profiles
- Search and filter product listings
- Purchase products with multiple payment methods (COD, bKash, Nagad, Rocket, Credit/Debit Card)
- Track order status and shipment details
- View payment and purchase history
- Rate products and artisans
- File complaints regarding orders

**For Artisans:**

- Register and create seller profiles (pending admin verification)
- Add, edit, and delete product listings with images
- Manage inventory and stock quantities
- View and manage customer orders
- Dispatch orders with courier service integration
- Track sales statistics and revenue
- Access digital wallet with transaction history
- Request payouts (15% commission deducted)

**For Administrators:**

- Verify or reject new artisan registrations
- Manage user accounts (activate/suspend)
- Monitor all transactions and generate audit logs
- View payout ledger and financial overviews
- Access seller financial details
- Oversee platform statistics

### 4.2 Non-Functional Requirements

**Security:**

- JWT-based authentication and authorization
- Bcrypt password hashing
- Role-based access control (RBAC)
- Secure API endpoints with token validation

**Performance:**

- Fast page load times with optimized database queries
- Responsive design for mobile and desktop devices
- Efficient image handling (max 5MB uploads)

**Scalability:**

- PostgreSQL database for handling growing user base
- Cloud deployment on Render platform
- RESTful API architecture

**Usability:**

- Intuitive user interface with Tailwind CSS
- Clear navigation between different user roles
- Mobile-responsive design (supports 375px-414px viewports)

**Reliability:**

- Database connection pooling with automatic reconnection
- Error handling with specific user-facing messages
- Idempotent database migrations

---

## 5. SYSTEM ANALYSIS

### 5.1 Use Case Diagram

**Actors:**

- Buyer
- Artisan
- Admin

**Use Cases:**

- Browse Products
- Purchase Product
- Track Order
- Register as Artisan
- Manage Products
- Process Orders
- Verify Artisans
- Monitor Transactions

### 5.2 Entity Relationship (ER) Diagram

**Main Entities:**

- User (user_id, email, password_hash, is_active)
- Artisan (artisan_id, nid, phone, is_verified)
- Customer (customer_id, phone)
- Product (product_id, name, price, stock_quantity, cultural_motif, artisan_id, image_url, description)
- Order (order_id, customer_id, order_date, status, total_amount)
- OrderItem (item_id, order_id, product_id, quantity, price)
- Shipment (shipment_id, order_id, courier_service, tracking_number, shipped_date, delivery_date)
- Transaction (transaction_id, order_id, amount, commission, payment_method, transaction_date)
- DigitalWallet (wallet_id, artisan_id, balance)
- Rating (rating_id, product_id, customer_id, rating_value, review_text)

**Relationships:**

- One Artisan has many Products
- One Customer places many Orders
- One Order contains many OrderItems
- One Order has one Shipment
- One Order generates one Transaction
- One Artisan has one DigitalWallet

---

## 6. SYSTEM DESIGN

### 6.1 Database Design

**Normalization:** The database follows **Third Normal Form (3NF)** to eliminate redundancy and ensure data integrity.

**Key Tables:**

**1. User Table**

```sql
CREATE TABLE "User" (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**2. Product Table**

```sql
CREATE TABLE Product (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    cultural_motif VARCHAR(100),
    artisan_id INT REFERENCES Artisan(artisan_id) ON DELETE CASCADE,
    image_url VARCHAR(500),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**3. Order Table**

```sql
CREATE TABLE "Order" (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES Customer(customer_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Pending Shipment',
    total_amount DECIMAL(10,2) NOT NULL
);
```

**4. OrderItem Table**

```sql
CREATE TABLE OrderItem (
    item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES "Order"(order_id) ON DELETE CASCADE,
    product_id INT REFERENCES Product(product_id),
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL
);
```

**5. Shipment Table**

```sql
CREATE TABLE Shipment (
    shipment_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES "Order"(order_id) ON DELETE CASCADE,
    courier_service VARCHAR(100),
    tracking_number VARCHAR(100),
    shipped_date TIMESTAMP,
    delivery_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Pending'
);
```

**6. Transaction Table**

```sql
CREATE TABLE Transaction (
    transaction_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES "Order"(order_id),
    amount DECIMAL(10,2) NOT NULL,
    commission DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**7. DigitalWallet Table**

```sql
CREATE TABLE DigitalWallet (
    wallet_id SERIAL PRIMARY KEY,
    artisan_id INT REFERENCES Artisan(artisan_id) ON DELETE CASCADE,
    balance DECIMAL(10,2) DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Primary Keys:** Each table has a surrogate key (auto-incrementing integer) serving as the primary key.

**Foreign Keys:** Enforce referential integrity between related tables (e.g., Order → Customer, Product → Artisan).

**Indexes:** Created on foreign key columns for improved query performance.

### 6.2 System Architecture

**Architecture Pattern:** Three-Tier Architecture

**Tier 1 - Presentation Layer (Frontend):**

- HTML5, CSS3 (Tailwind CSS)
- Vanilla JavaScript (ES6+)
- Responsive design for mobile and desktop

**Tier 2 - Application Layer (Backend):**

- FastAPI (Python web framework)
- RESTful API endpoints
- JWT authentication middleware
- Business logic and validation

**Tier 3 - Data Layer:**

- PostgreSQL database
- SQLAlchemy ORM for database operations
- Connection pooling for performance

**System Flow:**

```
User (Browser)
    ↓
Frontend (HTML/JS)
    ↓ HTTP Requests (JSON)
Backend API (FastAPI)
    ↓ SQL Queries
PostgreSQL Database
```

**Deployment Architecture:**

- Frontend: Hosted on GitHub Pages or Render static files
- Backend: Deployed on Render (cloud platform)
- Database: Managed PostgreSQL on Render
- Communication: HTTPS with CORS enabled

---

## 7. IMPLEMENTATION

### 7.1 Technologies Used

**Backend:**

- **Python 3.11+** - Programming language
- **FastAPI** - Modern web framework for building APIs
- **Uvicorn** - ASGI server
- **SQLAlchemy** - SQL toolkit and ORM
- **psycopg2** - PostgreSQL adapter
- **python-jose** - JWT token generation and validation
- **bcrypt** - Password hashing
- **python-multipart** - File upload handling

**Frontend:**

- **HTML5** - Markup language
- **Tailwind CSS** - Utility-first CSS framework
- **JavaScript (ES6+)** - Client-side scripting

**Database:**

- **PostgreSQL 14+** - Relational database management system

**Deployment:**

- **Render** - Cloud platform for backend and database
- **GitHub** - Version control and repository hosting
- **GitHub Pages** - Static site hosting (optional)

### 7.2 Key Implementation Features

**1. Authentication System**

```python
# JWT Token Creation
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=60))
    to_encode.update({"exp": expire})
    encoded_jwt = jose_jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Password Verification
def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'),
                          hashed_password.encode('utf-8'))
```

**2. Product Purchase Transaction**

```python
@app.post("/buyer/purchase")
async def buyer_purchase(
    purchase: BuyerPurchaseRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check stock availability
    product_check = db.execute(text(
        "SELECT stock_quantity, price FROM Product WHERE product_id = :pid"
    ), {"pid": purchase.product_id}).fetchone()

    if product_check[0] < purchase.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    # Calculate total amount
    total_amount = product_check[1] * purchase.quantity

    # Create order
    order_result = db.execute(text(
        """INSERT INTO "Order" (customer_id, total_amount, status)
           VALUES (:cid, :amt, 'Pending Shipment') RETURNING order_id"""
    ), {"cid": customer_id, "amt": total_amount})

    # Update stock
    db.execute(text(
        "UPDATE Product SET stock_quantity = stock_quantity - :qty WHERE product_id = :pid"
    ), {"qty": purchase.quantity, "pid": purchase.product_id})

    db.commit()
```

**3. Commission Calculation for Artisans**

```python
MARKETPLACE_COMMISSION_RATE = 0.15

# Calculate commission on sale
commission_amount = order_amount * MARKETPLACE_COMMISSION_RATE
artisan_payout = order_amount - commission_amount

# Update artisan wallet
db.execute(text(
    "UPDATE DigitalWallet SET balance = balance + :payout WHERE artisan_id = :aid"
), {"payout": artisan_payout, "aid": artisan_id})
```

**4. Dynamic Product Display (Frontend)**

```javascript
async function loadProducts() {
  const response = await fetch(`${API_BASE_URL}/products`);
  const products = await response.json();

  const container = document.getElementById("productsList");
  container.innerHTML = products
    .map(
      (product) => `
        <div class="bg-white p-6 rounded-xl shadow-md">
            <img src="${API_BASE_URL}${product.image_url}" 
                 class="w-full h-48 object-cover rounded-lg mb-4">
            <h3 class="text-lg font-bold">${product.name}</h3>
            <p class="text-gray-600">Motif: ${product.cultural_motif}</p>
            <p class="text-2xl font-bold text-green-600">Tk ${product.price}</p>
            <button onclick="openPurchaseModal(${product.product_id})" 
                    class="bg-blue-600 text-white px-4 py-2 rounded-lg">
                Buy Now
            </button>
        </div>
    `
    )
    .join("");
}
```

### 7.3 Screenshots

**Figure 1: Login Page with Role Selection**

- Split-screen design with background image
- Three role cards: Buyer, Artisan, Admin
- Registration option for new users

**Figure 2: Buyer Dashboard - Product Browsing**

- Grid layout of available products
- Product cards showing image, name, motif, price, stock
- Search functionality
- Responsive design for mobile devices

**Figure 3: Purchase Modal**

- Product details confirmation
- Quantity selector
- Payment method dropdown (COD, bKash, Nagad, Rocket, Credit/Debit Card)
- Total amount calculation

**Figure 4: Buyer Order Tracking**

- Order ID input and tracking number search
- Timeline visualization showing order status
- Shipment details with courier information

**Figure 5: Artisan Dashboard - Product Management**

- Statistics overview (Total Products, Sales, Orders)
- Product listing with edit/delete options
- Add new product form with image upload

**Figure 6: Artisan Order Management**

- Customer order list with status badges
- Dispatch order functionality
- Courier service selection

**Figure 7: Artisan Digital Wallet**

- Balance display
- Transaction history table
- Commission breakdown (15% marketplace fee)
- Payout request button

**Figure 8: Admin Dashboard - User Verification**

- Pending artisan registrations
- Verify/Reject actions
- User details display with NID and phone

**Figure 9: Admin Audit Logs**

- Comprehensive transaction list
- Filter options by date
- Order and payment details

**Figure 10: Admin Seller Financial Overview**

- Individual seller statistics
- Total sales and commission paid
- Transaction breakdown table

### 7.4 Database Migration System

Idempotent migrations ensure safe redeployment:

```sql
-- Migration: add_orderitem_and_shipment.sql
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_name = 'orderitem') THEN
        CREATE TABLE OrderItem (
            item_id SERIAL PRIMARY KEY,
            order_id INT REFERENCES "Order"(order_id) ON DELETE CASCADE,
            product_id INT REFERENCES Product(product_id),
            quantity INT NOT NULL,
            price DECIMAL(10,2) NOT NULL
        );
        CREATE INDEX idx_orderitem_order ON OrderItem(order_id);
        CREATE INDEX idx_orderitem_product ON OrderItem(product_id);
    END IF;
END $$;
```

---

## 8. CONCLUSION

The Cultural Artisan E-Marketplace successfully addresses the digital transformation needs of traditional artisans by providing a comprehensive, secure, and user-friendly platform. The system implements robust database design following normalization principles, secure authentication mechanisms, and role-based access control to ensure data integrity and user privacy.

**Key Achievements:**

1. Developed a fully functional three-tier web application with separate interfaces for buyers, artisans, and administrators
2. Implemented secure transaction processing with commission-based payment structure
3. Created an intuitive product management system with image upload capabilities
4. Established comprehensive order tracking and shipment management
5. Deployed the application on cloud infrastructure (Render) with PostgreSQL database
6. Achieved mobile responsiveness across all user interfaces

**Project Impact:**

- Provides market access for local artisans beyond geographical limitations
- Facilitates transparent transactions with detailed audit trails
- Ensures artisan authenticity through admin verification process
- Supports multiple payment methods including Cash on Delivery

### 8.1 Future Improvements

**Potential Enhancements:**

1. **Advanced Search & Filtering:** Implement full-text search, price range filters, and category-based browsing
2. **Real-time Notifications:** WebSocket integration for instant order updates and messages
3. **Rating & Review System:** Expand buyer feedback mechanisms with photo reviews
4. **Analytics Dashboard:** Advanced data visualization for sales trends and customer behavior
5. **Mobile Application:** Native iOS/Android apps for improved user experience
6. **Payment Gateway Integration:** Direct integration with bKash, Nagad APIs for automated payment processing
7. **Multi-language Support:** Bengali and English language options
8. **Social Features:** Artisan profiles with stories, workshop tours, and social sharing
9. **Recommendation Engine:** AI-powered product recommendations based on browsing history
10. **Inventory Alerts:** Automated low-stock notifications for artisans

---

## 9. REFERENCES

**Books & Documentation:**

1. Elmasri, R., & Navathe, S. B. (2015). _Fundamentals of Database Systems_ (7th ed.). Pearson.
2. FastAPI Documentation. (2024). Retrieved from https://fastapi.tiangolo.com/
3. PostgreSQL Documentation. (2024). Retrieved from https://www.postgresql.org/docs/

**Web Resources:**

1. Tailwind CSS. (2024). _Utility-First CSS Framework_. https://tailwindcss.com/
2. SQLAlchemy Documentation. https://docs.sqlalchemy.org/
3. JWT Introduction. https://jwt.io/introduction
4. Render Documentation. https://render.com/docs

**Tutorials & Learning Resources:**

1. MDN Web Docs - JavaScript Guide. https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide
2. W3Schools - HTML/CSS Tutorials. https://www.w3schools.com/
3. Real Python - FastAPI Tutorials. https://realpython.com/

**Tools & Platforms:**

1. GitHub - Version Control System. https://github.com/
2. Render - Cloud Application Platform. https://render.com/
3. VS Code - Code Editor. https://code.visualstudio.com/

---

**End of Report**

---

## APPENDIX

### A. System Installation Guide

**Prerequisites:**

- Python 3.11 or higher
- PostgreSQL 14 or higher
- Git

**Local Setup:**

```bash
# Clone repository
git clone https://github.com/SFKNiloy007/Cultural-Marketplace.git
cd Cultural-Marketplace

# Install dependencies
pip install -r requirements.txt

# Create .env file with database connection
DATABASE_URL=postgresql://user:password@localhost:5432/artisan_db

# Initialize database
curl -X POST http://localhost:8000/init-database-secret-endpoint-xyz

# Run server
python -m uvicorn main:app --reload
```

### B. API Endpoints Summary

**Authentication:**

- POST `/token` - Login and get JWT token
- POST `/register` - Register new user
- GET `/users/me` - Get current user info

**Products:**

- GET `/products` - List all products
- POST `/products` - Create product (Artisan)
- PUT `/products/{id}` - Update product
- DELETE `/products/{id}` - Delete product

**Buyer Endpoints:**

- POST `/buyer/purchase` - Purchase product
- GET `/buyer/orders` - List orders
- GET `/buyer/track/{order_id}` - Track order
- GET `/buyer/payment-history` - View payment history

**Artisan Endpoints:**

- GET `/artisan/products` - List artisan's products
- GET `/artisan/orders` - View customer orders
- POST `/artisan/orders/{id}/ship` - Dispatch order
- GET `/artisan/wallet` - View wallet balance
- GET `/artisan/stats` - Dashboard statistics

**Admin Endpoints:**

- GET `/admin/users/pending` - Pending verifications
- POST `/admin/user/{id}/verify` - Verify user
- GET `/admin/audit-logs` - Transaction logs
- GET `/admin/payout-ledger` - Payout records
- GET `/admin/complaints` - List buyer complaints
- POST `/admin/complaints/{id}/status` - Update complaint status
