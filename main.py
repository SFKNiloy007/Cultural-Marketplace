from datetime import timedelta, datetime
from typing import Annotated, List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import FileResponse
from fastapi import Path
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from jose import jwt as jose_jwt, JWTError
from jwt.exceptions import InvalidSignatureError
from pydantic import BaseModel
import random
import bcrypt
import os
import shutil
from pathlib import Path as FilePath
# NEW IMPORT: For CORS handling
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import DBAPIError
from psycopg2.errors import ForeignKeyViolation

# Internal project imports
from database import get_db

# --- CONFIGURATION AND SECURITY ---
SECRET_KEY = "SUPER_SECURE_KEY_FOR_MARKETPLACE"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Commission rate for the marketplace (15%)
MARKETPLACE_COMMISSION_RATE = 0.15


# --- UTILITY FUNCTIONS ---
def verify_password(plain_password, hashed_password):
    """Checks if a plain password matches the hashed password using bcrypt directly."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Creates a signed JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jose_jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class DBUser:
    def __init__(self, user_id: int, email: str, password_hash: str):
        self.user_id = user_id
        self.email = email
        self.password_hash = password_hash


def authenticate_user(db: Session, email: str, password: str):
    """Retrieves user from DB and verifies the password hash."""
    try:
        query = text(
            'SELECT user_id, email, password_hash, COALESCE(is_active, TRUE) FROM "User" WHERE email = :email')
        result = db.execute(query, {'email': email}).fetchone()

        if result:
            print(
                f"Auth: Found user for email={email}, id={result[0]}, active={result[3]}")
            # If user is not active, return None (will be handled by login endpoint)
            is_active = bool(result[3]) if len(result) > 3 else True
            if not is_active:
                print(
                    f"Auth: User {result[0]} is not active (pending verification)")
                return None
            user = DBUser(
                user_id=result[0], email=result[1], password_hash=result[2])
        else:
            print(f"Auth: No user found for email={email}")
            return None
    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        print(f"Database Query Error during authentication: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Authentication service error")
    if not user:
        return None
    try:
        ok = verify_password(password, user.password_hash)
        print(f"Auth: bcrypt verify result={ok} for user_id={user.user_id}")
    except Exception as e:
        print(f"Auth: bcrypt verification error: {e}")
        ok = False
    if not ok:
        return None
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    """Decode JWT token and get current user with role information."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if email is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    query = text(
        'SELECT user_id, email FROM "User" WHERE user_id = :uid AND is_active = TRUE')
    result = db.execute(query, {'uid': user_id}).fetchone()
    if result is None:
        raise credentials_exception

    # Determine user role by checking which table they belong to
    role = None
    artisan_check = db.execute(text("SELECT artisan_id FROM Artisan WHERE artisan_id = :uid"), {
                               'uid': user_id}).fetchone()
    if artisan_check:
        role = "artisan"
    else:
        customer_check = db.execute(text(
            "SELECT customer_id FROM Customer WHERE customer_id = :uid"), {'uid': user_id}).fetchone()
        if customer_check:
            role = "buyer"

    # Check if admin (you can add admin table check or use a flag in User table)
    # For now, if email contains "admin", treat as admin
    if "admin" in result[1].lower():
        role = "admin"

    return {"user_id": result[0], "email": result[1], "role": role}


async def verify_role(current_user: dict, required_role: str):
    """Verify user has the required role."""
    if current_user.get("role") != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. This endpoint requires {required_role} role."
        )


# --- FASTAPI APPLICATION ---

app = FastAPI(
    title="Local Artisan Marketplace API",
    description="Backend for handling secure authentication and marketplace integrity.",
)

