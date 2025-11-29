# Product Images Feature Guide

## Setup Instructions

### 1. Database Migration

Run the SQL migration to add image support:

```bash
# In pgAdmin Query Tool or psql:
psql -U postgres -d your_database_name -f add_product_images.sql
```

Or manually in pgAdmin:

```sql
ALTER TABLE Product ADD COLUMN image_url VARCHAR(500);
```

### 2. Restart Server

```bash
python -m uvicorn main:app --reload
```

## How to Use

### For Artisans - Uploading Product Images

#### Method 1: Two-Step Process (Upload then Create)

**Step 1: Upload Image**

```javascript
// Frontend JavaScript
const formData = new FormData();
formData.append("file", imageFile); // imageFile is from <input type="file">

const uploadResponse = await fetch(
  "http://localhost:8000/products/upload-image",
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  }
);

const { image_url } = await uploadResponse.json();
// Result: { "image_url": "/uploads/product_123_1701234567.jpg", "filename": "..." }
```

**Step 2: Create Product with Image URL**

```javascript
const productData = {
  name: "Handwoven Nakshi Katha",
  price: 2500.0,
  stock_quantity: 10,
  cultural_motif: "Traditional Bengali",
  image_url: image_url, // Use the URL from Step 1
};

const response = await fetch("http://localhost:8000/products", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify(productData),
});
```

#### Method 2: Update Existing Product Image

```javascript
// First upload the image (same as Step 1 above)
const { image_url } = await uploadImageResponse.json();

// Then update the product
const response = await fetch(`http://localhost:8000/products/${product_id}`, {
  method: "PUT",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ image_url: image_url }),
});
```

### For Buyers - Viewing Product Images

Product images are included automatically in all product listings:

```javascript
// Get all products
const response = await fetch("http://localhost:8000/products");
const products = await response.json();

products.forEach((product) => {
  console.log(product.name);
  console.log(product.image_url); // e.g., "/uploads/product_123_1701234567.jpg"

  // Display in HTML
  const img = document.createElement("img");
  img.src = `http://localhost:8000${product.image_url}`;
  img.alt = product.name;
  document.body.appendChild(img);
});
```

### HTML Example - Product Card with Image

```html
<div class="product-card">
  <img
    src="http://localhost:8000/uploads/product_123_1701234567.jpg"
    alt="Product Name"
    onerror="this.src='/uploads/placeholder.jpg'"
  />
  <h3>Handwoven Nakshi Katha</h3>
  <p>Price: ৳2,500</p>
  <p>Cultural Motif: Traditional Bengali</p>
  <button onclick="buyProduct(123)">Buy Now</button>
</div>
```

## API Endpoints

### 1. Upload Product Image (POST)

- **Endpoint**: `/products/upload-image`
- **Auth**: Required (Artisan only)
- **Content-Type**: `multipart/form-data`
- **Request Body**:
  - `file`: Image file (jpg, jpeg, png, gif, webp)
- **Response**:
  ```json
  {
    "image_url": "/uploads/product_123_1701234567.jpg",
    "filename": "product_123_1701234567.jpg"
  }
  ```

### 2. Create Product with Image (POST)

- **Endpoint**: `/products`
- **Auth**: Required (Artisan only)
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "name": "Product Name",
    "price": 2500.0,
    "stock_quantity": 10,
    "cultural_motif": "Traditional",
    "image_url": "/uploads/product_123_1701234567.jpg"
  }
  ```

### 3. Update Product Image (PUT)

- **Endpoint**: `/products/{product_id}`
- **Auth**: Required (Artisan - must own product)
- **Request Body**:
  ```json
  {
    "image_url": "/uploads/new_image.jpg"
  }
  ```

### 4. Get Products with Images (GET)

- **Endpoint**: `/products`
- **Auth**: Not required
- **Response**: Array of products with `image_url` field

### 5. Access Images

- **Endpoint**: `/uploads/{filename}`
- **Example**: `http://localhost:8000/uploads/product_123_1701234567.jpg`

## File Constraints

- **Allowed formats**: JPG, JPEG, PNG, GIF, WEBP
- **Naming convention**: `product_{artisan_id}_{timestamp}.{extension}`
- **Storage location**: `uploads/` directory
- **Max size**: Configure in your reverse proxy (default: unlimited in FastAPI)

## Security Notes

1. **Authentication**: Only logged-in artisans can upload images
2. **File validation**: Server checks file extensions
3. **Unique filenames**: Timestamp prevents filename collisions
4. **Ownership**: Only product owner can update images

## Troubleshooting

### Images not displaying?

1. Check if `/uploads` directory exists
2. Verify file was uploaded successfully
3. Check image URL format: should start with `/uploads/`
4. Ensure server is running on correct port

### Upload fails?

1. Check file format (must be jpg, jpeg, png, gif, or webp)
2. Verify artisan authentication token
3. Check server logs for errors

### For Network Access (Lab Demo)

When using `--host 0.0.0.0`:

```bash
# Images will be accessible at:
http://YOUR_IP:8000/uploads/product_123_1701234567.jpg

# Example in buyer HTML:
<img src="http://192.168.1.100:8000/uploads/product_123_1701234567.jpg">
```

## Testing with cURL

### Upload Image

```bash
curl -X POST "http://localhost:8000/products/upload-image" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/image.jpg"
```

### Create Product with Image

```bash
curl -X POST "http://localhost:8000/products" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Product",
    "price": 100,
    "stock_quantity": 5,
    "cultural_motif": "Modern",
    "image_url": "/uploads/product_123_1701234567.jpg"
  }'
```
