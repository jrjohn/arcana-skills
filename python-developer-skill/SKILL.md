---
name: python-developer-skill
description: Python/Flask development guide based on Arcana Cloud Python enterprise architecture. Provides comprehensive support for Clean Architecture, gRPC-first communication (2.78x faster), dual-protocol support, and multiple deployment modes. Suitable for Python microservices development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# Python Developer Skill

Professional Python/Flask development skill based on [Arcana Cloud Python](https://github.com/jrjohn/arcana-cloud-python) enterprise architecture.

## Core Architecture Principles

### Clean Architecture - Three Layers

```
┌─────────────────────────────────────────────────────┐
│                  Controller Layer                    │
│         HTTP Endpoints + JWT Auth + Validation      │
├─────────────────────────────────────────────────────┤
│                   Service Layer                      │
│          Business Logic + Orchestration             │
├─────────────────────────────────────────────────────┤
│                  Repository Layer                    │
│         Database Operations + Caching               │
└─────────────────────────────────────────────────────┘
```

### Deployment Modes
1. **Monolithic**: Single process/container (development)
2. **Layered**: Separate containers per layer with gRPC
3. **Microservices**: Fine-grained services with independent scaling

### Performance
- gRPC delivers **2.78x average speedup** over HTTP REST
- Point query performance: **6.30x faster** with gRPC

## Instructions

When handling Python/Flask development tasks, follow these principles:

### 1. Project Structure
```
arcana-cloud-python/
├── app/
│   ├── __init__.py
│   ├── controller/        # HTTP endpoints
│   │   ├── __init__.py
│   │   ├── user_controller.py
│   │   └── auth_controller.py
│   ├── service/           # Business logic
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── auth_service.py
│   ├── repository/        # Data access
│   │   ├── __init__.py
│   │   └── user_repository.py
│   ├── model/             # Domain models
│   │   ├── __init__.py
│   │   └── user.py
│   ├── dto/               # Data transfer objects
│   │   ├── __init__.py
│   │   └── user_dto.py
│   ├── grpc/              # gRPC services
│   │   ├── __init__.py
│   │   ├── server.py
│   │   └── user_service_pb2_grpc.py
│   └── config/            # Configuration
│       ├── __init__.py
│       └── settings.py
├── tests/                 # Test suite
├── deployment/            # Docker/K8s configs
├── k8s/                   # Kubernetes manifests
└── requirements.txt
```

### 2. Domain Model with SQLAlchemy

```python
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SyncStatus(str, Enum):
    SYNCED = "synced"
    PENDING = "pending"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: str = Column(String(36), primary_key=True)
    name: str = Column(String(255), nullable=False)
    email: str = Column(String(255), nullable=False, unique=True)
    password_hash: str = Column(String(255), nullable=False)
    sync_status: SyncStatus = Column(
        SQLEnum(SyncStatus), default=SyncStatus.SYNCED
    )
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
```

### 3. Repository Layer

```python
from typing import Optional, List
from sqlalchemy.orm import Session
from app.model.user import User, SyncStatus


class UserRepository:
    def __init__(self, session: Session):
        self._session = session

    def find_by_id(self, user_id: str) -> Optional[User]:
        return self._session.query(User).filter(User.id == user_id).first()

    def find_by_email(self, email: str) -> Optional[User]:
        return self._session.query(User).filter(User.email == email).first()

    def find_all(
        self, page: int = 0, size: int = 10
    ) -> tuple[List[User], int]:
        query = self._session.query(User)
        total = query.count()
        users = query.offset(page * size).limit(size).all()
        return users, total

    def find_pending_sync(self) -> List[User]:
        return (
            self._session.query(User)
            .filter(User.sync_status == SyncStatus.PENDING)
            .all()
        )

    def save(self, user: User) -> User:
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user

    def update(self, user: User) -> User:
        self._session.commit()
        self._session.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self._session.delete(user)
        self._session.commit()
```

### 4. Service Layer

```python
from typing import Optional, List
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash
from app.model.user import User, SyncStatus
from app.repository.user_repository import UserRepository
from app.dto.user_dto import CreateUserDTO, UpdateUserDTO


class UserService:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    def get_user(self, user_id: str) -> Optional[User]:
        return self._repository.find_by_id(user_id)

    def get_users(
        self, page: int = 0, size: int = 10
    ) -> tuple[List[User], int]:
        return self._repository.find_all(page, size)

    def create_user(self, dto: CreateUserDTO) -> User:
        # Check if email already exists
        existing = self._repository.find_by_email(dto.email)
        if existing:
            raise ValueError("Email already registered")

        user = User(
            id=str(uuid4()),
            name=dto.name,
            email=dto.email,
            password_hash=generate_password_hash(dto.password),
            sync_status=SyncStatus.SYNCED,
        )
        return self._repository.save(user)

    def update_user(self, user_id: str, dto: UpdateUserDTO) -> Optional[User]:
        user = self._repository.find_by_id(user_id)
        if not user:
            return None

        if dto.name:
            user.name = dto.name
        if dto.email:
            # Check if new email is taken by another user
            existing = self._repository.find_by_email(dto.email)
            if existing and existing.id != user_id:
                raise ValueError("Email already registered")
            user.email = dto.email

        return self._repository.update(user)

    def delete_user(self, user_id: str) -> bool:
        user = self._repository.find_by_id(user_id)
        if not user:
            return False
        self._repository.delete(user)
        return True

    def authenticate(self, email: str, password: str) -> Optional[User]:
        user = self._repository.find_by_email(email)
        if user and check_password_hash(user.password_hash, password):
            return user
        return None
```

### 5. Controller Layer (Flask)

```python
from flask import Blueprint, request, jsonify, g
from marshmallow import Schema, fields, validate, ValidationError
from app.service.user_service import UserService
from app.dto.user_dto import CreateUserDTO, UpdateUserDTO
from app.middleware.auth import jwt_required

user_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


class CreateUserSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))


class UpdateUserSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=255))
    email = fields.Email()


@user_bp.route("/<user_id>", methods=["GET"])
@jwt_required
def get_user(user_id: str):
    service: UserService = g.user_service

    user = service.get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict())


@user_bp.route("", methods=["GET"])
@jwt_required
def list_users():
    service: UserService = g.user_service

    page = request.args.get("page", 0, type=int)
    size = request.args.get("size", 10, type=int)

    users, total = service.get_users(page, size)

    return jsonify({
        "data": [u.to_dict() for u in users],
        "page": page,
        "size": size,
        "total": total,
    })


@user_bp.route("", methods=["POST"])
@jwt_required
def create_user():
    service: UserService = g.user_service
    schema = CreateUserSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    try:
        user = service.create_user(CreateUserDTO(**data))
        return jsonify(user.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@user_bp.route("/<user_id>", methods=["PUT"])
@jwt_required
def update_user(user_id: str):
    service: UserService = g.user_service
    schema = UpdateUserSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    try:
        user = service.update_user(user_id, UpdateUserDTO(**data))
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@user_bp.route("/<user_id>", methods=["DELETE"])
@jwt_required
def delete_user(user_id: str):
    service: UserService = g.user_service

    if service.delete_user(user_id):
        return "", 204
    return jsonify({"error": "User not found"}), 404
```

### 6. gRPC Service

```python
import grpc
from concurrent import futures
from app.grpc import user_pb2, user_pb2_grpc
from app.service.user_service import UserService


class UserServicer(user_pb2_grpc.UserServiceServicer):
    def __init__(self, user_service: UserService):
        self._service = user_service

    def GetUser(self, request, context):
        user = self._service.get_user(request.id)
        if not user:
            context.abort(grpc.StatusCode.NOT_FOUND, "User not found")

        return user_pb2.UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            created_at=int(user.created_at.timestamp() * 1000),
        )

    def ListUsers(self, request, context):
        users, total = self._service.get_users(request.page, request.size)

        return user_pb2.ListUsersResponse(
            users=[
                user_pb2.UserResponse(
                    id=u.id,
                    name=u.name,
                    email=u.email,
                    created_at=int(u.created_at.timestamp() * 1000),
                )
                for u in users
            ],
            total=total,
        )

    def CreateUser(self, request, context):
        try:
            from app.dto.user_dto import CreateUserDTO

            dto = CreateUserDTO(
                name=request.name,
                email=request.email,
                password=request.password,
            )
            user = self._service.create_user(dto)

            return user_pb2.UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                created_at=int(user.created_at.timestamp() * 1000),
            )
        except ValueError as e:
            context.abort(grpc.StatusCode.ALREADY_EXISTS, str(e))


def serve(user_service: UserService, port: int = 50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(
        UserServicer(user_service), server
    )
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    server.wait_for_termination()
```

### 7. JWT Authentication Middleware

```python
from functools import wraps
from typing import Optional
from flask import request, g, jsonify
import jwt
from datetime import datetime, timedelta
from app.config.settings import Settings


class JWTAuth:
    def __init__(self, settings: Settings):
        self._secret = settings.jwt_secret
        self._algorithm = "HS256"
        self._expiration = timedelta(hours=24)

    def create_token(self, user_id: str, roles: list[str]) -> str:
        payload = {
            "sub": user_id,
            "roles": roles,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + self._expiration,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(
                token, self._secret, algorithms=[self._algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(" ")[1]
        jwt_auth: JWTAuth = g.jwt_auth

        payload = jwt_auth.verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        g.current_user_id = payload["sub"]
        g.current_user_roles = payload["roles"]

        return f(*args, **kwargs)

    return decorated


def role_required(*required_roles):
    def decorator(f):
        @wraps(f)
        @jwt_required
        def decorated(*args, **kwargs):
            user_roles = g.current_user_roles

            if not any(role in user_roles for role in required_roles):
                return jsonify({"error": "Insufficient permissions"}), 403

            return f(*args, **kwargs)

        return decorated

    return decorator
```

### 8. Database Migration with Alembic

```python
# migrations/versions/001_initial.py
from alembic import op
import sqlalchemy as sa


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "sync_status",
            sa.Enum("synced", "pending", "failed", name="syncstatus"),
            default="synced",
        ),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"])


def downgrade():
    op.drop_index("ix_users_email")
    op.drop_table("users")
```

### 9. Testing with pytest

```python
import pytest
from unittest.mock import Mock, MagicMock
from app.service.user_service import UserService
from app.model.user import User, SyncStatus
from app.dto.user_dto import CreateUserDTO


@pytest.fixture
def mock_repository():
    return Mock()


@pytest.fixture
def user_service(mock_repository):
    return UserService(mock_repository)


class TestUserService:
    def test_get_user_found(self, user_service, mock_repository):
        # Arrange
        expected_user = User(
            id="123",
            name="John Doe",
            email="john@example.com",
            password_hash="hash",
            sync_status=SyncStatus.SYNCED,
        )
        mock_repository.find_by_id.return_value = expected_user

        # Act
        result = user_service.get_user("123")

        # Assert
        assert result == expected_user
        mock_repository.find_by_id.assert_called_once_with("123")

    def test_get_user_not_found(self, user_service, mock_repository):
        # Arrange
        mock_repository.find_by_id.return_value = None

        # Act
        result = user_service.get_user("nonexistent")

        # Assert
        assert result is None

    def test_create_user_success(self, user_service, mock_repository):
        # Arrange
        mock_repository.find_by_email.return_value = None
        mock_repository.save.side_effect = lambda u: u

        dto = CreateUserDTO(
            name="John Doe",
            email="john@example.com",
            password="password123",
        )

        # Act
        result = user_service.create_user(dto)

        # Assert
        assert result.name == "John Doe"
        assert result.email == "john@example.com"
        mock_repository.save.assert_called_once()

    def test_create_user_email_exists(self, user_service, mock_repository):
        # Arrange
        existing_user = User(
            id="456",
            name="Existing User",
            email="john@example.com",
            password_hash="hash",
        )
        mock_repository.find_by_email.return_value = existing_user

        dto = CreateUserDTO(
            name="John Doe",
            email="john@example.com",
            password="password123",
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Email already registered"):
            user_service.create_user(dto)
```

## Code Review Checklist

### Required Items
- [ ] Follow Clean Architecture layering
- [ ] gRPC service implemented for internal communication
- [ ] Repository pattern properly implemented
- [ ] JWT authentication complete
- [ ] Input validation with Marshmallow

### Performance Checks
- [ ] Use gRPC for internal communication (2.78x faster)
- [ ] Database queries optimized with indexes
- [ ] Connection pooling configured
- [ ] Caching strategy implemented

### Security Checks
- [ ] JWT token validation
- [ ] Role-based access control
- [ ] Input validation complete
- [ ] Password hashing with Werkzeug
- [ ] No hardcoded secrets

### Code Quality
- [ ] Type hints on all functions
- [ ] mypy strict mode passes
- [ ] flake8/black/isort compliant
- [ ] 100% test coverage target

## Common Issues

### gRPC Connection Issues
1. Check protobuf compilation
2. Verify service registration
3. Ensure proper error handling

### Database Issues
1. Run Alembic migrations
2. Check connection pool settings
3. Review query performance

### Testing Issues
1. Use pytest fixtures properly
2. Mock external dependencies
3. Test edge cases

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| Python | 3.14+ |
| Flask | 3.1+ |
| SQLAlchemy | 2.0+ |
| Marshmallow | 4.1+ |
| gRPC | 1.68+ |
| pytest | 8.3+ |
| MySQL | 8.0+ |
| Redis | 7.0+ |
