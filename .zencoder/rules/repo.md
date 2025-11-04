# CfpaZMS - نظام إدارة المؤسسات الشاملة
## Comprehensive Institutional Management System

### Project Type
**Python Flask Web Application**

### Technology Stack
- **Backend:** Python 3 + Flask
- **Frontend:** Bootstrap 5 + HTML/Jinja2
- **Database:** SQLAlchemy ORM (configured for PostgreSQL/MySQL)
- **Language Support:** Arabic (RTL) + English
- **UI Framework:** Bootstrap 5 with RTL support

### Target Framework for E2E Tests
**Playwright** (Python)

---

## Project Structure

### Root Files
- `app.py` - Flask application entry point
- `config.py` - Configuration settings
- `models.py` - SQLAlchemy database models
- `requirements.txt` - Python dependencies

### Routes Directory (`/routes`)
Organized by functional module:
- `admin.py` - Administration & user management
- `auth.py` - Authentication & login
- `dashboard.py` - Dashboard/home page
- `equipment.py` - Equipment/assets management
- `inventory.py` - Inventory & stock management
- `reports.py` - Reports generation
- `restaurant.py` - Restaurant/meal management
- `suppliers.py` - Supplier/vendor management
- `__init__.py` - Route initialization

### Templates Directory (`/templates`)

