"""
One-time seed script: creates the four roles, a default set of
request categories, and a first administrator account.

Run with: python seed.py
"""

from app.database import SessionLocal, engine, Base
from app.models.role import Role
from app.models.request_category import RequestCategory
from app.models.user import User
from app.core.security import hash_password

# UPDATED: Split STUDENT_STAFF into separate STUDENT and STAFF
# to match your permissions system (require_any_authenticated expects STUDENT and STAFF)
DEFAULT_ROLES = [
    "STUDENT",              # matches require_any_authenticated
    "STAFF",                # matches require_any_authenticated
    "MAINTENANCE_OFFICER",  # matches require_officer
    "ADMIN"                 # matches require_admin
]

# Role descriptions for documentation
ROLE_DESCRIPTIONS = {
    "STUDENT": "Student user - can submit and track service requests",
    "STAFF": "Staff member - can submit and manage requests",
    "MAINTENANCE_OFFICER": "Maintenance officer - can be assigned to and resolve requests",
    "ADMIN": "Administrator - full system access"
}

DEFAULT_CATEGORIES = [
    "Electrical",
    "Plumbing",
    "Furniture",
    "Internet/Network",
    "Classroom Equipment",
    "Hostel Maintenance",
]


def run():
    """Seed the database with initial data."""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # ===== SEED ROLES =====
        print("\n📋 Seeding roles...")
        for role_name in DEFAULT_ROLES:
            existing = db.query(Role).filter(Role.name == role_name).first()
            if not existing:
                role = Role(
                    name=role_name,
                    description=ROLE_DESCRIPTIONS.get(
                        role_name, f"{role_name} role")
                )
                db.add(role)
                print(f"  ✅ Created role: {role_name}")
            else:
                print(f"  ⏭️ Role already exists: {role_name}")
        db.commit()
        print("✅ Roles seeded successfully!")

        # ===== SEED CATEGORIES =====
        print("\n📋 Seeding categories...")
        for category_name in DEFAULT_CATEGORIES:
            existing = db.query(RequestCategory).filter(
                RequestCategory.name == category_name
            ).first()
            if not existing:
                db.add(RequestCategory(name=category_name))
                print(f"  ✅ Created category: {category_name}")
            else:
                print(f"  ⏭️ Category already exists: {category_name}")
        db.commit()
        print("✅ Categories seeded successfully!")

        # ===== SEED ADMIN USER =====
        print("\n👤 Creating admin user...")
        admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
        if not admin_role:
            print("  ❌ ADMIN role not found! Run seeding again.")
            return

        admin_email = "admin@campusfix.edu"
        existing_admin = db.query(User).filter(
            User.email == admin_email).first()

        if not existing_admin:
            admin_user = User(
                full_name="System Administrator",
                email=admin_email,
                hashed_password=hash_password("ChangeMe123!"),
                role_id=admin_role.id,
                is_active=True,
                phone_number="+1234567890",
                department="Administration"
            )
            db.add(admin_user)
            db.commit()
            print(f"  ✅ Created default administrator:")
            print(f"     Email: {admin_email}")
            print(f"     Password: ChangeMe123!")
        else:
            print(f"  ⏭️ Admin user already exists: {admin_email}")

        # ===== SEED DEMO STUDENT =====
        print("\n👤 Creating demo student...")
        student_role = db.query(Role).filter(Role.name == "STUDENT").first()
        if student_role:
            student_email = "student@campusfix.edu"
            if not db.query(User).filter(User.email == student_email).first():
                db.add(User(
                    full_name="Demo Student",
                    email=student_email,
                    hashed_password=hash_password("Demo123!"),
                    role_id=student_role.id,
                    is_active=True,
                    department="Computer Science"
                ))
                print(f"  ✅ Created demo student: {student_email} / Demo123!")

        # ===== SEED DEMO STAFF =====
        print("\n👤 Creating demo staff...")
        staff_role = db.query(Role).filter(Role.name == "STAFF").first()
        if staff_role:
            staff_email = "staff@campusfix.edu"
            if not db.query(User).filter(User.email == staff_email).first():
                db.add(User(
                    full_name="Demo Staff",
                    email=staff_email,
                    hashed_password=hash_password("Demo123!"),
                    role_id=staff_role.id,
                    is_active=True,
                    department="Administration"
                ))
                print(f"  ✅ Created demo staff: {staff_email} / Demo123!")

        # ===== SEED DEMO MAINTENANCE OFFICER =====
        print("\n👤 Creating demo officer...")
        officer_role = db.query(Role).filter(
            Role.name == "MAINTENANCE_OFFICER").first()
        if officer_role:
            officer_email = "officer@campusfix.edu"
            if not db.query(User).filter(User.email == officer_email).first():
                db.add(User(
                    full_name="Demo Officer",
                    email=officer_email,
                    hashed_password=hash_password("Demo123!"),
                    role_id=officer_role.id,
                    is_active=True,
                    department="Maintenance"
                ))
                print(f"  ✅ Created demo officer: {officer_email} / Demo123!")

        db.commit()

        print("\n" + "=" * 50)
        print("✅ SEED COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("\n📌 Credentials:")
        print(f"   Admin:    admin@campusfix.edu / ChangeMe123!")
        print(f"   Student:  student@campusfix.edu / Demo123!")
        print(f"   Staff:    staff@campusfix.edu / Demo123!")
        print(f"   Officer:  officer@campusfix.edu / Demo123!")
        print("\n⚠️  Please change these passwords after first login!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during seeding: {e}")
        raise
    finally:
        db.close()


def verify_seed():
    """Verify that seeding was successful."""
    db = SessionLocal()
    try:
        print("\n📊 Database Status:")
        print("-" * 40)

        # Count roles
        roles_count = db.query(Role).count()
        print(f"Roles: {roles_count}")
        for role in db.query(Role).all():
            print(f"  - {role.name}: {role.description or 'No description'}")

        # Count categories
        categories_count = db.query(RequestCategory).count()
        print(f"\nCategories: {categories_count}")
        for category in db.query(RequestCategory).all():
            print(f"  - {category.name}")

        # Count users
        users_count = db.query(User).count()
        print(f"\nUsers: {users_count}")
        for user in db.query(User).all():
            print(
                f"  - {user.email} ({user.role.name if user.role else 'No role'})")

    finally:
        db.close()


if __name__ == "__main__":
    import sys

    # Check for verify flag
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_seed()
    else:
        run()
        print("\n" + "-" * 50)
        print("To verify the seed, run: python seed.py --verify")
