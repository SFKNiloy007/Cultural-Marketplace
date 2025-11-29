# ✅ Product Image Feature - Implementation Complete

## What Was Added

### 1. **Database Schema Update**

- ✅ Created migration file: `add_product_images.sql`
- Adds `image_url` column to Product table

### 2. **Backend Changes (main.py)**

- ✅ Added image upload endpoint: `POST /products/upload-image`
- ✅ Updated product creation to include `image_url`
- ✅ Updated product listing to return `image_url`
- ✅ Added static file serving for `/uploads` directory
- ✅ Validates file types (jpg, jpeg, png, gif, webp)
- ✅ Generates unique filenames to prevent conflicts

### 3. **Directory Structure**

- ✅ Created `/uploads` directory for storing product images

### 4. **Documentation & Testing**

- ✅ `PRODUCT_IMAGES_GUIDE.md` - Complete usage guide
- ✅ `test_image_upload.html` - Interactive testing interface

---

## 🚀 Quick Start Guide

### Step 1: Update Database Schema

Run this in pgAdmin Query Tool:

```sql
ALTER TABLE Product ADD COLUMN image_url VARCHAR(500);
```

Or use psql:

```bash
psql -U postgres -d your_database_name -f add_product_images.sql
```

### Step 2: Restart Your Server

```bash
cd H:\EWU\CSE347\Project
python -m uvicorn main:app --reload
```

### Step 3: Test the Feature

1. **Open** `test_image_upload.html` in your browser
2. **Login** as an artisan to get a JWT token
3. **Paste** the token in the form
4. **Upload** an image → Get image URL
5. **Create** product with the image URL

---

## 📋 How It Works

### For Artisans (Creating Products with Images)

**Two-Step Process:**

1. **Upload Image First**

   ```javascript
   POST /products/upload-image
   Headers: { Authorization: Bearer TOKEN }
   Body: FormData with 'file'

   Response: { "image_url": "/uploads/product_123_1701234567.jpg" }
   ```

2. **Create Product with Image URL**
   ```javascript
   POST /products
   Body: {
     "name": "Product Name",
     "price": 2500,
     "stock_quantity": 10,
     "cultural_motif": "Traditional",
     "image_url": "/uploads/product_123_1701234567.jpg"  // From step 1
   }
   ```

### For Buyers (Viewing Product Images)

When buyers fetch products, they automatically get the image URL:

```javascript
GET /products

Response: [
  {
    "product_id": 1,
    "name": "Handwoven Nakshi Katha",
    "price": 2500.0,
    "image_url": "/uploads/product_123_1701234567.jpg",  // ← New field
    ...
  }
]
```

Display in HTML:

```html
<img
  src="http://localhost:8000/uploads/product_123_1701234567.jpg"
  alt="Product Name"
/>
```

---

## 🔐 Security Features

✅ **Authentication Required** - Only logged-in artisans can upload  
✅ **File Type Validation** - Server checks file extensions  
✅ **Unique Filenames** - Timestamp prevents overwriting  
✅ **Ownership Verification** - Only product owner can update images

---

## 🌐 For Lab Demo (Network Access)

When running with `--host 0.0.0.0`:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Images will be accessible from other devices:

```html
<!-- Get your IP with: ipconfig -->
<img src="http://192.168.1.100:8000/uploads/product_123_1701234567.jpg" />
```

---

## 📁 File Structure

```
H:\EWU\CSE347\Project\
├── main.py                      (✓ Updated with image features)
├── add_product_images.sql       (✓ Database migration)
├── PRODUCT_IMAGES_GUIDE.md      (✓ Complete documentation)
├── test_image_upload.html       (✓ Testing interface)
└── uploads/                     (✓ Created for storing images)
    └── (product images stored here)
```

---

## 🎯 Next Steps

1. **Run database migration** (`add_product_images.sql`)
2. **Restart server**
3. **Test with** `test_image_upload.html`
4. **Update buyer.html** to display product images
5. **Update artisan.html** to include image upload in product creation form

---

## 💡 Frontend Integration Examples

### Artisan Dashboard - Product Creation Form

```html
<form id="productForm">
  <input type="file" id="productImage" accept="image/*" />
  <button type="button" onclick="uploadImageFirst()">Upload Image</button>

  <input type="text" id="productName" placeholder="Product Name" />
  <input type="number" id="productPrice" placeholder="Price" />
  <input type="number" id="stockQuantity" placeholder="Stock" />
  <input type="text" id="culturalMotif" placeholder="Cultural Motif" />
  <input type="hidden" id="imageUrl" />
  <!-- Hidden, auto-filled -->

  <button type="submit">Create Product</button>
</form>

<script>
  async function uploadImageFirst() {
    const fileInput = document.getElementById("productImage");
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const response = await fetch(
      "http://localhost:8000/products/upload-image",
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      }
    );

    const data = await response.json();
    document.getElementById("imageUrl").value = data.image_url;
    alert("Image uploaded! Now create the product.");
  }
</script>
```

### Buyer Page - Product Display

```html
<div class="product-grid">
  <!-- This gets populated from /products API -->
</div>

<script>
  async function loadProducts() {
    const response = await fetch("http://localhost:8000/products");
    const products = await response.json();

    const grid = document.querySelector(".product-grid");

    products.forEach((product) => {
      const card = document.createElement("div");
      card.className = "product-card";
      card.innerHTML = `
      <img src="http://localhost:8000${
        product.image_url || "/static/placeholder.jpg"
      }" 
           alt="${product.name}"
           onerror="this.src='/static/placeholder.jpg'">
      <h3>${product.name}</h3>
      <p class="price">৳${product.price}</p>
      <p>${product.cultural_motif}</p>
      <button onclick="buyProduct(${product.product_id})">Buy Now</button>
    `;
      grid.appendChild(card);
    });
  }

  loadProducts();
</script>
```

---

## 🐛 Troubleshooting

| Issue                             | Solution                                      |
| --------------------------------- | --------------------------------------------- |
| "Column image_url does not exist" | Run the SQL migration file                    |
| Images not displaying             | Check if `/uploads` directory exists          |
| Upload fails                      | Verify file format (jpg, png, gif, webp only) |
| 401 Unauthorized                  | Check JWT token is valid and not expired      |
| 403 Forbidden                     | Only artisans can upload images               |

---

## ✨ Features Summary

✅ Artisans can upload product images  
✅ Images stored securely in `/uploads` directory  
✅ Unique filenames prevent conflicts  
✅ Buyers see product images automatically  
✅ Images work on local network (lab demo ready)  
✅ File type validation for security  
✅ Complete documentation and test files

**All code changes are complete and ready to use!**