#### Base Template
- `base.html` - Master template with RTL support, navbar, sidebar, color scheme (#1a3a52 primary, #2e5f8a secondary)

#### Admin Module (`/admin`)
- `users.html` - User listing with search, filter by role/status, pagination
- `add_user.html` - New user registration with bilingual name fields, role selection, permissions
- `edit_user.html` - User modification with all fields pre-populated
- `activity_logs.html` - Audit trail with date range filtering, action type filters
- `organization_settings.html` - Editable organization hierarchy (Ministry/Directorate/Institution names in Arabic/English)

#### Authentication Module (`/auth`)
- `login.html` - Login form with gradient background
- `user_profile.html` - User profile with sections for personal info, password change, permissions display

#### Dashboard Module (`/dashboard`)
- `index.html` - Main dashboard with system statistics and quick actions

#### Inventory Module (`/inventory`)
- `items.html` - Inventory item list with search, category filtering, stock levels display
- `add_item.html` - New item form with code, name, category, unit, min quantity, unit price
- `edit_item.html` - Item modification with current quantity/value display
- `categories.html` - Item categories listing with search, item count per category
- `add_category.html` - New category form with code, type, bilingual description
- `edit_category.html` - Category modification with item count display
- `transactions.html` - Stock movements audit trail (purchases, issues, transfers, returns, adjustments) with date range and type filtering
- `add_transaction.html` - Stock transaction form with auto unit population, source/destination locations, availability warnings

#### Equipment Module (`/equipment`)
- `assets.html` - Asset registry with search, category/status filtering, depreciation calculations
- `add_asset.html` - New asset form organized by: basic info, financial info, location/assignment, status/warranty
- `edit_asset.html` - Asset modification (serial number locked, all other fields editable)

#### Restaurant Module (`/restaurant`)
- `recipes.html` - Recipe card grid with search, meal type filtering
- `add_recipe.html` - Recipe form with ingredient dynamic rows, preparation steps, nutritional info
- `meals.html` - Daily meal registrations with summary statistics (meal type counts, daily cost), ingredients consumption modal
- `add_meal.html` - Daily meal registration form with recipe selection, automatic cost/serving calculation

#### Suppliers Module (`/suppliers`)
- `suppliers.html` - Supplier list with search (name/phone/tax ID), status filtering (active/inactive/suspended), pagination
- `add_supplier.html` - New supplier form with sections: basic info, contact details, legal info, banking, payment terms, notes
- `edit_supplier.html` - Supplier modification with metadata display (creation/modification dates, order count)

#### Reports Module (`/reports`)
- `inventory_movement.html` - Stock movement report with transaction type breakdown, summary cards, detailed transaction table, print support
- `low_stock_report.html` - Low inventory alerts with status indicators (critical/warning/normal), quick add transaction links
- `asset_inventory.html` - Asset inventory with category/status/responsible person filtering, warranty expiry indicators, print support
- `meal_consumption.html` - Restaurant consumption analytics with meal type breakdown, top recipes, detailed meals table

#### Error Pages (Root `/templates`)
- `404.html` - Page not found with home link
- `403.html` - Access denied with home link
- `500.html` - Server error with home link

---

## Key Features

### 1. User Management & Permissions
- Role-based access control (RBAC)
- Bilingual user data (Arabic/English names)
- Activity logging for audit trails
- Status tracking (active/inactive)

### 2. Inventory Management
- Item categorization (office equipment, electronics, consumables, food items, etc.)
- Stock level tracking with minimum quantity alerts
- Transaction logging (purchases, issues, transfers, returns, adjustments)
- Real-time stock balance calculations
- Unit-based measurements support

### 3. Supplier Management
- Comprehensive supplier registry
- Tax ID and commercial register tracking
- Banking information storage
- Payment terms management
- Status tracking (active/inactive/suspended)
- Contact person assignment

### 4. Equipment/Assets Management
- Asset registration with serial numbers
- Depreciation tracking
- Category-based organization (computer, printer, furniture, vehicle, etc.)
- Status tracking (in use, damaged, maintenance, retired)
- Warranty expiry monitoring
- Responsible party assignment

### 5. Restaurant Operations
- Recipe management with ingredients
- Daily meal registration
- Ingredient consumption tracking
- Cost calculations and budget monitoring
- Meal type categorization (breakfast, lunch, dinner, snack)

### 6. Reporting & Analytics
- Inventory movement reports with date range filtering
- Low stock alerts with critical indicators
- Asset inventory reports with warranty monitoring
- Meal consumption analytics with cost breakdowns
- Print-friendly report layouts

### 7. Organization Hierarchy
- Editable ministry, directorate, and institution names
- Bilingual support for all organizational levels
- Dynamic display in all documents and reports

---

## Design Patterns

### Form Organization
- Consistent card-based sections
- Required field indicators (*)
- Help text and validation messages
- Modal-based dialogs for actions

### Data Display
- Responsive tables with hover effects
- Search & filter functionality
- Pagination for large datasets
- Badge-based status indicators

### Color Scheme
- Primary: `#1a3a52` (dark blue)
- Secondary: `#2e5f8a` (medium blue)
- Success: `#27ae60`
- Danger: `#e74c3c`
- Warning: `#f39c12`
- Info: `#3498db`

### RTL Support
- All templates use `dir="rtl"` and `lang="ar"`
- Arabic-first labels and form fields
- Bootstrap RTL CSS included
- Right-aligned content by default

---

## API Routes (Expected Backend Implementation)

### Authentication (`/auth`)
- `POST /login` - User login
- `GET/POST /profile` - User profile view/update
- `POST /change-password` - Password change

### Admin (`/admin`)
- `GET /users` - List users
- `POST /users/add` - Create user
- `POST /users/<id>/edit` - Update user
- `POST /users/<id>/delete` - Delete user
- `GET /users/<id>/delete` - Delete via GET
- `GET /activity-logs` - Activity log view
- `GET/POST /settings` - Organization settings

### Inventory (`/inventory`)
- `GET /items` - List items with pagination
- `POST /items/add` - Create item
- `POST /items/<id>/edit` - Update item
- `GET /items/<id>/delete` - Delete item
- `GET /categories` - List categories
- `POST /categories/add` - Create category
- `POST /categories/<id>/edit` - Update category
- `GET /transactions` - List transactions
- `POST /transactions/add` - Record transaction
- `POST /transactions/<id>/edit` - Update transaction

### Suppliers (`/suppliers`)
- `GET /` - List suppliers with search/filter
- `POST /add` - Create supplier
- `POST /<id>/edit` - Update supplier
- `GET /<id>/delete` - Delete supplier

### Equipment (`/equipment`)
- `GET /` - List assets with filtering
- `POST /add` - Register asset
- `POST /<id>/edit` - Update asset
- `GET /<id>/delete` - Delete asset

### Restaurant (`/restaurant`)
- `GET /recipes` - List recipes
- `POST /recipes/add` - Create recipe
- `POST /recipes/<id>/edit` - Update recipe
- `GET /meals` - List daily meals
- `POST /meals/add` - Register meal
- `POST /meals/<id>/edit` - Update meal

### Reports (`/reports`)
- `GET /inventory-movement` - Inventory movement report
- `GET /low-stock` - Low stock report
- `GET /asset-inventory` - Asset inventory report
- `GET /meal-consumption` - Meal consumption report

### Dashboard (`/dashboard`)
- `GET /` - Main dashboard

---

## Database Models (Expected)

### User
- `id`, `username`, `email`, `password_hash`, `full_name`, `phone`
- `role`, `department`, `is_active`, `created_at`, `updated_at`, `last_login`

### InventoryItem
- `id`, `code`, `name`, `description`, `category_id`
- `unit`, `min_quantity`, `unit_price`, `current_quantity`, `created_at`

### InventoryCategory
- `id`, `code`, `name`, `type`, `description_ar`, `description_en`

### Transaction
- `id`, `item_id`, `type`, `quantity`, `reference_number`
- `date`, `location_from`, `location_to`, `created_by`, `created_at`

### Supplier
- `id`, `name`, `category`, `phone`, `email`, `contact_person`
- `tax_id`, `commercial_register`, `address`, `bank_name`, `bank_account`
- `bank_account_holder`, `iban`, `payment_terms`, `discount_rate`, `notes`, `status`
- `created_at`, `updated_at`

### Equipment/Asset
- `id`, `serial_number`, `category`, `name`, `description`
- `purchase_date`, `original_value`, `depreciation_rate`, `location`
- `assigned_to`, `status`, `warranty_expiry`, `supplier_id`, `notes`, `created_at`

### Recipe
- `id`, `name`, `name_en`, `meal_type`, `serving_size`, `description`
- `ingredients` (JSON or related table), `preparation_steps`, `calories`, `estimated_cost`

### Meal
- `id`, `date`, `meal_type`, `recipe_id`, `portions`, `expected_cost`, `notes`, `created_at`

### OrganizationSettings
- `ministry_name`, `ministry_name_en`
- `directorate_name`, `directorate_name_en`
- `institution_name`, `institution_name_en`
- `institution_code`, `tax_id`, `logo_url`, `address`, `contact_info`

---

## Configuration Notes

### Required Environment Variables
```
FLASK_APP=app.py
FLASK_ENV=development/production
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost/cfpa_zms
```

### Key Jinja2 Filters
- `currency` - Format numbers as currency
- `date` formatting - Display dates in DD/MM/YYYY format
- `strftime` - Custom date formatting

### JavaScript Features
- Dynamic form row addition/removal (ingredients, recipe steps)
- Auto-population of fields based on dropdown selection
- Date/time picker initialization
- Real-time calculations (costs, totals)
- Confirmation dialogs for destructive actions

---

## Testing Strategy

### Frontend Testing Areas
1. **Form Validation**
   - Required field validation
   - Format validation (email, phone, etc.)
   - Cross-field validation

2. **Search & Filtering**
   - Text search functionality
   - Multi-select filters
   - Filter persistence in pagination

3. **CRUD Operations**
   - Create operations with validation
   - Edit operations with data loading
   - Delete operations with confirmation
   - List operations with pagination

4. **Dynamic Content**
   - Dropdown population based on selection
   - Automatic field calculation
   - Ingredient/row management (add/remove)

5. **Navigation**
   - Menu links functionality
   - Breadcrumb navigation
   - Back/cancel button behavior

6. **Responsive Design**
   - RTL layout verification
   - Mobile responsiveness
   - Print layout functionality

---

## Coding Conventions

1. **Templates**
   - Arabic labels first (RTL-friendly)
   - Bilingual support where applicable
   - Card-based layouts for sections
   - Color-coded status badges
   - Consistent form structure

2. **CSS/Styling**
   - Bootstrap utility classes
   - Custom CSS in `<style>` blocks
   - Color variables in CSS custom properties
   - Print media queries for report layouts

3. **JavaScript**
   - Minimal vanilla JS for interactions
   - Bootstrap modal/dropdown integration
   - Form validation before submission
   - Confirmation for destructive actions

4. **Security**
   - CSRF protection (Flask-WTF assumed)
   - Input validation on forms
   - Permission checks on routes
   - Secure password handling

---

## Completion Status

✅ **Complete Modules:**
- Base template with RTL support
- Admin module (users, settings, activity logs)
- Authentication (login, user profile)
- Dashboard
- Inventory management (items, categories, transactions)
- Equipment/assets management (assets, issues/assignments)
- Supplier management (suppliers, purchase orders)
- Restaurant operations (recipes, meals)
- All reports (inventory movement, low stock, asset inventory, meal consumption)
- Error pages (404, 403, 500)

### Recent Template-Route Fixes and Additions

**Fixed Template Issues:**
1. **inventory/add_transaction.html** - Added missing `unit_price` field that route processes; removed reference to non-existent `transaction_date` field
2. **suppliers/add_supplier.html** - Fixed incorrect route reference from `suppliers.list_suppliers` to `suppliers.suppliers`

**Created Missing Templates:**
1. **reports/index.html** - Main reports page with links to all available reports
2. **suppliers/orders.html** - Purchase orders list with status filtering and pagination
3. **suppliers/add_order.html** - Add new purchase order form
4. **suppliers/edit_order.html** - Edit purchase order with order items display
5. **equipment/issues.html** - Item issues (assignments) list with user filtering
6. **equipment/add_issue.html** - Issue (assign) equipment to employee form
7. **equipment/return_issue.html** - Return equipment form with condition tracking

All templates now have exact field alignment with their corresponding route handlers.

⏳ **Recommended Enhancements:**
- Email notifications for low stock alerts
- QR code/barcode support for assets
- PDF export functionality
- Real-time dashboard updates
- API documentation (Swagger/OpenAPI)
- Integration with external accounting systems

---

**Last Updated:** 2024
**Status:** Frontend UI layer complete, ready for backend route implementation and testing