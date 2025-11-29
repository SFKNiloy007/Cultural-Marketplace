# Artisan E-Marketplace

A comprehensive e-commerce platform connecting local artisans with buyers, featuring role-based access control, digital wallet management, and secure payment processing.

## 🎨 Project Overview

The Artisan E-Marketplace is a multi-role platform designed to:

- **Connect** local artisans with customers
- **Facilitate** secure transactions with payment gateway integration
- **Provide** transparent commission-based earnings for artisans
- **Enable** order tracking and complaint management
- **Support** admin oversight and audit capabilities

## 🏗️ Architecture

### Frontend (HTML/CSS/JavaScript)

- **login.html** - Role-based login page (Buyer/Artisan/Admin)
- **buyer.html** - Buyer dashboard with product browsing, ordering, and tracking
- **artisan.html** - Artisan dashboard for product management and wallet
- **admin.html** - Admin dashboard for platform management
- Uses Tailwind CSS for styling and React for dynamic UI

### Backend (FastAPI/Python)

- **main.py** - RESTful API with JWT authentication
- **database.py** - PostgreSQL connection management
- **hash.py** - Password hashing utilities

### Database (PostgreSQL)

- **schema.sql** - Complete database schema with tables, indexes, and triggers

## 📋 Features by Role

### 🛍️ Buyer Features

- Browse artisan products with cultural motifs
- Purchase products with quantity selection
- Multiple payment methods (bKash, Nagad, Rocket, Card)
- Order tracking with real-time status
- Payment history and transaction records
- File complaints about orders
- View complaint status

### 🎨 Artisan Features

- List products with price, quantity, and cultural motifs
- Manage inventory (add, edit, delete products)
- Digital wallet showing earnings
- View sales statistics
- Track orders for their products
- See commission breakdown (15% marketplace fee)
- Request payouts

### ⚙️ Admin Features

- Verify/reject artisan registrations
- Suspend artisan accounts
- View all transactions (audit logs)
- Generate transaction reports
- View payout ledger for all artisans
- Monitor platform statistics

## 💳 Payment System

### Transaction Flow

1. Buyer selects product and quantity
2. System calculates total: `Total = Price × Quantity`
3. Generates unique Transaction ID: `{METHOD}-{TIMESTAMP}-{RANDOM}`
4. Processes payment through selected method
5. Updates inventory automatically
6. Records transaction for audit

### Commission Structure

- **Marketplace Commission**: 15% of each sale
- **Artisan Earnings**: 85% of each sale
- Automatically calculated and tracked in wallet

## 🗄️ Database Schema

### Key Tables

- **User** - Authentication and user types
- **Customer** - Buyer profile information
- **Artisan** - Seller profile with verification status
- **Product** - Product catalog with inventory
- **Order** - Order records with status tracking
- **Transaction** - Payment records with unique IDs
- **Complaint** - Customer complaint management
- **Payout** - Artisan payout requests and history
- **AuditLog** - System activity tracking

## 🚀 Getting Started

### Prerequisites

```bash
# Install Python packages
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv passlib python-jose python-multipart
```

### Database Setup

1. Create PostgreSQL database
2. Create `.env` file in project root:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/artisan_marketplace
```

3. Run schema:

```bash
psql -U username -d artisan_marketplace -f schema.sql
```

### Running the Application

1. **Start the backend server**:

```bash
uvicorn main:app --reload
```

2. **Open the application**:
   - Open `login.html` in your browser
   - Or use Live Server in VS Code

### Default Test Accounts

```
Admin:
  Email: admin@marketplace.com
  Password: admin123

Buyer:
  Email: buyer@example.com
  Password: buyer123

Artisan:
  Email: artisan@example.com
  Password: artisan123
```

## 🔒 Security Features

- **JWT Authentication** - Secure token-based auth
- **Bcrypt Password Hashing** - Industry-standard password security
- **Role-Based Access Control** - Enforced at API level
- **CORS Protection** - Configured for secure origins
- **SQL Injection Prevention** - Parameterized queries
- **Row-Level Locking** - Prevents inventory race conditions

## 📊 API Endpoints

### Authentication

- `POST /token` - Login and get JWT token

### Buyer Endpoints

- `GET /buyer/orders` - Get order history
- `POST /buyer/purchase` - Make a purchase
- `GET /buyer/track/{order_id}` - Track order status
- `GET /buyer/payment-history` - View payment history
- `POST /buyer/complaint` - File complaint
- `GET /buyer/complaints` - View complaints

### Artisan Endpoints

- `GET /artisan/products` - Get own products
- `GET /artisan/stats` - Dashboard statistics
- `GET /artisan/wallet` - Wallet and transactions
- `POST /artisan/payout-request` - Request payout

### Admin Endpoints

- `GET /admin/stats` - Platform statistics
- `GET /admin/artisans/pending` - Pending verifications
- `POST /admin/artisan/{id}/verify` - Verify artisan
- `POST /admin/artisan/{id}/suspend` - Suspend artisan
- `GET /admin/audit-logs` - Transaction audit logs
- `GET /admin/payout-ledger` - Artisan payouts

### Product Endpoints

- `GET /products` - List all products
- `POST /products` - Create product
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Delete product

## 🎯 Key Implementation Details

### Transaction ID Generation

```python
transaction_id = f"{payment_method.upper()}-{timestamp}-{random_number}"
# Example: BKASH-1701234567-5432
```

### Inventory Locking

- Uses PostgreSQL `FOR UPDATE NOWAIT` for race condition prevention
- Ensures stock accuracy during concurrent purchases
- Automatic rollback on conflicts

### Commission Calculation

```python
artisan_earnings = sale_amount * (1 - 0.15)  # 85% to artisan
marketplace_commission = sale_amount * 0.15   # 15% to platform
```

## 📝 Future Enhancements

- [ ] Image upload for products
- [ ] Real-time notifications
- [ ] Advanced search and filtering
- [ ] Customer reviews and ratings
- [ ] Shipping integration
- [ ] Multi-language support (Bengali + English)
- [ ] Mobile app version
- [ ] Analytics dashboard
- [ ] Email notifications
- [ ] SMS alerts for order updates

## 🛠️ Technology Stack

- **Frontend**: HTML5, Tailwind CSS, React (via CDN)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Authentication**: JWT + Bcrypt
- **Payment**: Mock integration (ready for real gateway)

## 📄 License

Educational project for CSE347 - Database Management Systems

## 👥 Contributors

Developed for Eastern Washington University - CSE347 Project

---

**Note**: This is a demonstration project. For production use, implement:

- Real payment gateway integration
- SSL/HTTPS encryption
- Rate limiting
- Enhanced error handling
- Comprehensive logging
- Automated testing
- CI/CD pipeline
