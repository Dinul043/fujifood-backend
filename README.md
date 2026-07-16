# FujiFood Backend — White-Label Restaurant Commerce API

A multi-tenant restaurant platform API built with FastAPI, SQLAlchemy, and MySQL. Powers the customer storefront and restaurant admin panel with real-time WebSocket updates.

## Quick Setup (5 minutes)

**Prerequisites:** Python 3.10+, MySQL 8.0+

```bash
# 1. Clone the repository
git clone https://github.com/Dinul043/fujifood-backend.git
cd fujifood-backend

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install ALL dependencies
pip install -r requirements.txt

# 4. Create environment file
cp .env.example .env
# Edit .env — fill in DB_PASSWORD and other values

# 5. Create MySQL database
mysql -u root -p -e "CREATE DATABASE fujifood CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 6. Run database migrations (creates all 16 tables)
python -m alembic upgrade head

# 7. Seed demo data (creates tenant, restaurant, admin user)
python seed_demo.py

# 8. Start the server
python main.py
```

API available at [http://localhost:8000](http://localhost:8000)
Docs at [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

**If you get errors:**
- `bcrypt` install fails on Windows: `pip install bcrypt --only-binary :all:`
- MySQL connection refused: ensure MySQL is running and password in `.env` is correct
- `ModuleNotFoundError`: run `pip install -r requirements.txt` again

## Environment Variables (.env)

```env
# App
DEBUG=True
ENVIRONMENT=development

# Database (MySQL)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=fujifood
DB_USER=root
DB_PASSWORD=your_mysql_password

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# Email (Mailtrap sandbox for dev)
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=587
SMTP_USER=your_mailtrap_user
SMTP_PASSWORD=your_mailtrap_password
FROM_EMAIL=noreply@fujifood.com

# Razorpay (test keys)
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=your_razorpay_secret
```

## Tech Stack

- **Framework:** FastAPI 0.115
- **ORM:** SQLAlchemy 2.0 (sync)
- **Database:** MySQL 8.0 (PyMySQL driver)
- **Migrations:** Alembic
- **Auth:** JWT (python-jose), bcrypt password hashing
- **Payment:** Razorpay SDK
- **Real-time:** WebSocket (native FastAPI)
- **Email:** SMTP (Mailtrap in dev)
- **File Upload:** Local disk (uploads/ directory)
## Folder Structure

```
fujifood-backend/
├── main.py                       # Entry point — runs uvicorn
├── requirements.txt              # Python dependencies
├── seed_demo.py                  # Seeds demo tenant + restaurant + admin user
├── alembic.ini                   # Alembic configuration
├── .env.example                  # Environment variables template
├── uploads/                      # Uploaded menu images (served as static files)
│
├── alembic/                      # Database migrations
│   ├── env.py                    # Alembic environment config
│   └── versions/                 # Migration files (001-016)
│       ├── 001_create_tenants_table.py
│       ├── 002_create_users_table.py
│       ├── 003_create_restaurants_table.py
│       ├── 004_create_menu_categories_table.py
│       ├── 005_create_menu_items_table.py
│       ├── 006_create_orders_table.py
│       ├── 007_create_order_items_table.py
│       ├── 008_create_themes_table.py
│       ├── 009_create_otp_tokens_table.py
│       ├── 010_create_refresh_tokens_table.py
│       ├── 011_create_user_addresses_table.py
│       ├── 012_create_business_hours_table.py
│       ├── 013_add_purpose_to_otp_tokens.py
│       ├── 014_create_password_reset_tokens_table.py
│       ├── 015_add_unique_email_per_tenant.py
│       └── 016_add_is_owner_to_users.py
│
├── app/
│   ├── main.py                   # FastAPI app creation, CORS, router registration
│   ├── __init__.py
│   │
│   ├── api/                      # API layer
│   │   └── v1/
│   │       ├── router.py         # Aggregates all route modules
│   │       ├── deps.py           # Dependency injection (get_current_user, require_role)
│   │       └── routes/
│   │           ├── auth.py       # Login (admin phone+pw, customer OTP), refresh, /me, profile
│   │           ├── orders.py     # Place order, my-orders, manage orders, update status
│   │           ├── menu.py       # Categories CRUD, items CRUD, public storefront menu
│   │           ├── restaurants.py# Public restaurant info, admin manage/update
│   │           ├── payment.py    # Razorpay order creation, verification, refunds
│   │           ├── geocode.py    # Delivery radius check (Haversine)
│   │           ├── tenants.py    # Tenant provisioning (internal)
│   │           ├── themes.py     # Theme CRUD (future website studio)
│   │           ├── staff.py      # Staff management (owner adds/removes staff)
│   │           ├── upload.py     # Image file upload (menu items)
│   │           └── websocket.py  # WebSocket endpoints (admin + customer)
│   │
│   ├── core/                     # Core infrastructure
│   │   ├── config.py             # Settings from .env (Pydantic BaseSettings)
│   │   ├── database.py           # SQLAlchemy engine + session factory
│   │   └── security.py          # JWT encode/decode, password hashing
│   │
│   ├── models/                   # SQLAlchemy ORM models (15 tables)
│   │   ├── base.py               # BaseModel with UUID, IST timestamps, soft delete
│   │   ├── tenant.py             # Tenant (SaaS account)
│   │   ├── user.py               # User (customer + restaurant_admin, is_owner flag)
│   │   ├── restaurant.py         # Restaurant profile (location, delivery settings)
│   │   ├── menu.py               # MenuCategory + MenuItem
│   │   ├── order.py              # Order + OrderItem
│   │   ├── otp_token.py          # OTP codes (5 min expiry)
│   │   ├── refresh_token.py      # JWT refresh tokens
│   │   ├── password_reset_token.py # Password reset OTPs
│   │   ├── user_address.py       # Customer saved addresses
│   │   ├── business_hours.py     # Restaurant operating hours
│   │   └── theme.py              # Theme configuration
│   │
│   ├── schemas/                  # Pydantic request/response DTOs
│   │   ├── auth.py               # Login, OTP, token, profile schemas
│   │   ├── order.py              # PlaceOrder, UpdateStatus, OrderResponse
│   │   ├── menu.py               # Category/Item CRUD schemas
│   │   ├── restaurant.py         # Restaurant update/response schemas
│   │   ├── tenant.py             # Tenant provisioning schema
│   │   └── theme.py              # Theme schemas
│   │
│   ├── services/                 # Business logic layer
│   │   ├── auth_service.py       # Login, OTP, token creation, password reset
│   │   ├── order_service.py      # Place order, cancel, status transitions
│   │   ├── menu_service.py       # Menu CRUD, public menu
│   │   ├── payment_service.py    # Razorpay integration
│   │   ├── restaurant_service.py # Restaurant profile management
│   │   ├── tenant_service.py     # Tenant + restaurant + admin provisioning
│   │   ├── theme_service.py      # Theme CRUD
│   │   └── websocket_manager.py  # WebSocket connection manager (singleton)
│   │
│   ├── utils/                    # Utility functions
│   │   ├── email.py              # Send email via SMTP
│   │   └── geo.py                # Haversine distance calculation
│   │
│   └── repositories/             # (Architecture-ready, base pattern)
│       └── base.py               # Generic repository base class
│
└── tests/                        # Test structure (pytest)
    ├── unit/
    └── integration/
```

## Database (15 Tables)

| Table | Purpose |
|-------|---------|
| tenants | SaaS accounts (one per restaurant) |
| users | All users (customers + admins). `is_owner` flag for owner vs staff |
| restaurants | Restaurant profile, location, delivery settings |
| menu_categories | Food categories (Starters, Main Course, etc.) |
| menu_items | Individual dishes with price, image, availability |
| orders | Order header (status, amounts, payment) |
| order_items | Line items per order |
| otp_tokens | Email OTP codes (5 min expiry) |
| refresh_tokens | JWT refresh tokens (revokable) |
| password_reset_tokens | Password reset OTP codes |
| user_addresses | Customer saved delivery addresses |
| business_hours | Restaurant operating hours |
| themes | Website theme configuration |

## API Endpoints (52 total)

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/admin/login | Admin login (phone + password) |
| POST | /api/v1/auth/customer/login | Customer login (email + password) |
| POST | /api/v1/auth/otp/send | Send OTP to email |
| POST | /api/v1/auth/otp/verify | Verify OTP, get tokens |
| POST | /api/v1/auth/refresh | Refresh access token |
| GET | /api/v1/auth/me | Get current user profile |
| PATCH | /api/v1/auth/profile | Update name/phone/password |
| POST | /api/v1/auth/forgot-password | Send reset OTP |
| POST | /api/v1/auth/reset-password | Reset with OTP + new password |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/orders/place | Place new order (triggers WebSocket to admin) |
| GET | /api/v1/orders/my-orders | Customer's order history |
| POST | /api/v1/orders/my-orders/{id}/cancel | Cancel order (triggers WebSocket) |
| GET | /api/v1/orders/manage | Admin: list all orders |
| PATCH | /api/v1/orders/manage/{id}/status | Admin: update status (triggers WebSocket to customer) |

### Menu
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/menu/storefront/{slug} | Public full menu |
| GET | /api/v1/menu/manage/categories | Admin: list categories |
| POST | /api/v1/menu/manage/categories | Admin: create category |
| PATCH | /api/v1/menu/manage/categories/{id} | Admin: update category |
| DELETE | /api/v1/menu/manage/categories/{id} | Admin: delete category |
| GET | /api/v1/menu/manage/items | Admin: list items |
| POST | /api/v1/menu/manage/items | Admin: create item |
| PATCH | /api/v1/menu/manage/items/{id} | Admin: update item |
| DELETE | /api/v1/menu/manage/items/{id} | Admin: delete item |
| POST | /api/v1/menu/manage/items/{id}/toggle | Admin: toggle availability |

### Restaurant
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/restaurants/storefront/{slug} | Public restaurant info |
| GET | /api/v1/restaurants/manage | Admin: get own restaurant |
| PATCH | /api/v1/restaurants/manage | Admin: update restaurant |
| POST | /api/v1/restaurants/manage/go-online | Start accepting orders |
| POST | /api/v1/restaurants/manage/go-offline | Stop accepting orders |

### Payment
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/payment/create-order | Create Razorpay order |
| POST | /api/v1/payment/verify | Verify payment signature |

### Staff (Owner only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/staff/ | List all staff |
| POST | /api/v1/staff/ | Add staff member |
| PATCH | /api/v1/staff/{id} | Update staff |
| DELETE | /api/v1/staff/{id} | Deactivate staff |

### Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/geo/check-delivery | Check if location is within delivery radius |
| POST | /api/v1/upload/image | Upload menu item image |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| ws://host/ws/admin/{tenant_id} | Admin: new order + cancel notifications |
| ws://host/ws/customer/{user_id} | Customer: order status updates |

## Default Admin Credentials

```
Phone: 9876543210
Password: Admin@123
Role: restaurant_admin (is_owner: true)
Tenant: a2b
```

## Architecture Decisions

- **Multi-tenant:** All tables have `tenant_id`. Data is always scoped per restaurant.
- **IST Timestamps:** `created_at`, `updated_at` stored in India Standard Time.
- **Soft Delete:** `deleted_at` column on all tables — records are never physically deleted.
- **UUID:** Every record has a public UUID (used in URLs), separate from integer ID (used internally).
- **Owner vs Staff:** `is_owner` boolean on users table. Owner sees revenue/history/reports/staff. Staff sees orders/menu/dashboard only.
- **WebSocket:** Singleton `ws_manager` handles connections. Notifications triggered from order routes after DB commit.

## Running in Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Common Issues

- **bcrypt install error on Windows:** Run `pip install bcrypt --only-binary :all:`
- **MySQL connection refused:** Ensure MySQL service is running and credentials are correct
- **Alembic "already exists":** Run `python -m alembic stamp head` then `python -m alembic upgrade head`
