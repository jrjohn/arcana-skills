# Specification-Driven UI Generation Guide

This guide explains how to automatically generate complete UI/UX screen series from SRS (Software Requirements Specification), SDD (Software Design Document), or other specification documents.

## Table of Contents
1. [Supported Document Formats](#supported-document-formats)
2. [Specification Document Parsing Workflow](#specification-document-parsing-workflow)
3. [SRS Document Parsing](#srs-document-parsing)
4. [SDD Document Parsing](#sdd-document-parsing)
5. [Requirements to UI Mapping](#requirements-to-ui-mapping)
6. [Batch UI Generation](#batch-ui-generation)
7. [Output Directory Structure](#output-directory-structure)
8. [Generation Report Templates](#generation-report-templates)

---

## Supported Document Formats

### Parseable Specification Document Types

```
Supported Formats
+-- Markdown (.md)
|   +-- SRS-*.md (Software Requirements Specification)
|   +-- SDD-*.md (Software Design Document)
|   +-- PRD-*.md (Product Requirements Document)
|   +-- FSD-*.md (Functional Specification Document)
|   +-- *.md (Other specification documents)
|
+-- Word Documents (.docx)
|   +-- SRS-*.docx
|   +-- SDD-*.docx
|   +-- PRD-*.docx
|   +-- *.docx
|
+-- PDF (.pdf)
|   +-- Various specification documents
|
+-- Other
    +-- .txt (Plain text)
    +-- .json (Structured specifications)
```

### Document Type Descriptions

| Document Type | Full Name | Main Content | UI Generation Focus |
|---------------|-----------|--------------|---------------------|
| **SRS** | Software Requirements Specification | Functional requirements, user stories, use cases | Feature screens, workflows |
| **SDD** | Software Design Document | System architecture, screen specs, data models | Detailed screen design |
| **PRD** | Product Requirements Document | Product vision, feature list, priorities | Feature scope, MVP |
| **FSD** | Functional Specification Document | Detailed functional specs, business rules | Interaction logic, validation |
| **Wireframe Doc** | Wireframe Document | Screen layouts, component arrangements | Visual implementation |

---

## Specification Document Parsing Workflow

### Overall Workflow

```
+-------------------------------------------------------------------+
|                Specification-Driven UI Generation Workflow         |
+-------------------------------------------------------------------+
|                                                                   |
|  Input Specification Document                                     |
|  (SRS/SDD/PRD.md or .docx)                                       |
|           |                                                       |
|           v                                                       |
|  +-------------------+                                            |
|  |  Document Parsing |                                            |
|  |  ---------------  |                                            |
|  |  - Structure ID   |                                            |
|  |  - Section extract|                                            |
|  |  - Requirements   |                                            |
|  +--------+----------+                                            |
|           |                                                       |
|           v                                                       |
|  +-------------------+                                            |
|  | Requirements      |                                            |
|  | Analysis          |                                            |
|  |  ---------------  |                                            |
|  |  - Feature list   |                                            |
|  |  - User roles     |                                            |
|  |  - Flow ID        |                                            |
|  |  - Screen derive  |                                            |
|  +--------+----------+                                            |
|           |                                                       |
|           v                                                       |
|  +-------------------+                                            |
|  |   UI Planning     |                                            |
|  |  ---------------  |                                            |
|  |  - Screen list    |                                            |
|  |  - Flow diagrams  |                                            |
|  |  - Component reqs |                                            |
|  |  - Style confirm  |                                            |
|  +--------+----------+                                            |
|           |                                                       |
|           v                                                       |
|  +-------------------+                                            |
|  |  Batch Generation |                                            |
|  |  ---------------  |                                            |
|  |  - Generate screens|                                           |
|  |  - Apply styles   |                                            |
|  |  - Multi-format   |                                            |
|  +--------+----------+                                            |
|           |                                                       |
|           v                                                       |
|  Output Directory                                                 |
|  +-- generated-ui/                                                |
|      +-- html/                                                    |
|      +-- react/                                                   |
|      +-- swiftui/                                                 |
|      +-- compose/                                                 |
|      +-- report.md                                                |
|                                                                   |
+-------------------------------------------------------------------+
```

### Parsing Steps

```
Step 1: Document Reading
        +-- Identify document format (.md/.docx/.pdf)
        +-- Read document content
        +-- Convert to unified format

Step 2: Structure Parsing
        +-- Identify section headings
        +-- Extract table data
        +-- Parse list items
        +-- Identify images/flowcharts

Step 3: Requirements Extraction
        +-- Extract functional requirements (FR)
        +-- Extract user stories (User Story)
        +-- Extract use cases (Use Case)
        +-- Extract screen specifications (Screen Spec)
        +-- Extract business rules (Business Rule)

Step 4: UI Mapping
        +-- Requirements -> Screen mapping
        +-- Flows -> Navigation structure
        +-- Data -> Forms/Lists
        +-- Rules -> Validation/States

Step 5: Batch Generation
        +-- Create output directories
        +-- Generate screens sequentially
        +-- Generate navigation/routing
        +-- Output generation report
```

---

## SRS Document Parsing

### Common SRS Structure

```markdown
# Typical SRS Section Structure

1. Introduction
   1.1 Purpose
   1.2 Scope
   1.3 Definitions and Abbreviations

2. Overall Description
   2.1 Product Perspective
   2.2 Product Features        <- [Important] Feature List
   2.3 User Classes            <- [Important] User Roles
   2.4 Operating Environment
   2.5 Constraints

3. Functional Requirements    <- [Core]
   3.1 User Stories
   3.2 Use Case Descriptions
   3.3 Functional Specifications

4. External Interface Requirements
   4.1 User Interface         <- [Important] UI Specs
   4.2 Hardware Interface
   4.3 Software Interface
   4.4 Communication Interface

5. Non-functional Requirements
   5.1 Performance Requirements
   5.2 Security Requirements
   5.3 Usability Requirements <- [Reference] UX Requirements
```

### SRS Parsing Focus

#### 1. Functional Requirements Extraction

```markdown
## Content Extracted from SRS

### User Story Format
As a [user role]
I want to [feature description]
So that [value/purpose]

-> Extraction:
  - User role -> Determines screen permissions/entry
  - Feature description -> Maps to screens/features
  - Value purpose -> Determines UX focus

### Use Case Format
Use Case Name: UC-001 User Login
Primary Actor: General User
Preconditions: User has registered
Main Flow:
  1. User opens App
  2. System displays login screen
  3. User enters username and password
  4. System validates
  5. Login successful, redirect to home
Alternative Flows:
  3a. User selects social login
  4a. Validation fails, show error

-> Extraction:
  - Use case name -> Feature module
  - Main flow -> Screen flow
  - Alternative flows -> Branches/error states
```

#### 2. Feature List Extraction

```markdown
## SRS Feature List Example

| ID | Feature Name | Description | Priority |
|----|--------------|-------------|----------|
| FR-001 | User Registration | New users can register via Email | Must |
| FR-002 | User Login | Users can login via Email/password | Must |
| FR-003 | Social Login | Support Google/Apple login | Should |
| FR-004 | Forgot Password | Users can reset password | Must |
| FR-005 | Browse Products | Users can browse product list | Must |
| FR-006 | Search Products | Users can search products | Must |
| FR-007 | Product Details | Users can view product details | Must |
| FR-008 | Add to Cart | Users can add products to cart | Must |
| FR-009 | Checkout | Users can complete purchase flow | Must |
| FR-010 | Order Inquiry | Users can check order status | Should |

-> Auto-derived Screens:
  - FR-001 -> Registration page (multi-step)
  - FR-002 -> Login page
  - FR-003 -> Social login buttons (integrated into login page)
  - FR-004 -> Forgot password flow (3 pages)
  - FR-005 -> Product list page
  - FR-006 -> Search page/search results
  - FR-007 -> Product details page
  - FR-008 -> Cart page
  - FR-009 -> Checkout flow (multi-page)
  - FR-010 -> Order list/order details
```

#### 3. User Role Extraction

```markdown
## User Class Example

| Role | Description | Main Features |
|------|-------------|---------------|
| Guest | Non-logged in user | Browse, search |
| Member | Registered user | Purchase, favorites, orders |
| VIP Member | Paid member | Exclusive offers, priority service |
| Admin | Backend administrator | Product management, order management |

-> Auto-derived:
  - Different navigation structures per role
  - Permission control screens
  - Role-specific feature pages
```

---

## SDD Document Parsing

### Common SDD Structure

```markdown
# Typical SDD Section Structure

1. Introduction
   1.1 Purpose
   1.2 Scope

2. System Architecture
   2.1 Architecture Overview
   2.2 Module Design

3. Data Design                <- [Important]
   3.1 Data Models
   3.2 Database Design

4. Interface Design           <- [Core]
   4.1 User Interface Design
   4.2 Screen Specifications
   4.3 Navigation Structure
   4.4 Interaction Design

5. Component Design
   5.1 Component Specifications
   5.2 API Design
```

### SDD Parsing Focus

#### 1. Screen Specification Extraction

```markdown
## SDD Screen Specification Example

### 4.2.1 Login Screen (SCR-001)

**Screen Name:** Login Screen
**Screen ID:** SCR-001
**Access Permission:** Public

**Screen Elements:**
| Element | Type | Description | Validation Rules |
|---------|------|-------------|------------------|
| Logo | Image | App Logo | - |
| Title | Text | "Welcome Back" | - |
| Email Input | TextField | User Email | Email format |
| Password Input | SecureField | User Password | Min 8 chars |
| Login Button | Button | Primary CTA | - |
| Forgot Password | Link | Navigate to forgot password | - |
| Google Login | Button | Social login | - |
| Apple Login | Button | Social login | - |
| Register Link | Link | Navigate to registration | - |

**Screen States:**
- Default: Initial empty state
- Loading: Login validation in progress
- Error: Login failed (show error message)
- Success: Login successful (redirect to home)

**Navigation:**
- Source: Splash screen, after logout
- Destination: Home (success), Registration page, Forgot password page

-> Directly generate screen code
```

#### 2. Navigation Structure Extraction

```markdown
## SDD Navigation Structure Example

### 4.3 Navigation Structure

```
App
+-- Public Area
|   +-- Splash Screen
|   +-- Onboarding
|   +-- Login
|   +-- Register
|   +-- Forgot Password
|
+-- Member Area (Login Required)
|   +-- Home
|   |   +-- Recommended Products
|   |   +-- Latest News
|   |
|   +-- Explore
|   |   +-- Category List
|   |   +-- Product List
|   |   +-- Search Results
|   |
|   +-- Cart
|   |   +-- Cart List
|   |   +-- Checkout Flow
|   |
|   +-- Profile
|       +-- Personal Info
|       +-- Order History
|       +-- Favorites
|       +-- Settings
|
+-- Admin Area (Admin Permission Required)
    +-- Dashboard
    +-- Product Management
    +-- Order Management
```

-> Auto-generate:
  - Tab Bar navigation
  - Navigation Stack
  - Routing configuration
```

#### 3. Data Model Extraction

```markdown
## SDD Data Model Example

### 3.1 Data Models

**User**
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| email | String | Email address |
| name | String | Full name |
| avatar | URL | Avatar image |
| createdAt | DateTime | Creation time |

**Product**
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Product name |
| description | String | Description |
| price | Decimal | Price |
| images | [URL] | Image list |
| category | Category | Category |

-> Auto-derived:
  - Form field configuration
  - List display fields
  - Detail page structure
```

---

## Requirements to UI Mapping

### Auto-Mapping Rules

```
+-------------------------------------------------------------------+
|                  Requirements -> UI Auto-Mapping                   |
+-------------------------------------------------------------------+
|                                                                   |
|  Requirement Type          ->    UI Screen                        |
|  ---------------------------------------------------------        |
|  User Registration         ->    Registration flow (1-3 pages)    |
|  User Login                ->    Login page + social login        |
|  Password Reset            ->    Forgot password flow (3 pages)   |
|  Browse List               ->    List page + filter + sort        |
|  Search Feature            ->    Search page + search results     |
|  View Details              ->    Detail page + recommendations    |
|  CRUD Operations           ->    List + Create + Edit + Details   |
|  Shopping Cart             ->    Cart page + quantity adjust      |
|  Checkout Flow             ->    Multi-step checkout (3-5 pages)  |
|  Order Management          ->    Order list + order details       |
|  Profile                   ->    Profile page + edit page         |
|  Settings                  ->    Settings list + setting pages    |
|  Notifications             ->    Notification list + details      |
|  Social Features           ->    Feed + post + interactions       |
|                                                                   |
+-------------------------------------------------------------------+
```

### Screen State Auto-Completion

```
Auto-generated states for each feature screen:

List Page States:
+-- Default (with data)
+-- Empty (empty state + CTA)
+-- Loading (loading + Skeleton)
+-- Error (error + retry)
+-- Refreshing (pull to refresh)
+-- LoadMore (load more)

Form Page States:
+-- Default (empty)
+-- Filled (with data)
+-- Validating (validation in progress)
+-- ValidationError (validation error)
+-- Submitting (submitting)
+-- SubmitSuccess (success)
+-- SubmitError (failure)

Detail Page States:
+-- Default (success)
+-- Loading (loading)
+-- Error (data not found)
```

### Mapping Example

```markdown
## Input: SRS Functional Requirement

FR-005: Browse Products
- Users can browse product list
- Support category filtering
- Support price sorting
- Display product image, name, price

## Output: UI Screen List

### SCR-010 Product List Page
- Page Type: List page
- Components:
  - Top: Search bar + filter button
  - Filter: Category filter sheet
  - Sort: Sort menu
  - List: Product card grid (2 columns)
  - Card: Image + name + price + favorite
- States: Default/Empty/Loading/Error/LoadMore
- Navigation: Tab Bar -> Home Tab

### SCR-011 Category Filter Sheet
- Page Type: Bottom Sheet
- Components: Category list (single/multi select)

### SCR-012 Sort Menu
- Page Type: Action Sheet
- Options: Recommended/Price low to high/Price high to low/Newest
```

---

## Batch UI Generation

### Generation Request Format

```markdown
## Specification-Driven UI Generation Request

### Input Document
- Document Path: /path/to/SRS-ProjectName-1.0.md
- Document Type: SRS (Software Requirements Specification)

### Output Settings
- Output Directory: /path/to/generated-ui/
- Output Formats:
  - [x] HTML + Tailwind
  - [x] React
  - [ ] SwiftUI
  - [ ] Jetpack Compose
- Style Settings:
  - Primary Color: #6366F1
  - Style: Modern minimalist
  - Border Radius: 12px

### Generation Scope
- [x] All features
- [ ] Specific features only: [feature list]

### Additional Options
- [x] Generate navigation/routing configuration
- [x] Generate component library
- [x] Generate generation report
- [ ] Apply extracted style
```

### Batch Generation Flow

```
1. Parse Specification Document
   +-- Read SRS/SDD
   +-- Extract functional requirements
   +-- Generate screen list

2. Confirm Generation Scope
   +-- Display screen list
   +-- Estimate screen count
   +-- User confirmation

3. Generate Screens Sequentially
   +-- Group by module
   +-- Sort by priority
   +-- Generate code one by one
   +-- Display progress

4. Generate Supporting Files
   +-- Routing configuration
   +-- Shared components
   +-- Theme settings
   +-- Type definitions

5. Output Report
   +-- Generation summary
   +-- Screen list
   +-- File directory
   +-- Recommendations
```

---

## Output Directory Structure

### Standard Output Directory

```
generated-ui/
|
+-- README.md                    # Generation report and usage guide
+-- SCREENS.md                   # Screen list and specifications
|
+-- html/                        # HTML + Tailwind output
|   +-- auth/                    # Auth module
|   |   +-- login.html
|   |   +-- register.html
|   |   +-- forgot-password.html
|   |   +-- reset-password.html
|   |
|   +-- home/                    # Home module
|   |   +-- home.html
|   |   +-- dashboard.html
|   |
|   +-- product/                 # Product module
|   |   +-- product-list.html
|   |   +-- product-detail.html
|   |   +-- product-search.html
|   |
|   +-- cart/                    # Cart module
|   |   +-- cart.html
|   |   +-- checkout.html
|   |   +-- order-confirmation.html
|   |
|   +-- profile/                 # Profile module
|   |   +-- profile.html
|   |   +-- edit-profile.html
|   |   +-- orders.html
|   |   +-- settings.html
|   |
|   +-- components/              # Shared components
|   |   +-- navbar.html
|   |   +-- tabbar.html
|   |   +-- card.html
|   |   +-- button.html
|   |
|   +-- states/                  # State pages
|       +-- empty.html
|       +-- loading.html
|       +-- error.html
|
+-- react/                       # React output
|   +-- src/
|   |   +-- components/
|   |   |   +-- ui/              # Base components
|   |   |   |   +-- Button.tsx
|   |   |   |   +-- Input.tsx
|   |   |   |   +-- Card.tsx
|   |   |   |   +-- index.ts
|   |   |   |
|   |   |   +-- layout/          # Layout components
|   |   |       +-- Header.tsx
|   |   |       +-- TabBar.tsx
|   |   |       +-- Container.tsx
|   |   |
|   |   +-- screens/             # Screen components
|   |   |   +-- auth/
|   |   |   |   +-- LoginScreen.tsx
|   |   |   |   +-- RegisterScreen.tsx
|   |   |   |   +-- ForgotPasswordScreen.tsx
|   |   |   |
|   |   |   +-- home/
|   |   |   |   +-- HomeScreen.tsx
|   |   |   |
|   |   |   +-- product/
|   |   |   |   +-- ProductListScreen.tsx
|   |   |   |   +-- ProductDetailScreen.tsx
|   |   |   |
|   |   |   +-- profile/
|   |   |       +-- ProfileScreen.tsx
|   |   |       +-- SettingsScreen.tsx
|   |   |
|   |   +-- styles/
|   |   |   +-- theme.ts            # Theme settings
|   |   |
|   |   +-- types/
|   |   |   +-- index.ts            # Type definitions
|   |   |
|   |   +-- routes/
|   |       +-- index.tsx           # Route configuration
|   |
|   +-- package.json
|
+-- swiftui/                     # SwiftUI output
|   +-- Sources/
|   |   +-- Views/
|   |   |   +-- Auth/
|   |   |   +-- Home/
|   |   |   +-- Product/
|   |   |   +-- Profile/
|   |   |
|   |   +-- Components/
|   |   |   +-- AppButton.swift
|   |   |   +-- AppTextField.swift
|   |   |   +-- AppCard.swift
|   |   |
|   |   +-- Theme/
|   |       +-- AppTheme.swift
|   |
|   +-- Package.swift
|
+-- compose/                     # Jetpack Compose output
|   +-- app/src/main/java/
|       +-- com/example/app/
|           +-- ui/
|           |   +-- screens/
|           |   +-- components/
|           |   +-- theme/
|           +-- navigation/
|
+-- assets/                      # Shared resources
|   +-- icons/
|   +-- images/
|   +-- fonts/
|
+-- figma/                       # Figma export
    +-- screens.json                # Figma structure JSON
```

### Project-Named Output

```
generated-ui-{ProjectName}/
|
+-- README.md
+-- SCREENS.md
+-- CHANGELOG.md
|
+-- v1.0/                        # Versioned output
|   +-- html/
|   +-- react/
|   +-- ...
|
+-- latest/                      # Latest version
    +-- (symlink to v1.0)
```

---

## Generation Report Templates

### README.md Template

```markdown
# {ProjectName} UI Generation Report

## Generation Info

| Item | Content |
|------|---------|
| Project Name | {ProjectName} |
| Specification Document | SRS-{ProjectName}-1.0.md |
| Generation Time | {DateTime} |
| Generation Version | v1.0 |

## Generation Summary

| Statistic | Count |
|-----------|-------|
| Total Screens | {TotalScreens} |
| Modules | {TotalModules} |
| Components | {TotalComponents} |

### Output Formats

- [x] HTML + Tailwind ({ScreenCount} pages)
- [x] React ({ScreenCount} components)
- [ ] SwiftUI
- [ ] Jetpack Compose

## Screen List

### Auth Module

| Screen | File | Status |
|--------|------|--------|
| Login | auth/login.html | Done |
| Register | auth/register.html | Done |
| Forgot Password | auth/forgot-password.html | Done |

### Home Module

| Screen | File | Status |
|--------|------|--------|
| Home | home/home.html | Done |

### Product Module

| Screen | File | Status |
|--------|------|--------|
| Product List | product/list.html | Done |
| Product Detail | product/detail.html | Done |
| Search Results | product/search.html | Done |

... (more modules)

## Style Settings

```
Primary Color: #6366F1
Secondary Color: #EC4899
Background: #FFFFFF
Border Radius: 12px
Font: Inter / SF Pro
```

## How to Use

### HTML Preview
```bash
cd generated-ui/html
open login.html
```

### React Development
```bash
cd generated-ui/react
npm install
npm run dev
```

## Next Steps

1. **Feature Completion**
   - [ ] Connect backend API
   - [ ] Implement form validation logic
   - [ ] Add state management

2. **Design Adjustments**
   - [ ] Adjust colors to brand
   - [ ] Replace placeholder images
   - [ ] Fine-tune spacing and typography

3. **Testing**
   - [ ] Responsive testing
   - [ ] Accessibility testing
   - [ ] Browser compatibility testing

## File Directory

```
generated-ui/
+-- html/           # {HTMLCount} files
+-- react/          # {ReactCount} files
+-- assets/         # Shared resources
+-- README.md       # This document
```

---

*Auto-generated by App UI/UX Designer Skill*
*Generation Time: {DateTime}*
```

### SCREENS.md Template

```markdown
# {ProjectName} Screen Specifications

## Screen Overview

```
Total Screens: {Total}
+-- Auth Module: {AuthCount} pages
+-- Home Module: {HomeCount} pages
+-- Product Module: {ProductCount} pages
+-- Cart Module: {CartCount} pages
+-- Profile Module: {ProfileCount} pages
```

---

## SCR-001 Login Page

**Basic Info**
| Item | Content |
|------|---------|
| Screen ID | SCR-001 |
| Screen Name | Login Page |
| Module | Auth |
| Access Permission | Public |

**Screen Elements**
| Element | Type | Required |
|---------|------|----------|
| Logo | Image | Yes |
| Title | Text | Yes |
| Email Input | TextField | Yes |
| Password Input | SecureField | Yes |
| Login Button | Button | Yes |
| Forgot Password | Link | Yes |
| Social Login | ButtonGroup | No |
| Register Link | Link | Yes |

**Screen States**
- Default
- Loading
- Error

**Navigation**
- Source: Splash screen
- Destination: Home, Register page, Forgot password

**Requirements Covered**
- FR-002: User Login
- FR-003: Social Login

---

## SCR-002 Register Page

... (more screen specifications)
```

---

## Quick Start Commands

### Generate UI from SRS

```
Please read /path/to/SRS-ProjectName-1.0.md
and generate complete UI screens

Output Settings:
- Directory: ./generated-ui/
- Format: HTML + React
- Style: Modern minimalist, primary color #6366F1
```

### Generate UI from SDD

```
Please read /path/to/SDD-ProjectName-1.0.docx
and generate UI based on screen specifications

Output Settings:
- Directory: ./generated-ui/
- Format: SwiftUI
- Strictly follow SDD-defined screen structure
```

### Generate from Multiple Documents

```
Please read the following documents:
1. /path/to/SRS-ProjectName-1.0.md (Functional requirements)
2. /path/to/SDD-ProjectName-1.0.md (Screen specifications)

Integrate both documents to generate complete UI

Output Settings:
- Directory: ./generated-ui-ProjectName/
- Format: All platforms (HTML/React/SwiftUI/Compose)
```

---

## Generation Checklist

```
Document Parsing
[ ] Document format identified correctly
[ ] Section structure parsed completely
[ ] Functional requirements extracted completely
[ ] User roles identified
[ ] Screen specifications extracted

UI Planning
[ ] Screen list complete
[ ] Flow logic correct
[ ] State coverage complete
[ ] Navigation structure reasonable

Generation Quality
[ ] Code is executable
[ ] Style is consistent
[ ] Naming follows conventions
[ ] Directory structure is clear

Output Completeness
[ ] All screens generated
[ ] Shared components created
[ ] Route configuration generated
[ ] Generation report output
```
