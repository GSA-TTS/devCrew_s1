"""
Issue #41: Customer Data Module
Implements CRUD operations for customer data with SQLAlchemy.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import Session, sessionmaker

Base = declarative_base()


# SQLAlchemy Models
class Customer(Base):
    """Customer database model."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    phone = Column(String(50))
    company = Column(String(255))
    address = Column(Text)
    metadata = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)


# Pydantic Models
class CustomerBase(BaseModel):
    """Base customer schema."""

    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CustomerCreate(CustomerBase):
    """Customer creation schema."""

    customer_id: Optional[str] = None


class CustomerUpdate(BaseModel):
    """Customer update schema."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    """Customer response schema."""

    id: int
    customer_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class CustomerListResponse(BaseModel):
    """Customer list response schema."""

    total: int
    customers: List[CustomerResponse]
    page: int
    page_size: int


# Database connection
def get_database_url(
    user: str = "postgres",
    password: str = "postgres",
    host: str = "localhost",
    port: int = 5432,
    database: str = "customer_db",
) -> str:
    """
    Get database URL.

    Args:
        user: Database user
        password: Database password
        host: Database host
        port: Database port
        database: Database name

    Returns:
        Database URL
    """
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def get_async_database_url(
    user: str = "postgres",
    password: str = "postgres",
    host: str = "localhost",
    port: int = 5432,
    database: str = "customer_db",
) -> str:
    """
    Get async database URL.

    Args:
        user: Database user
        password: Database password
        host: Database host
        port: Database port
        database: Database name

    Returns:
        Async database URL
    """
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


# Database setup
engine = create_engine(get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async_engine = create_async_engine(get_async_database_url(), echo=False)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


def create_tables():
    """Create database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Get database session.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """
    Get async database session.

    Yields:
        Async database session
    """
    async with AsyncSessionLocal() as session:
        yield session


# CRUD Operations
class CustomerCRUD:
    """CRUD operations for customer data."""

    @staticmethod
    def generate_customer_id(email: str) -> str:
        """
        Generate customer ID from email.

        Args:
            email: Customer email

        Returns:
            Customer ID
        """
        import hashlib

        return f"CUST_{hashlib.md5(email.encode()).hexdigest()[:12].upper()}"

    @staticmethod
    def create_customer(db: Session, customer: CustomerCreate) -> Customer:
        """
        Create a new customer.

        Args:
            db: Database session
            customer: Customer data

        Returns:
            Created customer

        Raises:
            ValueError: If customer already exists
        """
        # Check if customer exists
        existing = (
            db.query(Customer).filter(Customer.email == customer.email).first()
        )
        if existing and not existing.deleted_at:
            raise ValueError(f"Customer with email {customer.email} already exists")

        # Generate customer ID if not provided
        customer_id = customer.customer_id or CustomerCRUD.generate_customer_id(
            customer.email
        )

        db_customer = Customer(
            customer_id=customer_id,
            email=customer.email,
            full_name=customer.full_name,
            phone=customer.phone,
            company=customer.company,
            address=customer.address,
            metadata=customer.metadata,
        )

        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        return db_customer

    @staticmethod
    async def acreate_customer(
        db: AsyncSession, customer: CustomerCreate
    ) -> Customer:
        """
        Create a new customer (async).

        Args:
            db: Async database session
            customer: Customer data

        Returns:
            Created customer

        Raises:
            ValueError: If customer already exists
        """
        # Check if customer exists
        result = await db.execute(
            select(Customer).filter(Customer.email == customer.email)
        )
        existing = result.scalar_one_or_none()

        if existing and not existing.deleted_at:
            raise ValueError(f"Customer with email {customer.email} already exists")

        # Generate customer ID if not provided
        customer_id = customer.customer_id or CustomerCRUD.generate_customer_id(
            customer.email
        )

        db_customer = Customer(
            customer_id=customer_id,
            email=customer.email,
            full_name=customer.full_name,
            phone=customer.phone,
            company=customer.company,
            address=customer.address,
            metadata=customer.metadata,
        )

        db.add(db_customer)
        await db.commit()
        await db.refresh(db_customer)
        return db_customer

    @staticmethod
    def get_customer(db: Session, customer_id: str) -> Optional[Customer]:
        """
        Get customer by ID.

        Args:
            db: Database session
            customer_id: Customer ID

        Returns:
            Customer or None
        """
        return (
            db.query(Customer)
            .filter(
                Customer.customer_id == customer_id, Customer.deleted_at.is_(None)
            )
            .first()
        )

    @staticmethod
    async def aget_customer(
        db: AsyncSession, customer_id: str
    ) -> Optional[Customer]:
        """
        Get customer by ID (async).

        Args:
            db: Async database session
            customer_id: Customer ID

        Returns:
            Customer or None
        """
        result = await db.execute(
            select(Customer).filter(
                Customer.customer_id == customer_id, Customer.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def get_customer_by_email(db: Session, email: str) -> Optional[Customer]:
        """
        Get customer by email.

        Args:
            db: Database session
            email: Customer email

        Returns:
            Customer or None
        """
        return (
            db.query(Customer)
            .filter(Customer.email == email, Customer.deleted_at.is_(None))
            .first()
        )

    @staticmethod
    def list_customers(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> List[Customer]:
        """
        List customers with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records
            is_active: Filter by active status

        Returns:
            List of customers
        """
        query = db.query(Customer).filter(Customer.deleted_at.is_(None))

        if is_active is not None:
            query = query.filter(Customer.is_active == is_active)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    async def alist_customers(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> List[Customer]:
        """
        List customers with pagination (async).

        Args:
            db: Async database session
            skip: Number of records to skip
            limit: Maximum number of records
            is_active: Filter by active status

        Returns:
            List of customers
        """
        query = select(Customer).filter(Customer.deleted_at.is_(None))

        if is_active is not None:
            query = query.filter(Customer.is_active == is_active)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    def update_customer(
        db: Session, customer_id: str, customer_update: CustomerUpdate
    ) -> Optional[Customer]:
        """
        Update customer.

        Args:
            db: Database session
            customer_id: Customer ID
            customer_update: Update data

        Returns:
            Updated customer or None
        """
        db_customer = CustomerCRUD.get_customer(db, customer_id)
        if not db_customer:
            return None

        update_data = customer_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_customer, field, value)

        db_customer.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_customer)
        return db_customer

    @staticmethod
    async def aupdate_customer(
        db: AsyncSession, customer_id: str, customer_update: CustomerUpdate
    ) -> Optional[Customer]:
        """
        Update customer (async).

        Args:
            db: Async database session
            customer_id: Customer ID
            customer_update: Update data

        Returns:
            Updated customer or None
        """
        db_customer = await CustomerCRUD.aget_customer(db, customer_id)
        if not db_customer:
            return None

        update_data = customer_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_customer, field, value)

        db_customer.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_customer)
        return db_customer

    @staticmethod
    def delete_customer(db: Session, customer_id: str, soft: bool = True) -> bool:
        """
        Delete customer (soft or hard delete).

        Args:
            db: Database session
            customer_id: Customer ID
            soft: If True, perform soft delete

        Returns:
            True if deleted, False otherwise
        """
        db_customer = CustomerCRUD.get_customer(db, customer_id)
        if not db_customer:
            return False

        if soft:
            # Soft delete
            db_customer.deleted_at = datetime.utcnow()
            db_customer.is_active = False
            db.commit()
        else:
            # Hard delete
            db.delete(db_customer)
            db.commit()

        return True

    @staticmethod
    async def adelete_customer(
        db: AsyncSession, customer_id: str, soft: bool = True
    ) -> bool:
        """
        Delete customer (async, soft or hard delete).

        Args:
            db: Async database session
            customer_id: Customer ID
            soft: If True, perform soft delete

        Returns:
            True if deleted, False otherwise
        """
        db_customer = await CustomerCRUD.aget_customer(db, customer_id)
        if not db_customer:
            return False

        if soft:
            # Soft delete
            db_customer.deleted_at = datetime.utcnow()
            db_customer.is_active = False
            await db.commit()
        else:
            # Hard delete
            await db.delete(db_customer)
            await db.commit()

        return True

    @staticmethod
    def count_customers(db: Session, is_active: Optional[bool] = None) -> int:
        """
        Count customers.

        Args:
            db: Database session
            is_active: Filter by active status

        Returns:
            Number of customers
        """
        query = db.query(Customer).filter(Customer.deleted_at.is_(None))

        if is_active is not None:
            query = query.filter(Customer.is_active == is_active)

        return query.count()

    @staticmethod
    async def acount_customers(
        db: AsyncSession, is_active: Optional[bool] = None
    ) -> int:
        """
        Count customers (async).

        Args:
            db: Async database session
            is_active: Filter by active status

        Returns:
            Number of customers
        """
        from sqlalchemy import func

        query = select(func.count(Customer.id)).filter(Customer.deleted_at.is_(None))

        if is_active is not None:
            query = query.filter(Customer.is_active == is_active)

        result = await db.execute(query)
        return result.scalar()


# Validation utilities
class CustomerValidator:
    """Validate customer data."""

    @staticmethod
    def validate_create(customer: CustomerCreate) -> List[str]:
        """
        Validate customer creation data.

        Args:
            customer: Customer data

        Returns:
            List of validation errors
        """
        errors = []

        if not customer.email:
            errors.append("Email is required")

        if customer.phone and len(customer.phone) > 50:
            errors.append("Phone number is too long")

        if customer.full_name and len(customer.full_name) > 255:
            errors.append("Full name is too long")

        return errors

    @staticmethod
    def validate_update(customer: CustomerUpdate) -> List[str]:
        """
        Validate customer update data.

        Args:
            customer: Customer update data

        Returns:
            List of validation errors
        """
        errors = []

        if customer.phone and len(customer.phone) > 50:
            errors.append("Phone number is too long")

        if customer.full_name and len(customer.full_name) > 255:
            errors.append("Full name is too long")

        return errors
