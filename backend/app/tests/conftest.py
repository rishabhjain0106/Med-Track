import os
import sys
import pytest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

TEST_DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_suite.db"))
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"

from app.database import Base
from app.models.hospital import Hospital
from app.models.user import User
from app.models.blood import BloodInventory
from app.models.medicine import MedicineInventory
from app.models.beds import BedInventory
from app.security.auth import hash_password
from app.cache.redis_client import cache_client

# Test Engine with timeout to allow busy handler for multi-threaded SQLite
TEST_ENGINE = create_engine(
    f"sqlite:///{TEST_DB_FILE}",
    connect_args={"check_same_thread": False, "timeout": 30},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    try:
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)
    except Exception:
        pass


@pytest.fixture(autouse=True)
def clean_db():
    yield
    # Clean up all records after each test for clean isolation
    with TEST_ENGINE.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    cache_client.delete_pattern("*")


@pytest.fixture
def db():
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_hospital(db):
    hospital = Hospital(
        name="Dehradun Central Hospital",
        lat=30.3165,
        lng=78.0322,
        address="Clock Tower, Dehradun",
        phone="+91-135-2712345"
    )
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    return hospital


@pytest.fixture
def sample_user(db):
    user = User(
        name="Test Citizen",
        email="citizen@careos.org",
        password_hash=hash_password("password123"),
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_staff(db, sample_hospital):
    staff = User(
        name="Dr. Test Staff",
        email="staff@careos.org",
        password_hash=hash_password("password123"),
        role="hospital_staff",
        hospital_id=sample_hospital.id
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff
