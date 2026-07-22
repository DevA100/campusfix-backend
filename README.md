# CampusFix Backend API

RESTful API for the CampusFix - University Maintenance Request Management System.

## 📋 Overview

CampusFix is a comprehensive maintenance request management system designed for universities. This backend API handles user authentication, service request management, assignment tracking, and reporting.

## 🚀 Features

- **User Authentication**: JWT-based authentication with role-based access control
- **User Roles**: Student, Staff, Maintenance Officer, Admin
- **Service Requests**: Create, view, update, and track maintenance requests
- **Assignment System**: Admin can assign requests to maintenance officers
- **Status Tracking**: Track request lifecycle (PENDING → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED)
- **File Uploads**: Upload evidence files for requests
- **Reporting**: Export reports as CSV
- **Audit Logging**: Track all status changes

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (Neon)
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **Deployment**: Render

## 📦 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL
- pip

### Setup

1. Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/campusfix-backend.git
cd campusfix-backend
```
