import sys
import os
from datetime import datetime, timedelta, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal, engine, Base
from app.models.hospital import Hospital
from app.models.user import User
from app.models.blood import BloodInventory
from app.models.medicine import MedicineInventory
from app.models.beds import BedInventory
from app.models.reservation import Reservation
from app.models.audit import AuditLog
from app.security.auth import hash_password


def seed_database():
    print("Creating tables if they do not exist...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Hospital).count() > 0:
            print("Database already contains hospitals. Skipping seed.")
            return

        print("Seeding 5 hospitals around Dehradun...")
        hospitals_data = [
            {
                "id": 1,
                "name": "Max Super Speciality Hospital, Dehradun",
                "lat": 30.3402,
                "lng": 78.0782,
                "address": "Mussoorie Diversion Road, Malsi, Dehradun, Uttarakhand 248001",
                "phone": "+91-135-7193000",
            },
            {
                "id": 2,
                "name": "Himalayan Hospital, Jolly Grant",
                "lat": 30.1983,
                "lng": 78.1691,
                "address": "Swami Ram Nagar, Jolly Grant, Doiwala, Dehradun, Uttarakhand 248016",
                "phone": "+91-135-2471133",
            },
            {
                "id": 3,
                "name": "Government Doon Medical College Hospital",
                "lat": 30.3256,
                "lng": 78.0437,
                "address": "Parade Ground, Dehradun, Uttarakhand 248001",
                "phone": "+91-135-2659012",
            },
            {
                "id": 4,
                "name": "Shri Mahant Indiresh Hospital",
                "lat": 30.3129,
                "lng": 78.0264,
                "address": "Patel Nagar, Dehradun, Uttarakhand 248001",
                "phone": "+91-135-6672400",
            },
            {
                "id": 5,
                "name": "Synergy Institute of Medical Sciences",
                "lat": 30.3398,
                "lng": 77.9945,
                "address": "Canal Road, Ballupur, Dehradun, Uttarakhand 248001",
                "phone": "+91-135-2226000",
            },
        ]

        hospitals = []
        for h in hospitals_data:
            hospital = Hospital(**h)
            db.add(hospital)
            hospitals.append(hospital)
        db.flush()

        print("Seeding staff and public users...")
        users_data = [
            # Staff accounts for each hospital
            {
                "name": "Dr. Rohit Sharma (Max Staff)",
                "email": "staff_max@careos.org",
                "password_hash": hash_password("staff123"),
                "role": "hospital_staff",
                "hospital_id": 1,
            },
            {
                "name": "Dr. Ananya Verma (Himalayan Staff)",
                "email": "staff_hiht@careos.org",
                "password_hash": hash_password("staff123"),
                "role": "hospital_staff",
                "hospital_id": 2,
            },
            {
                "name": "Dr. Rajesh Rawat (Doon Govt Staff)",
                "email": "staff_doon@careos.org",
                "password_hash": hash_password("staff123"),
                "role": "hospital_staff",
                "hospital_id": 3,
            },
            {
                "name": "Dr. Sunita Negi (Indiresh Staff)",
                "email": "staff_indiresh@careos.org",
                "password_hash": hash_password("staff123"),
                "role": "hospital_staff",
                "hospital_id": 4,
            },
            {
                "name": "Dr. Amit Joshi (Synergy Staff)",
                "email": "staff_synergy@careos.org",
                "password_hash": hash_password("staff123"),
                "role": "hospital_staff",
                "hospital_id": 5,
            },
            # Public and Admin users
            {
                "name": "Siddharth Mehra (Citizen)",
                "email": "user@careos.org",
                "password_hash": hash_password("user123"),
                "role": "user",
                "hospital_id": None,
            },
            {
                "name": "Pooja Bisht (Citizen)",
                "email": "pooja@careos.org",
                "password_hash": hash_password("user123"),
                "role": "user",
                "hospital_id": None,
            },
            {
                "name": "CareOS System Admin",
                "email": "admin@careos.org",
                "password_hash": hash_password("admin123"),
                "role": "admin",
                "hospital_id": None,
            },
        ]

        for u in users_data:
            user = User(**u)
            db.add(user)
        db.flush()

        print("Seeding blood, medicine, and bed inventory...")
        blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        now = datetime.now(timezone.utc)
        future_30d = now + timedelta(days=30)
        future_180d = now + timedelta(days=180)

        # Blood inventory seed
        blood_stock_distribution = {
            1: {"A+": 18, "A-": 6, "B+": 22, "B-": 4, "AB+": 9, "AB-": 3, "O+": 25, "O-": 7},
            2: {"A+": 30, "A-": 8, "B+": 28, "B-": 5, "AB+": 12, "AB-": 4, "O+": 40, "O-": 10},
            3: {"A+": 14, "A-": 3, "B+": 16, "B-": 2, "AB+": 7, "AB-": 2, "O+": 18, "O-": 4},
            4: {"A+": 20, "A-": 5, "B+": 19, "B-": 4, "AB+": 8, "AB-": 3, "O+": 22, "O-": 6},
            5: {"A+": 12, "A-": 4, "B+": 15, "B-": 3, "AB+": 6, "AB-": 2, "O+": 16, "O-": 5},
        }

        for h_id, stocks in blood_stock_distribution.items():
            for bg, units in stocks.items():
                db.add(
                    BloodInventory(
                        hospital_id=h_id,
                        blood_group=bg,
                        units_available=units,
                        expiry_date=future_30d,
                        updated_at=now,
                    )
                )

        # Medicine inventory seed
        common_medicines = [
            ("Paracetamol 650mg IV", 150),
            ("Remdesivir 100mg", 45),
            ("Insulin Glargine 100IU", 80),
            ("Ceftriaxone 1g Injection", 120),
            ("Pantoprazole 40mg IV", 200),
            ("Enoxaparin 40mg PFS", 60),
            ("Atropine 0.6mg/ml", 95),
            ("Adrenaline 1mg Ampoules", 110),
        ]

        for h in hospitals:
            for med_name, qty in common_medicines:
                # Add slight variation per hospital
                variation = (h.id * 7) % 30
                db.add(
                    MedicineInventory(
                        hospital_id=h.id,
                        name=med_name,
                        quantity_available=qty + variation,
                        expiry_date=future_180d,
                        updated_at=now,
                    )
                )

        # Bed inventory seed
        bed_configs = {
            1: [("general", 150, 42), ("icu", 40, 8), ("emergency", 20, 5)],
            2: [("general", 300, 85), ("icu", 60, 14), ("emergency", 35, 9)],
            3: [("general", 220, 30), ("icu", 35, 4), ("emergency", 25, 3)],
            4: [("general", 180, 50), ("icu", 45, 11), ("emergency", 20, 6)],
            5: [("general", 120, 28), ("icu", 25, 5), ("emergency", 15, 4)],
        }

        for h_id, configs in bed_configs.items():
            for b_type, total, avail in configs:
                db.add(
                    BedInventory(
                        hospital_id=h_id,
                        bed_type=b_type,
                        total_beds=total,
                        available_beds=avail,
                        updated_at=now,
                    )
                )

        db.commit()
        print("Successfully seeded MedTrack (CareOS) database!")
        print("Hospital staff logins: staff_max@careos.org, staff_hiht@careos.org, etc. (Password: staff123)")
        print("Public user login: user@careos.org (Password: user123)")
        print("Admin login: admin@careos.org (Password: admin123)")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