# --- STATIC FILES MOUNTING ---
# Mount the uploads directory to serve product images
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
# Mount the images directory to serve site assets (thumbnails, etc.)
os.makedirs("images", exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

# --- CORS MIDDLEWARE SETUP ---
app.add_middleware(
    CORSMiddleware,
    # Allow local dev and Replit origins
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://*.replit.dev",
        "https://*.replit.app",
        "*"  # Allow all for Replit webview
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- STATIC FILE SERVING ---

@app.get("/", tags=["Static"])
async def serve_login():
    """Serve the login page."""
    return FileResponse("login.html")


@app.get("/login.html", tags=["Static"])
async def serve_login_page():
    return FileResponse("login.html")


@app.get("/buyer.html", tags=["Static"])
async def serve_buyer_page():
    return FileResponse("buyer.html")


@app.get("/artisan.html", tags=["Static"])
async def serve_artisan_page():
    return FileResponse("artisan.html")


@app.get("/admin.html", tags=["Static"])
async def serve_admin_page():
    return FileResponse("admin.html")


# --- AUTHENTICATION ENDPOINT ---

@app.post("/token", tags=["Authentication"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user:
        # Check if user exists but is inactive
        check_user = db.execute(text('SELECT user_id, is_active FROM "User" WHERE email = :email'),
                                {"email": form_data.username}).fetchone()
        if check_user and not check_user[1]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account pending verification. Please wait for admin approval before logging in."
            )
        # User doesn't exist (could have been rejected and deleted, or never registered)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password. If your registration was rejected, please register again with proper credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.user_id},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", tags=["Authentication"])
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Get current user information with role."""
    return current_user


# --- REGISTRATION ENDPOINT ---

class RegistrationRequest(BaseModel):
    email: str
    password: str
    role: str  # "buyer", "artisan", or "admin"
    nid: str = None  # National ID for verification
    phone: str = None  # Contact phone number


@app.post("/register", tags=["Authentication"])
async def register_user(
    registration: RegistrationRequest,
    db: Session = Depends(get_db)
):
    """Register a new user and automatically create their role record (Customer/Artisan). Admin accounts must be created by database administrators."""

    # Validate role - admin not allowed for self-registration
    if registration.role not in ["buyer", "artisan"]:
        raise HTTPException(
            status_code=400, detail="Invalid role. Only 'buyer' and 'artisan' can self-register. Admin accounts must be created by database administrators.")

    # Check if email already exists
    existing = db.execute(text('SELECT user_id FROM "User" WHERE email = :email'),
                          {"email": registration.email}).fetchone()
    if existing:
        raise HTTPException(
            status_code=400, detail="Email already registered.")

    try:
        # Hash password
        password_hash = bcrypt.hashpw(registration.password.encode(
            'utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Create User record (set is_active=FALSE for pending verification)
        user_query = text('''
            INSERT INTO "User" (email, password_hash, is_active)
            VALUES (:email, :hash, FALSE)
            RETURNING user_id
        ''')
        user_id = db.execute(user_query, {
            "email": registration.email,
            "hash": password_hash
        }).scalar_one()

        # Create role-specific record
        if registration.role == "buyer":
            db.execute(text('INSERT INTO Customer(customer_id) VALUES(:uid)'), {
                       "uid": user_id})
        elif registration.role == "artisan":
            db.execute(text('INSERT INTO Artisan(artisan_id) VALUES(:uid)'), {
                       "uid": user_id})

        db.commit()

        return {
            "status": "pending",
            "message": f"Registration submitted successfully as {registration.role}. Your account is pending admin verification. You will be able to login once approved.",
            "user_id": user_id,
            "email": registration.email
        }

    except DBAPIError as e:
        db.rollback()
        print(f"Registration error: {e}")
        raise HTTPException(
            status_code=500, detail="Registration failed due to database error.")


# --- ADMIN USER MANAGEMENT ---

@app.post("/admin/users/{user_id}/activate", tags=["Admin"])
async def admin_activate_user(
    user_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate a user account (set is_active=TRUE). Admin-only."""
    await verify_role(current_user, "admin")

    try:
        exists = db.execute(text('SELECT user_id FROM "User" WHERE user_id = :uid'), {
                            "uid": user_id}).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="User not found")

        db.execute(text('UPDATE "User" SET is_active = TRUE WHERE user_id = :uid'), {
                   "uid": user_id})
        db.commit()
        return {"status": "ok", "message": "User activated", "user_id": user_id}
    except DBAPIError:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error while activating user")


# --- PRODUCT DISPLAY MODEL ---
class ProductDisplay(BaseModel):
    product_id: int
    name: str
    price: float
    stock_quantity: int
    cultural_motif: str
    artisan_id: int
    seller_email: str = None
    image_url: str = None
    description: str = None


class ShipOrderRequest(BaseModel):
    courier_service: str
    tracking_number: Optional[str] = None

# --- PRODUCT CREATION INPUT MODEL ---


class ProductCreate(BaseModel):
    name: str
    price: float
    stock_quantity: int
    cultural_motif: str
    image_url: Optional[str] = None
    description: Optional[str] = None
    # artisan_id is derived from the current authenticated artisan

# --- CRUD: CREATE PRODUCT (C) ---


@app.post("/products", response_model=ProductDisplay, tags=["Product Catalog"])
async def create_product(
    product: ProductCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allows an Artisan to add a new product listing."""
    # Enforce role and derive artisan_id from the authenticated user
    import time
    start_ts = time.time()
    try:
        # Verify artisan role (will raise 403 if not artisan)
        await verify_role(current_user, "artisan")

        aid = current_user['user_id']

        # Check artisan exists
        check_artisan_query = text(
            "SELECT 1 FROM Artisan WHERE artisan_id = :aid")
        if not db.execute(check_artisan_query, {'aid': aid}).scalar():
            raise HTTPException(
                status_code=400, detail="Artisan profile not found for user.")

        insert_query = text(
            """
            INSERT INTO Product (artisan_id, name, price, stock_quantity, cultural_motif, image_url, description)
            VALUES (:aid, :name, :price, :stock, :motif, :image, :desc)
            RETURNING product_id;
            """
        )

        new_id = db.execute(insert_query, {
            'aid': aid,
            'name': product.name,
            'price': product.price,
            'stock': product.stock_quantity,
            'motif': product.cultural_motif,
            'image': product.image_url,
            'desc': product.description
        }).scalar_one()

        db.commit()
        return ProductDisplay(
            product_id=new_id,
            name=product.name,
            price=product.price,
            stock_quantity=product.stock_quantity,
            cultural_motif=product.cultural_motif,
            artisan_id=aid,
            image_url=product.image_url,
            description=product.description
        )
    except HTTPException as http_ex:
        db.rollback()
        raise http_ex
    except DBAPIError as db_error:
        db.rollback()
        print(f"--- PRODUCT CREATE FAIL ---: {db_error}")
        raise HTTPException(
            status_code=500, detail="Failed to create product listing due to DB error.")
    finally:
        print(f"create_product took {int((time.time()-start_ts)*1000)}ms")


@app.post("/products/upload-image", tags=["Product Catalog"])
async def upload_product_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a product image. Returns the image URL to be used when creating/updating products."""
    await verify_role(current_user, "artisan")

    # Validate file type
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    file_extension = FilePath(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Generate unique filename
    timestamp = int(datetime.now().timestamp())
    unique_filename = f"product_{current_user['user_id']}_{timestamp}{file_extension}"
    file_path = FilePath("uploads") / unique_filename

    try:
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Return the URL path
        image_url = f"/uploads/{unique_filename}"
        return {"image_url": image_url, "filename": unique_filename}

    except Exception as e:
        print(f"Image upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload image")


@app.put("/products/{product_id}", tags=["Product Catalog"])
async def update_product(
    product_id: int,
    updates: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a product. Only the owning artisan can edit."""
    await verify_role(current_user, "artisan")

    # Ensure product belongs to current artisan
    owner = db.execute(text("SELECT artisan_id FROM Product WHERE product_id = :pid"), {
                       'pid': product_id}).fetchone()
    if not owner:
        raise HTTPException(status_code=404, detail="Product not found")
    if owner[0] != current_user['user_id']:
        raise HTTPException(
            status_code=403, detail="Not authorized to edit this product")

    # Build dynamic update query
    fields = []
    params = {'pid': product_id}
    for key in ['name', 'price', 'stock_quantity', 'cultural_motif', 'image_url', 'description']:
        if key in updates:
            fields.append(f"{key} = :{key}")
            params[key] = updates[key]

    if not fields:
        return {"status": "noop"}

    try:
        q = text(
            f"UPDATE Product SET {', '.join(fields)} WHERE product_id = :pid")
        db.execute(q, params)
        db.commit()
        return {"status": "ok"}
    except DBAPIError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Update failed")


@app.delete("/products/{product_id}", tags=["Product Catalog"])
async def delete_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a product. Only the owning artisan can delete."""
    await verify_role(current_user, "artisan")

    owner = db.execute(text("SELECT artisan_id FROM Product WHERE product_id = :pid"), {
                       'pid': product_id}).fetchone()
    if not owner:
        raise HTTPException(status_code=404, detail="Product not found")
    if owner[0] != current_user['user_id']:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this product")

    try:
        db.execute(text("DELETE FROM Product WHERE product_id = :pid"), {
                   'pid': product_id})
        db.commit()
        return {"status": "ok"}
    except DBAPIError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Delete failed")


@app.get("/artisan/orders", tags=["Artisan"])
async def get_artisan_orders(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return orders related to the current artisan's products."""
    await verify_role(current_user, "artisan")

    # Get artisan_id
    artisan_query = text(
        "SELECT artisan_id FROM Artisan WHERE artisan_id = :uid")
    artisan = db.execute(
        artisan_query, {'uid': current_user['user_id']}).fetchone()

    if not artisan:
        return []

    aid = artisan[0]

    # Get orders for this artisan's products with shipment info
    query = text(
        """
        SELECT 
            o.order_id, 
            o.order_date, 
            o.status, 
            p.name,
            oi.quantity,
            COALESCE(t.amount,0) as amount,
            s.courier_service,
            s.shipped_date,
            s.tracking_number
        FROM Product p
        JOIN OrderItem oi ON p.product_id = oi.product_id
        JOIN "Order" o ON oi.order_id = o.order_id
        LEFT JOIN "Transaction" t ON o.order_id = t.order_id
        LEFT JOIN Shipment s ON o.order_id = s.order_id
        WHERE p.artisan_id = :aid
        ORDER BY o.order_date DESC
        LIMIT 50
        """
    )
    rows = db.execute(query, {"aid": aid}).fetchall()
    return [
        {
            "order_id": r[0],
            "order_date": r[1].isoformat(),
            "status": r[2],
            "product_name": r[3],
            "quantity": r[4],
            "amount": float(r[5]) if r[5] else 0.0,
            "courier_service": r[6],
            "shipped_date": r[7].isoformat() if r[7] else None,
            "tracking_number": r[8]
        } for r in rows
    ]


@app.post("/artisan/payout-request", tags=["Artisan"])
async def payout_request(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a payout request for the current artisan (stub)."""
    await verify_role(current_user, "artisan")
    # No dedicated payout table in schema; return a mocked response
    return {"status": "submitted", "message": "Payout will be processed in 3-5 business days."}


@app.post("/artisan/orders/{order_id}/ship", tags=["Artisan"])
async def ship_order(
    order_id: int,
    payload: ShipOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark an order as shipped via selected courier service."""
    await verify_role(current_user, "artisan")

    # Validate courier choice
    allowed_couriers = [
        "Uthao",
        "Fatao Courier Services",
        "Royal Bengal Ilish Mach Logistics",
        "Abul and Co"
    ]
    if payload.courier_service not in allowed_couriers:
        raise HTTPException(status_code=400, detail="Invalid courier service")

    # Ensure order belongs to this artisan via at least one product
    ownership_check = db.execute(text("""
        SELECT 1
        FROM OrderItem oi
        JOIN Product p ON oi.product_id = p.product_id
        WHERE oi.order_id = :oid AND p.artisan_id = :aid
        LIMIT 1
    """), {"oid": order_id, "aid": current_user['user_id']}).fetchone()

    if not ownership_check:
        raise HTTPException(
            status_code=404, detail="Order not found for this artisan")

    # Fetch current status
    status_row = db.execute(text("SELECT status FROM \"Order\" WHERE order_id = :oid"), {
                            "oid": order_id}).fetchone()
    if not status_row:
        raise HTTPException(status_code=404, detail="Order not found")
    if status_row[0] != 'Pending Shipment':
        raise HTTPException(
            status_code=400, detail="Order is not pending shipment")

    # Ensure no existing shipment
    existing = db.execute(text("SELECT shipment_id FROM Shipment WHERE order_id = :oid"), {
                          "oid": order_id}).fetchone()
    if existing:
        raise HTTPException(
            status_code=400, detail="Shipment already recorded")

    try:
        # Insert shipment record
        db.execute(text("""
            INSERT INTO Shipment (order_id, courier_service, shipped_date, tracking_number)
            VALUES (:oid, :courier, :date, :track)
        """), {
            "oid": order_id,
            "courier": payload.courier_service,
            "date": datetime.utcnow(),
            "track": payload.tracking_number
        })

        # Update order status
        db.execute(text("UPDATE \"Order\" SET status='Shipped' WHERE order_id = :oid"), {
                   "oid": order_id})
        db.commit()

        return {
            "status": "shipped",
            "order_id": order_id,
            "courier_service": payload.courier_service,
            "tracking_number": payload.tracking_number
        }
    except DBAPIError as e:
        db.rollback()
        print(f"Ship order DB error: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to record shipment")


@app.post("/admin/promote-to-artisan/{user_id}", tags=["Admin"])
async def promote_to_artisan(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an Artisan row for a given user. Admin-only."""
    await verify_role(current_user, "admin")

    # Ensure user exists
    exists = db.execute(text('SELECT user_id FROM "User" WHERE user_id = :uid'), {
                        "uid": user_id}).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if artisan already exists
    already = db.execute(text('SELECT artisan_id FROM Artisan WHERE artisan_id = :uid'), {
                         "uid": user_id}).fetchone()
    if already:
        return {"status": "ok", "message": "Already an artisan"}

    try:
        db.execute(text('INSERT INTO Artisan(artisan_id) VALUES(:uid)'), {
                   "uid": user_id})
        db.commit()
        return {"status": "ok", "message": "User promoted to artisan", "artisan_id": user_id}
    except DBAPIError:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to promote user to artisan")


@app.post("/admin/promote-to-customer/{user_id}", tags=["Admin"])
async def promote_to_customer(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Customer row for a given user. Admin-only."""
    await verify_role(current_user, "admin")

    # Ensure user exists
    exists = db.execute(text('SELECT user_id FROM "User" WHERE user_id = :uid'), {
                        "uid": user_id}).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if customer already exists
    already = db.execute(text('SELECT customer_id FROM Customer WHERE customer_id = :uid'), {
                         "uid": user_id}).fetchone()
    if already:
        return {"status": "ok", "message": "Already a customer"}

    try:
        db.execute(text('INSERT INTO Customer(customer_id) VALUES(:uid)'), {
                   "uid": user_id})
        db.commit()
        return {"status": "ok", "message": "User promoted to customer/buyer", "customer_id": user_id}
    except DBAPIError:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to promote user to customer")


# --- READ FUNCTIONALITY: GET ALL PRODUCTS (R) ---
@app.get("/products", response_model=List[ProductDisplay], tags=["Product Catalog"])
def read_products(db: Session = Depends(get_db)):
    """Fetches all products from the database for display."""
    try:
        query = text("""
            SELECT 
                p.product_id, p.name, p.price, p.stock_quantity, p.cultural_motif, p.artisan_id,
                u.email as seller_email, p.image_url, p.description
            FROM Product p
            JOIN "User" u ON p.artisan_id = u.user_id
            ORDER BY p.product_id DESC
        """)
        products = db.execute(query).fetchall()

        # Convert list of SQL rows to list of dicts with seller info
        return [
            {
                "product_id": row[0],
                "name": row[1],
                "price": float(row[2]),
                "stock_quantity": row[3],
                "cultural_motif": row[4],
                "artisan_id": row[5],
                "seller_email": row[6],
                "image_url": row[7],
                "description": row[8]
            } for row in products
        ]
    except Exception as e:
        print(f"Database Read Error: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve products.")


# --- CRITICAL INVENTORY LOCKING LOGIC ---
class PurchaseRequest(BaseModel):
    product_id: int
    user_id: int
    payment_method: str


@app.post("/purchase/lock", tags=["Transaction"])
def lock_item_for_purchase(request: PurchaseRequest, db: Session = Depends(get_db)):
    """
    CRITICAL INTEGRITY LOGIC: Handles LOCK, Transaction, and Stock Update.
    """
    try:
        # --- PHASE 1: LOCK AND CHECK ---
        query = text("""
            SELECT product_id, price, stock_quantity 
            FROM Product 
            WHERE product_id = :pid 
            FOR UPDATE NOWAIT
        """)

        product_result = db.execute(
            query, {'pid': request.product_id}).fetchone()

        if not product_result:
            raise HTTPException(status_code=404, detail="Product not found.")

        current_stock = product_result[2]

        if current_stock < 1:
            # This is the expected failure path after one successful sale
            raise HTTPException(
                status_code=400, detail="SOLD OUT: Item unavailable. Stock is 0.")

        product_price = product_result[1]

        # --- PHASE 2: CREATE ORDER AND TRANSACTION RECORDS ---

        # 1. Create Order Record (Requires Customer FK verification)
        insert_order_query = text("""
            INSERT INTO "Order" (customer_id, order_date, status)
            VALUES (:cid, :date, 'Pending Shipment')
            RETURNING order_id;
        """)

        new_order_id = db.execute(insert_order_query, {
                                  'cid': request.user_id, 'date': datetime.now()}).scalar_one()

        # 2. Create Transaction Record (Requires Order FK verification)
        trans_id = f"BKASH-{int(datetime.now().timestamp())}-{random.randint(1000, 9999)}"

        insert_transaction_query = text("""
            INSERT INTO "Transaction" (transaction_id, order_id, amount, payment_method, transaction_date)
            VALUES (:tid, :oid, :amount, :method, :date);
        """)

        db.execute(insert_transaction_query, {
            'tid': trans_id,
            'oid': new_order_id,
            'amount': product_price,
            'method': request.payment_method,
            'date': datetime.now()
        })

        # 3. Update Product Stock (Releases the lock implicitly before commit)
        update_query = text(
            "UPDATE Product SET stock_quantity = stock_quantity - 1 WHERE product_id = :pid")
        db.execute(update_query, {'pid': request.product_id})

        # --- PHASE 3: COMMIT (Releases the Lock and Finalizes Transaction) ---
        db.commit()

        return {"status": "success", "message": "Item secured and purchased!", "product_id": request.product_id, "order_id": new_order_id}

    except HTTPException as http_ex:
        db.rollback()
        raise http_ex

    except DBAPIError as db_error:
        db.rollback()
        error_message = str(db_error.orig)

        # Handle specific concurrency error returned by PostgreSQL
        if "NOWAIT" in error_message or "could not obtain lock" in error_message:
            raise HTTPException(
                status_code=400, detail="CONCURRENCY ERROR: Item is currently locked by another buyer. Try again.")

        if isinstance(db_error.orig, ForeignKeyViolation):
            raise HTTPException(
                status_code=400, detail="INTEGRITY ERROR: Missing required Customer/Artisan data. Run SQL setup script.")

        print(f"--- DB TRANSACTION FAIL (Unclassified) ---: {db_error}")
        raise HTTPException(
            status_code=500, detail="System integrity error during transaction. Check server logs.")

    except Exception as e:
        db.rollback()
        print(f"--- UNEXPECTED FAIL ---: {e}")
        raise HTTPException(
            status_code=500, detail=f"Unexpected system error: {e}")


# ==================== NEW BUYER ENDPOINTS ====================

class BuyerPurchaseRequest(BaseModel):
    product_id: int
    quantity: int
    payment_method: str


@app.post("/buyer/purchase", tags=["Buyer"])
async def buyer_purchase(
    request: BuyerPurchaseRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Buyer makes a purchase with quantity and payment calculation."""
    await verify_role(current_user, "buyer")

    try:
        # Lock and get product
        query = text("""
            SELECT product_id, price, stock_quantity, artisan_id
            FROM Product 
            WHERE product_id = :pid 
            FOR UPDATE NOWAIT
        """)
        product = db.execute(query, {'pid': request.product_id}).fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if product[2] < request.quantity:
            raise HTTPException(
                status_code=400, detail=f"Insufficient stock. Available: {product[2]}")

        # Calculate total amount
        total_amount = float(product[1]) * request.quantity

        # Create order
        insert_order = text("""
            INSERT INTO "Order" (customer_id, order_date, status)
            VALUES (:cid, :date, 'Pending Shipment')
            RETURNING order_id;
        """)
        order_id = db.execute(insert_order, {
            'cid': current_user['user_id'],
            'date': datetime.now()
        }).scalar_one()

        # Generate transaction ID
        trans_id = f"{request.payment_method.upper()}-{int(datetime.now().timestamp())}-{random.randint(1000, 9999)}"

        # Create transaction
        insert_transaction = text("""
            INSERT INTO "Transaction" (transaction_id, order_id, amount, payment_method, transaction_date)
            VALUES (:tid, :oid, :amount, :method, :date);
        """)
        db.execute(insert_transaction, {
            'tid': trans_id,
            'oid': order_id,
            'amount': total_amount,
            'method': request.payment_method,
            'date': datetime.now()
        })

        # Create order item to track product purchase
        insert_order_item = text("""
            INSERT INTO OrderItem (order_id, product_id, quantity, price)
            VALUES (:oid, :pid, :qty, :price);
        """)
        db.execute(insert_order_item, {
            'oid': order_id,
            'pid': request.product_id,
            'qty': request.quantity,
            'price': product[1]
        })

        # Update stock
        update_stock = text(
            "UPDATE Product SET stock_quantity = stock_quantity - :qty WHERE product_id = :pid")
        db.execute(update_stock, {
                   'qty': request.quantity, 'pid': request.product_id})

        db.commit()

        return {
            "status": "success",
            "transaction_id": trans_id,
            "order_id": order_id,
            "total_amount": total_amount
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Purchase error: {e}")
        raise HTTPException(status_code=500, detail="Purchase failed")


@app.get("/buyer/orders", tags=["Buyer"])
async def get_buyer_orders(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get buyer's order history."""
    query = text("""
        SELECT o.order_id, o.order_date, o.status, t.amount as total_amount
        FROM "Order" o
        LEFT JOIN "Transaction" t ON o.order_id = t.order_id
        WHERE o.customer_id = :cid
        ORDER BY o.order_date DESC
    """)
    orders = db.execute(query, {'cid': current_user['user_id']}).fetchall()

    return [
        {
            "order_id": row[0],
            "order_date": row[1].isoformat(),
            "status": row[2],
            "total_amount": float(row[3]) if row[3] else 0
        } for row in orders
    ]


@app.get("/buyer/track/{order_id}", tags=["Buyer"])
async def track_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track order status including courier, tracking number and expected delivery date."""
    await verify_role(current_user, "buyer")

    query = text("""
        SELECT o.order_id, o.order_date, o.status, s.courier_service, s.tracking_number, s.shipped_date
        FROM "Order" o
        LEFT JOIN Shipment s ON o.order_id = s.order_id
        WHERE o.order_id = :oid AND o.customer_id = :cid
        LIMIT 1
    """)
    row = db.execute(
        query, {"oid": order_id, "cid": current_user['user_id']}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")

    courier_service = row[3]
    tracking_number = row[4]
    shipped_date = row[5]

    expected_delivery_date = None
    if shipped_date and courier_service:
        days_map = {
            "Uthao": 2,
            "Fatao Courier Services": 3,
            "Royal Bengal Ilish Mach Logistics": 5,
            "Abul and Co": 4
        }
        expected_delivery_date = (
            shipped_date + timedelta(days=days_map.get(courier_service, 3))).isoformat()

    timeline = [
        {"status": "Order Placed", "date": row[1].strftime(
            "%b %d, %I:%M %p"), "completed": True},
        {"status": "Payment Confirmed", "date": row[1].strftime(
            "%b %d, %I:%M %p"), "completed": True},
        {"status": "Processing", "date": shipped_date.isoformat(
        ) if shipped_date else "In Progress", "completed": row[2] != "Pending Shipment"},
        {"status": "Shipped", "date": shipped_date.isoformat(
        ) if shipped_date else "Pending", "completed": row[2] in ["Shipped", "Delivered"]},
        {"status": "Delivered", "date": expected_delivery_date if row[2] ==
            "Delivered" else "Pending", "completed": row[2] == "Delivered"}
    ]

    return {
        "order_id": row[0],
        "status": row[2],
        "courier_service": courier_service,
        "tracking_number": tracking_number,
        "shipped_date": shipped_date.isoformat() if shipped_date else None,
        "expected_delivery_date": expected_delivery_date,
        "timeline": timeline
    }


@app.post("/buyer/orders/{order_id}/confirm-delivery", tags=["Buyer"])
async def confirm_delivery(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Buyer confirms receipt of a shipped order; status becomes Delivered."""
    await verify_role(current_user, "buyer")

    # Fetch order ensuring ownership and current status
    row = db.execute(text("""
        SELECT status FROM "Order" WHERE order_id = :oid AND customer_id = :cid
    """), {"oid": order_id, "cid": current_user['user_id']}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    if row[0] != 'Shipped':
        raise HTTPException(
            status_code=400, detail="Order must be in Shipped state to confirm delivery")

    try:
        db.execute(text("UPDATE \"Order\" SET status='Delivered' WHERE order_id = :oid"), {
                   "oid": order_id})
        db.commit()
        return {"status": "Delivered", "order_id": order_id}
    except DBAPIError as e:
        db.rollback()
        print(f"Confirm delivery error: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to confirm delivery")


@app.get("/buyer/payment-history", tags=["Buyer"])
async def get_payment_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get buyer's payment history."""
    query = text("""
        SELECT t.transaction_id, t.order_id, t.amount, t.payment_method, t.transaction_date
        FROM "Transaction" t
        JOIN "Order" o ON t.order_id = o.order_id
        WHERE o.customer_id = :cid
        ORDER BY t.transaction_date DESC
    """)
    payments = db.execute(query, {'cid': current_user['user_id']}).fetchall()

    return [
        {
            "transaction_id": row[0],
            "order_id": row[1],
            "amount": float(row[2]),
            "payment_method": row[3],
            "transaction_date": row[4].isoformat()
        } for row in payments
    ]


# ==================== COMPLAINT ENDPOINTS ====================

class ComplaintRequest(BaseModel):
    order_id: int
    complaint_type: str
    description: str


# In-memory complaint storage (replace with database table in production)
complaints_storage = []


@app.post("/buyer/complaint", tags=["Buyer"])
async def submit_complaint(
    complaint: ComplaintRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a complaint about an order."""
    await verify_role(current_user, "buyer")

    # Verify order belongs to this customer
    order_check = db.execute(
        text("SELECT order_id FROM \"Order\" WHERE order_id = :oid AND customer_id = :cid"),
        {"oid": complaint.order_id, "cid": current_user['user_id']}
    ).fetchone()

    if not order_check:
        raise HTTPException(
            status_code=404, detail="Order not found or does not belong to you")

    # Store complaint
    complaint_data = {
        "complaint_id": len(complaints_storage) + 1,
        "order_id": complaint.order_id,
        "customer_id": current_user['user_id'],
        "complaint_type": complaint.complaint_type,
        "description": complaint.description,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    complaints_storage.append(complaint_data)

    return {"status": "success", "complaint_id": complaint_data["complaint_id"]}


@app.get("/buyer/complaints", tags=["Buyer"])
async def get_complaints(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get buyer's complaints."""
    await verify_role(current_user, "buyer")

    # Filter complaints for this customer
    customer_complaints = [
        c for c in complaints_storage
        if c["customer_id"] == current_user['user_id']
    ]

    return customer_complaints


# ==================== NEW ARTISAN ENDPOINTS ====================

@app.get("/artisan/products", tags=["Artisan"])
async def get_artisan_products(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get artisan's own products."""
    # Get artisan_id from user_id
    # In schemas where Artisan does not have user_id column,
    # artisan_id is the same identifier as User.user_id.
    artisan_query = text(
        "SELECT artisan_id FROM Artisan WHERE artisan_id = :uid")
    artisan = db.execute(
        artisan_query, {'uid': current_user['user_id']}).fetchone()

    if not artisan:
        return []

    query = text("""
        SELECT product_id, name, price, stock_quantity, cultural_motif, artisan_id, image_url, description
        FROM Product
        WHERE artisan_id = :aid
        ORDER BY product_id DESC
    """)
    products = db.execute(query, {'aid': artisan[0]}).fetchall()

    return [
        {
            "product_id": row[0],
            "name": row[1],
            "price": float(row[2]),
            "stock_quantity": row[3],
            "cultural_motif": row[4],
            "artisan_id": row[5],
            "image_url": row[6],
            "description": row[7]
        } for row in products
    ]


@app.get("/artisan/stats", tags=["Artisan"])
async def get_artisan_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get artisan dashboard statistics."""
    await verify_role(current_user, "artisan")

    artisan_query = text(
        "SELECT artisan_id FROM Artisan WHERE artisan_id = :uid")
    artisan = db.execute(
        artisan_query, {'uid': current_user['user_id']}).fetchone()

    if not artisan:
        return {"total_products": 0, "total_sales": 0, "pending_orders": 0, "completed_orders": 0, "wallet_balance": 0}

    aid = artisan[0]

    # Get stats with conservative queries to avoid DB errors
    try:
        total_products = db.execute(
            text(
                "SELECT COUNT(*) FROM Product WHERE artisan_id = :aid"), {"aid": aid}
        ).scalar() or 0

        # Calculate sales from OrderItem table
        sales_query = text("""
            SELECT 
                COALESCE(SUM(t.amount), 0) as total_sales,
                COUNT(DISTINCT CASE WHEN o.status = 'Pending Shipment' THEN o.order_id END) as awaiting_dispatch,
                COUNT(DISTINCT CASE WHEN o.status = 'Shipped' THEN o.order_id END) as in_transit,
                COUNT(DISTINCT CASE WHEN o.status = 'Delivered' THEN o.order_id END) as completed_orders
            FROM Product p
            LEFT JOIN OrderItem oi ON p.product_id = oi.product_id
            LEFT JOIN "Order" o ON oi.order_id = o.order_id
            LEFT JOIN "Transaction" t ON o.order_id = t.order_id
            WHERE p.artisan_id = :aid
        """)
        sales_result = db.execute(sales_query, {"aid": aid}).fetchone()

        total_sales = float(sales_result[0]) if sales_result else 0.0
        awaiting_dispatch = int(sales_result[1]) if sales_result else 0
        in_transit = int(sales_result[2]) if sales_result else 0
        completed_orders = int(sales_result[3]) if sales_result else 0

        wallet_balance = float(total_sales) * (1 - MARKETPLACE_COMMISSION_RATE)

        return {
            "total_products": int(total_products),
            "total_sales": float(total_sales),
            "awaiting_dispatch": int(awaiting_dispatch),
            "in_transit": int(in_transit),
            "completed_orders": int(completed_orders),
            "wallet_balance": float(wallet_balance)
        }
    except DBAPIError as e:
        print(f"Artisan stats query error: {e}")
        return {
            "total_products": 0,
            "total_sales": 0.0,
            "awaiting_dispatch": 0,
            "in_transit": 0,
            "completed_orders": 0,
            "wallet_balance": 0.0
        }


@app.get("/artisan/recent-sales", tags=["Artisan"])
async def get_artisan_recent_sales(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent sales for artisan dashboard notifications."""
    await verify_role(current_user, "artisan")

    artisan_query = text(
        "SELECT artisan_id FROM Artisan WHERE artisan_id = :uid")
    artisan = db.execute(
        artisan_query, {'uid': current_user['user_id']}).fetchone()

    if not artisan:
        return []

    aid = artisan[0]

    # Get last 10 sales with product and buyer info
    recent_sales_query = text("""
        SELECT 
            p.name,
            p.product_id,
            u.email as buyer_email,
            oi.quantity,
            t.amount,
            o.order_date,
            o.status,
            t.transaction_id
        FROM Product p
        JOIN OrderItem oi ON p.product_id = oi.product_id
        JOIN "Order" o ON oi.order_id = o.order_id
        JOIN "Transaction" t ON o.order_id = t.order_id
        JOIN Customer c ON o.customer_id = c.customer_id
        JOIN "User" u ON c.customer_id = u.user_id
        WHERE p.artisan_id = :aid
        ORDER BY o.order_date DESC
        LIMIT 10
    """)

    sales = db.execute(recent_sales_query, {"aid": aid}).fetchall()

    return [
        {
            "product_name": sale[0],
            "product_id": sale[1],
            "buyer_email": sale[2],
            "quantity": sale[3],
            "amount": float(sale[4]),
            "payout": float(sale[4]) * (1 - MARKETPLACE_COMMISSION_RATE),
            "order_date": sale[5].isoformat(),
            "status": sale[6],
            "transaction_id": sale[7]
        } for sale in sales
    ]


@app.get("/artisan/wallet", tags=["Artisan"])
async def get_artisan_wallet(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get artisan wallet and transaction details."""
    await verify_role(current_user, "artisan")

    artisan_query = text(
        "SELECT artisan_id FROM Artisan WHERE artisan_id = :uid")
    artisan = db.execute(
        artisan_query, {'uid': current_user['user_id']}).fetchone()

    if not artisan:
        return {"balance": 0, "total_earned": 0, "commission_paid": 0, "pending_payout": 0, "transactions": []}

    aid = artisan[0]

    # Get transactions related to this artisan through OrderItem
    transactions_query = text("""
        SELECT 
            t.transaction_id,
            t.order_id,
            t.amount,
            t.transaction_date
        FROM Product p
        JOIN OrderItem oi ON p.product_id = oi.product_id
        JOIN "Order" o ON oi.order_id = o.order_id
        JOIN "Transaction" t ON o.order_id = t.order_id
        WHERE p.artisan_id = :aid
        ORDER BY t.transaction_date DESC
    """)

    transactions = db.execute(transactions_query, {"aid": aid}).fetchall()

    total_earned = sum(float(t[2]) for t in transactions)
    commission_paid = total_earned * MARKETPLACE_COMMISSION_RATE
    net_balance = total_earned - commission_paid

    return {
        "balance": net_balance,
        "total_earned": total_earned,
        "commission_paid": commission_paid,
        "pending_payout": net_balance,
        "transactions": [
            {
                "transaction_id": t[0],
                "order_id": t[1],
                "amount": float(t[2]),
                "commission": float(t[2]) * MARKETPLACE_COMMISSION_RATE,
                "net": float(t[2]) * (1 - MARKETPLACE_COMMISSION_RATE),
                "date": t[3].isoformat()
            } for t in transactions
        ]
    }


# ==================== NEW ADMIN ENDPOINTS ====================

@app.get("/admin/stats", tags=["Admin"])
async def get_admin_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics."""
    await verify_role(current_user, "admin")

    stats_query = text("""
        SELECT 
            (SELECT COUNT(*) FROM Artisan) as total_artisans,
            0 as pending_artisans,
            (SELECT COUNT(*) FROM "Transaction") as total_transactions,
            (SELECT COUNT(*) FROM "Order" WHERE status != 'Delivered') as active_orders
    """)
    stats = db.execute(stats_query).fetchone()

    return {
        "total_artisans": stats[0],
        "pending_artisans": stats[1],
        "total_transactions": stats[2],
        "active_orders": stats[3]
    }


@app.get("/admin/users/pending", tags=["Admin"])
async def get_pending_users(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users (buyers and artisans) pending verification."""
    await verify_role(current_user, "admin")

    # Get pending artisans
    artisan_query = text("""
        SELECT u.user_id, u.email, 'artisan' as user_type, a.village_origin, u.registration_date
        FROM "User" u
        JOIN Artisan a ON a.artisan_id = u.user_id
        WHERE COALESCE(u.is_active, FALSE) = FALSE
    """)
    artisans = db.execute(artisan_query).fetchall()

    # Get pending buyers
    buyer_query = text("""
        SELECT u.user_id, u.email, 'buyer' as user_type, c.shipping_address, u.registration_date
        FROM "User" u
        JOIN Customer c ON c.customer_id = u.user_id
        WHERE COALESCE(u.is_active, FALSE) = FALSE
    """)
    buyers = db.execute(buyer_query).fetchall()

    # Combine both lists
    pending_users = []

    for row in artisans:
        pending_users.append({
            "user_id": row[0],
            "email": row[1],
            "user_type": "Artisan",
            "details": row[3] or "N/A",
            "registration_date": row[4].isoformat() if row[4] else "N/A",
            "status": "pending"
        })

    for row in buyers:
        pending_users.append({
            "user_id": row[0],
            "email": row[1],
            "user_type": "Buyer",
            "details": row[3] or "N/A",
            "registration_date": row[4].isoformat() if row[4] else "N/A",
            "status": "pending"
        })

    # Sort by registration date (newest first)
    pending_users.sort(key=lambda x: x["registration_date"], reverse=True)

    return pending_users


@app.get("/admin/artisans/pending", tags=["Admin"])
async def get_pending_artisans(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get artisans pending verification (not yet approved). Deprecated - use /admin/users/pending instead."""
    await verify_role(current_user, "admin")
    query = text("""
        SELECT a.artisan_id, u.email, a.village_origin, a.digital_literacy_level, u.is_active
        FROM Artisan a
        JOIN "User" u ON a.artisan_id = u.user_id
        WHERE COALESCE(u.is_active, FALSE) = FALSE
    """)
    artisans = db.execute(query).fetchall()

    return [
        {
            "artisan_id": row[0],
            "business_name": row[1],
            "contact_phone": row[2],
            "location": row[3],
            "status": "pending"
        } for row in artisans
    ]


@app.get("/admin/artisans/active", tags=["Admin"])
async def get_active_artisans(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get verified active artisans (approved and active)."""
    await verify_role(current_user, "admin")
    query = text("""
        SELECT a.artisan_id, u.email, a.village_origin
        FROM Artisan a
        JOIN "User" u ON a.artisan_id = u.user_id
        WHERE u.is_active = TRUE
    """)
    artisans = db.execute(query).fetchall()

    return [
        {
            "artisan_id": row[0],
            "business_name": row[1],
            "contact_phone": row[2]
        } for row in artisans
    ]


@app.post("/admin/user/{user_id}/verify", tags=["Admin"])
async def verify_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify/Approve any user (buyer or artisan) by activating their account."""
    await verify_role(current_user, "admin")
    try:
        query = text(
            "UPDATE \"User\" SET is_active = TRUE WHERE user_id = :uid")
        result = db.execute(query, {'uid': user_id})
        db.commit()
        return {"status": "success", "message": "User approved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Approval failed")


@app.post("/admin/artisan/{artisan_id}/verify", tags=["Admin"])
async def verify_artisan(
    artisan_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify/Approve an artisan by activating their account. Deprecated - use /admin/user/{user_id}/verify instead."""
    await verify_role(current_user, "admin")
    try:
        query = text(
            "UPDATE \"User\" SET is_active = TRUE WHERE user_id = :aid")
        result = db.execute(query, {'aid': artisan_id})
        db.commit()
        return {"status": "success", "message": "Artisan approved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Approval failed")


@app.post("/admin/user/{user_id}/reject", tags=["Admin"])
async def reject_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject any user (buyer or artisan) by deleting their account."""
    await verify_role(current_user, "admin")
    try:
        # Delete from Customer or Artisan table first (foreign key constraint)
        db.execute(text("DELETE FROM Customer WHERE customer_id = :uid"), {
                   'uid': user_id})
        db.execute(text("DELETE FROM Artisan WHERE artisan_id = :uid"), {
                   'uid': user_id})

        # Then delete from User table
        db.execute(text("DELETE FROM \"User\" WHERE user_id = :uid"), {
                   'uid': user_id})

        db.commit()
        return {"status": "success", "message": "User rejected and removed from system"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Rejection failed: {str(e)}")


@app.post("/admin/artisan/{artisan_id}/reject", tags=["Admin"])
async def reject_artisan(
    artisan_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject an artisan by deactivating their account. Deprecated - use /admin/user/{user_id}/reject instead."""
    await verify_role(current_user, "admin")
    try:
        query = text(
            "UPDATE \"User\" SET is_active = FALSE WHERE user_id = :aid")
        result = db.execute(query, {'aid': artisan_id})
        db.commit()
        return {"status": "success", "message": "Artisan rejected successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Rejection failed")


@app.post("/admin/artisan/{artisan_id}/suspend", tags=["Admin"])
async def suspend_artisan(
    artisan_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Suspend an artisan."""
    try:
        query = text(
            "UPDATE \"User\" SET is_active = FALSE WHERE user_id = :aid")
        db.execute(query, {'aid': artisan_id})
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Suspension failed")


@app.get("/admin/audit-logs", tags=["Admin"])
async def get_audit_logs(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction audit logs."""
    query = text("""
        SELECT transaction_id, order_id, amount, payment_method, transaction_date
        FROM "Transaction"
        ORDER BY transaction_date DESC
        LIMIT 100
    """)
    logs = db.execute(query).fetchall()

    return [
        {
            "transaction_id": row[0],
            "order_id": row[1],
            "amount": float(row[2]),
            "payment_method": row[3],
            "transaction_date": row[4].isoformat()
        } for row in logs
    ]


@app.get("/admin/payout-ledger", tags=["Admin"])
async def get_payout_ledger(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get artisan payout ledger."""
    query = text("""
        SELECT 
            u.email as artisan_name,
            COALESCE(SUM(t.amount), 0) as total_sales
        FROM Artisan a
        JOIN "User" u ON a.artisan_id = u.user_id
        LEFT JOIN Product p ON a.artisan_id = p.artisan_id
        LEFT JOIN "Transaction" t ON t.order_id IN (
            SELECT o.order_id FROM "Order" o
        )
        GROUP BY a.artisan_id, u.email
    """)
    payouts = db.execute(query).fetchall()

    return [
        {
            "artisan_name": row[0],
            "total_sales": float(row[1]),
            "commission": float(row[1]) * MARKETPLACE_COMMISSION_RATE,
            "net_payout": float(row[1]) * (1 - MARKETPLACE_COMMISSION_RATE),
            "status": "pending"
        } for row in payouts
    ]


@app.get("/admin/seller-financial/{artisan_id}", tags=["Admin"])
async def get_seller_financial_info(
    artisan_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed financial information for a specific seller/artisan."""
    await verify_role(current_user, "admin")

    # Check if artisan exists
    artisan_check = db.execute(
        text("SELECT artisan_id FROM Artisan WHERE artisan_id = :aid"),
        {"aid": artisan_id}
    ).fetchone()

    if not artisan_check:
        raise HTTPException(status_code=404, detail="Artisan not found")

    # Get artisan basic info
    artisan_info = db.execute(text("""
        SELECT u.user_id, u.email, u.registration_date, a.village_origin
        FROM "User" u
        JOIN Artisan a ON u.user_id = a.artisan_id
        WHERE a.artisan_id = :aid
    """), {"aid": artisan_id}).fetchone()

    # Get financial stats
    financial_stats = db.execute(text("""
        SELECT 
            COUNT(DISTINCT p.product_id) as total_products,
            COALESCE(SUM(t.amount), 0) as total_revenue,
            COUNT(DISTINCT o.order_id) as total_orders,
            COUNT(DISTINCT CASE WHEN o.status = 'Delivered' THEN o.order_id END) as completed_orders,
            COUNT(DISTINCT CASE WHEN o.status = 'Pending Shipment' THEN o.order_id END) as pending_orders
        FROM Product p
        LEFT JOIN OrderItem oi ON p.product_id = oi.product_id
        LEFT JOIN "Order" o ON oi.order_id = o.order_id
        LEFT JOIN "Transaction" t ON o.order_id = t.order_id
        WHERE p.artisan_id = :aid
    """), {"aid": artisan_id}).fetchone()

    # Get recent transactions
    recent_transactions = db.execute(text("""
        SELECT 
            t.transaction_id,
            t.order_id,
            t.amount,
            t.payment_method,
            t.transaction_date,
            p.name as product_name,
            oi.quantity
        FROM Product p
        JOIN OrderItem oi ON p.product_id = oi.product_id
        JOIN "Order" o ON oi.order_id = o.order_id
        JOIN "Transaction" t ON o.order_id = t.order_id
        WHERE p.artisan_id = :aid
        ORDER BY t.transaction_date DESC
        LIMIT 20
    """), {"aid": artisan_id}).fetchall()

    total_revenue = float(financial_stats[1]) if financial_stats else 0.0
    commission = total_revenue * MARKETPLACE_COMMISSION_RATE
    net_earnings = total_revenue - commission

    return {
        "artisan_id": artisan_info[0],
        "email": artisan_info[1],
        "registration_date": artisan_info[2].isoformat() if artisan_info[2] else None,
        "village_origin": artisan_info[3],
        "financial_summary": {
            "total_products": int(financial_stats[0]) if financial_stats else 0,
            "total_revenue": total_revenue,
            "marketplace_commission": commission,
            "net_earnings": net_earnings,
            "total_orders": int(financial_stats[2]) if financial_stats else 0,
            "completed_orders": int(financial_stats[3]) if financial_stats else 0,
            "pending_orders": int(financial_stats[4]) if financial_stats else 0
        },
        "recent_transactions": [
            {
                "transaction_id": tx[0],
                "order_id": tx[1],
                "amount": float(tx[2]),
                "commission": float(tx[2]) * MARKETPLACE_COMMISSION_RATE,
                "net": float(tx[2]) * (1 - MARKETPLACE_COMMISSION_RATE),
                "payment_method": tx[3],
                "date": tx[4].isoformat(),
                "product_name": tx[5],
                "quantity": tx[6]
            } for tx in recent_transactions
        ]
    }


@app.get("/admin/all-sellers-financial", tags=["Admin"])
async def get_all_sellers_financial(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get financial overview of all sellers/artisans."""
    await verify_role(current_user, "admin")

    sellers_query = text("""
        SELECT 
            a.artisan_id,
            u.email,
            u.registration_date,
            COUNT(DISTINCT p.product_id) as total_products,
            COALESCE(SUM(t.amount), 0) as total_revenue,
            COUNT(DISTINCT o.order_id) as total_orders
        FROM Artisan a
        JOIN "User" u ON a.artisan_id = u.user_id
        LEFT JOIN Product p ON a.artisan_id = p.artisan_id
        LEFT JOIN OrderItem oi ON p.product_id = oi.product_id
        LEFT JOIN "Order" o ON oi.order_id = o.order_id
        LEFT JOIN "Transaction" t ON o.order_id = t.order_id
        WHERE u.is_active = TRUE
        GROUP BY a.artisan_id, u.email, u.registration_date
        ORDER BY total_revenue DESC
    """)

    sellers = db.execute(sellers_query).fetchall()

    return [
        {
            "artisan_id": seller[0],
            "email": seller[1],
            "registration_date": seller[2].isoformat() if seller[2] else None,
            "total_products": int(seller[3]),
            "total_revenue": float(seller[4]),
            "marketplace_commission": float(seller[4]) * MARKETPLACE_COMMISSION_RATE,
            "net_earnings": float(seller[4]) * (1 - MARKETPLACE_COMMISSION_RATE),
            "total_orders": int(seller[5])
        } for seller in sellers
    ]

# ==================== TRACKING BY COURIER ID (BUYER) ====================


class ShipmentTrackingResponse(BaseModel):
    tracking_number: Optional[str]
    courier_service: Optional[str]
    shipped_date: Optional[str]
    expected_delivery_date: Optional[str]
    status: str
    order_id: int
    product_name: Optional[str]
    quantity: int
    artisan_email: Optional[str]


@app.get("/buyer/track-by/{tracking_number}", response_model=ShipmentTrackingResponse, tags=["Buyer"])
async def track_by_tracking_number(
    tracking_number: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allow a buyer to view shipment/order details using the courier tracking number they received.
    Ensures the tracking number belongs to one of the buyer's own orders."""
    await verify_role(current_user, "buyer")

    query = text("""
        SELECT 
            s.tracking_number,
            s.courier_service,
            s.shipped_date,
            o.status,
            o.order_id,
            p.name as product_name,
            COALESCE(oi.quantity, 1) as quantity,
            u.email as artisan_email
        FROM Shipment s
        JOIN "Order" o ON s.order_id = o.order_id
        JOIN OrderItem oi ON oi.order_id = o.order_id
        JOIN Product p ON oi.product_id = p.product_id
        JOIN Artisan a ON p.artisan_id = a.artisan_id
        JOIN "User" u ON a.artisan_id = u.user_id
        WHERE s.tracking_number = :track AND o.customer_id = :cid
        LIMIT 1
    """)

    row = db.execute(query, {"track": tracking_number,
                     "cid": current_user["user_id"]}).fetchone()

    if not row:
        raise HTTPException(
            status_code=404, detail="Tracking number not found for your orders")

    expected_delivery_date = None
    if row[2] and row[1]:
        days_map = {
            "Uthao": 2,
            "Fatao Courier Services": 3,
            "Royal Bengal Ilish Mach Logistics": 5,
            "Abul and Co": 4
        }
        expected_delivery_date = (
            row[2] + timedelta(days=days_map.get(row[1], 3))).isoformat()

    return ShipmentTrackingResponse(
        tracking_number=row[0],
        courier_service=row[1],
        shipped_date=row[2].isoformat() if row[2] else None,
        expected_delivery_date=expected_delivery_date,
        status=row[3],
        order_id=row[4],
        product_name=row[5],
        quantity=int(row[6]) if row[6] else 1,
        artisan_email=row[7]
    )
