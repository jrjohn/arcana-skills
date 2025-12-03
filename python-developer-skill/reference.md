# Python Developer Skill - Technical Reference

## Table of Contents
1. [Project Structure](#project-structure)
2. [Clean Architecture Layers](#clean-architecture-layers)
3. [SQLAlchemy ORM](#sqlalchemy-orm)
4. [Flask Application](#flask-application)
5. [gRPC Services](#grpc-services)
6. [Authentication & Security](#authentication--security)
7. [Caching with Redis](#caching-with-redis)
8. [Testing](#testing)
9. [Deployment](#deployment)

---

## Project Structure

```
arcana-cloud-python/
├── app/
│   ├── __init__.py              # Application factory
│   ├── controller/              # HTTP endpoints (Flask blueprints)
│   │   ├── __init__.py
│   │   ├── user_controller.py
│   │   ├── auth_controller.py
│   │   └── health_controller.py
│   ├── service/                 # Business logic
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── auth_service.py
│   │   └── notification_service.py
│   ├── repository/              # Data access
│   │   ├── __init__.py
│   │   ├── base_repository.py
│   │   ├── user_repository.py
│   │   └── cache_repository.py
│   ├── model/                   # Domain models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── order.py
│   │   └── base.py
│   ├── dto/                     # Data transfer objects
│   │   ├── __init__.py
│   │   ├── user_dto.py
│   │   └── order_dto.py
│   ├── grpc/                    # gRPC services
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── user_servicer.py
│   │   └── protos/
│   │       ├── user.proto
│   │       └── common.proto
│   ├── middleware/              # Request middleware
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── error_handler.py
│   ├── config/                  # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── database.py
│   └── util/                    # Utilities
│       ├── __init__.py
│       ├── validators.py
│       └── helpers.py
├── migrations/                  # Alembic migrations
│   ├── versions/
│   └── env.py
├── tests/                       # Test suite
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── deployment/                  # Docker configs
│   ├── Dockerfile
│   └── docker-compose.yml
├── k8s/                         # Kubernetes manifests
│   ├── deployment.yaml
│   └── service.yaml
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── alembic.ini
└── wsgi.py
```

---

## Clean Architecture Layers

### Layer Responsibilities

| Layer | Responsibility | Dependencies |
|-------|----------------|--------------|
| **Controller** | HTTP/gRPC endpoints, request validation | Service |
| **Service** | Business logic, orchestration | Repository |
| **Repository** | Data access, caching | Database, Cache |

### Dependency Flow
```
┌─────────────────────────────────────────────────────────────┐
│                    Controller Layer                          │
│  ┌───────────────────┐    ┌───────────────────┐            │
│  │  Flask Blueprints │    │   gRPC Servicers  │            │
│  │  (REST API)       │    │   (Protobuf)      │            │
│  └─────────┬─────────┘    └─────────┬─────────┘            │
│            │                        │                       │
│            └──────────┬─────────────┘                       │
│                       ↓                                     │
├─────────────────────────────────────────────────────────────┤
│                     Service Layer                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Business Logic │ Validation │ Event Publishing       │  │
│  └───────────────────────────────────────────────────────┘  │
│                       │                                     │
│                       ↓                                     │
├─────────────────────────────────────────────────────────────┤
│                    Repository Layer                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐│
│  │ SQLAlchemy   │ │ Redis Cache  │ │ External APIs        ││
│  │ Repositories │ │ Repository   │ │ (gRPC Clients)       ││
│  └──────────────┘ └──────────────┘ └──────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Dependency Injection Pattern
```python
# app/container.py
from dependency_injector import containers, providers
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis

from app.config.settings import Settings
from app.repository.user_repository import UserRepository
from app.repository.cache_repository import CacheRepository
from app.service.user_service import UserService
from app.service.auth_service import AuthService


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Database
    engine = providers.Singleton(
        create_engine,
        config.database_url,
        pool_size=5,
        max_overflow=10,
    )

    session_factory = providers.Singleton(
        sessionmaker,
        bind=engine,
    )

    # Redis
    redis_client = providers.Singleton(
        redis.Redis.from_url,
        config.redis_url,
    )

    # Repositories
    user_repository = providers.Factory(
        UserRepository,
        session_factory=session_factory,
    )

    cache_repository = providers.Singleton(
        CacheRepository,
        redis_client=redis_client,
    )

    # Services
    user_service = providers.Factory(
        UserService,
        repository=user_repository,
        cache=cache_repository,
    )

    auth_service = providers.Factory(
        AuthService,
        user_repository=user_repository,
        settings=config.settings,
    )
```

---

## SQLAlchemy ORM

### Base Model
```python
# app/model/base.py
from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declarative_base, declared_attr

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class BaseModel(Base, TimestampMixin):
    """Base model with common functionality."""

    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        # Convert CamelCase to snake_case
        name = cls.__name__
        return "".join(
            ["_" + c.lower() if c.isupper() else c for c in name]
        ).lstrip("_") + "s"

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update(self, **kwargs: Any) -> None:
        """Update model attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
```

### Entity Model
```python
# app/model/user.py
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.model.base import BaseModel


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class SyncStatus(str, Enum):
    SYNCED = "synced"
    PENDING = "pending"
    FAILED = "failed"


# Many-to-many relationship table
user_roles = Table(
    "user_roles",
    BaseModel.metadata,
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
    Column("role_id", String(36), ForeignKey("roles.id"), primary_key=True),
)


class User(BaseModel):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE)
    sync_status = Column(SQLEnum(SyncStatus), default=SyncStatus.SYNCED)
    email_verified = Column(Boolean, default=False)

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "status": self.status.value,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def has_role(self, role_name: str) -> bool:
        return any(role.name == role_name for role in self.roles)


class Role(BaseModel):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))

    users = relationship("User", secondary=user_roles, back_populates="roles")


class UserProfile(BaseModel):
    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True)
    avatar_url = Column(String(500))
    bio = Column(String(1000))
    phone = Column(String(20))

    user = relationship("User", back_populates="profile")
```

### Repository Pattern
```python
# app/repository/base_repository.py
from typing import Generic, TypeVar, Optional, List, Type
from sqlalchemy.orm import Session, sessionmaker

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, session_factory: sessionmaker, model_class: Type[T]):
        self._session_factory = session_factory
        self._model_class = model_class

    @property
    def session(self) -> Session:
        return self._session_factory()

    def find_by_id(self, entity_id: str) -> Optional[T]:
        with self.session as session:
            return session.query(self._model_class).filter_by(id=entity_id).first()

    def find_all(
        self,
        page: int = 0,
        size: int = 10,
        **filters,
    ) -> tuple[List[T], int]:
        with self.session as session:
            query = session.query(self._model_class)

            for key, value in filters.items():
                if hasattr(self._model_class, key):
                    query = query.filter(getattr(self._model_class, key) == value)

            total = query.count()
            items = query.offset(page * size).limit(size).all()

            return items, total

    def save(self, entity: T) -> T:
        with self.session as session:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity

    def save_all(self, entities: List[T]) -> List[T]:
        with self.session as session:
            session.add_all(entities)
            session.commit()
            for entity in entities:
                session.refresh(entity)
            return entities

    def delete(self, entity: T) -> None:
        with self.session as session:
            session.delete(entity)
            session.commit()

    def delete_by_id(self, entity_id: str) -> bool:
        entity = self.find_by_id(entity_id)
        if entity:
            self.delete(entity)
            return True
        return False


# app/repository/user_repository.py
from typing import Optional, List
from sqlalchemy import or_
from app.model.user import User, SyncStatus
from app.repository.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session_factory):
        super().__init__(session_factory, User)

    def find_by_email(self, email: str) -> Optional[User]:
        with self.session as session:
            return session.query(User).filter(User.email == email).first()

    def find_by_status(self, status: str) -> List[User]:
        with self.session as session:
            return session.query(User).filter(User.status == status).all()

    def find_pending_sync(self) -> List[User]:
        with self.session as session:
            return (
                session.query(User)
                .filter(User.sync_status == SyncStatus.PENDING)
                .all()
            )

    def search(
        self,
        query: str,
        page: int = 0,
        size: int = 10,
    ) -> tuple[List[User], int]:
        with self.session as session:
            search_filter = or_(
                User.name.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%"),
            )

            base_query = session.query(User).filter(search_filter)
            total = base_query.count()
            users = base_query.offset(page * size).limit(size).all()

            return users, total

    def exists_by_email(self, email: str) -> bool:
        with self.session as session:
            return session.query(
                session.query(User).filter(User.email == email).exists()
            ).scalar()
```

---

## Flask Application

### Application Factory
```python
# app/__init__.py
from flask import Flask
from flask_cors import CORS
from app.config.settings import Settings
from app.config.database import init_db
from app.middleware.error_handler import register_error_handlers
from app.container import Container


def create_app(settings: Settings = None) -> Flask:
    """Application factory pattern."""
    app = Flask(__name__)

    # Load configuration
    settings = settings or Settings()
    app.config.from_object(settings)

    # Initialize container
    container = Container()
    container.config.from_pydantic(settings)
    app.container = container

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": settings.cors_origins}})

    # Initialize database
    init_db(app)

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    register_blueprints(app)

    # Register before/after request handlers
    register_request_handlers(app)

    return app


def register_blueprints(app: Flask) -> None:
    from app.controller.user_controller import user_bp
    from app.controller.auth_controller import auth_bp
    from app.controller.health_controller import health_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(health_bp)


def register_request_handlers(app: Flask) -> None:
    from flask import g

    @app.before_request
    def before_request():
        # Inject services into g
        g.user_service = app.container.user_service()
        g.auth_service = app.container.auth_service()

    @app.teardown_request
    def teardown_request(exception=None):
        # Cleanup
        pass
```

### Controller Blueprint
```python
# app/controller/user_controller.py
from flask import Blueprint, request, jsonify, g
from marshmallow import Schema, fields, validate, ValidationError, post_load
from app.middleware.auth import jwt_required, role_required
from app.dto.user_dto import CreateUserDTO, UpdateUserDTO

user_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


class CreateUserSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8),
        load_only=True,
    )

    @post_load
    def make_dto(self, data, **kwargs):
        return CreateUserDTO(**data)


class UpdateUserSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=255))
    email = fields.Email()

    @post_load
    def make_dto(self, data, **kwargs):
        return UpdateUserDTO(**data)


class PaginationSchema(Schema):
    page = fields.Int(load_default=0, validate=validate.Range(min=0))
    size = fields.Int(load_default=10, validate=validate.Range(min=1, max=100))


@user_bp.route("", methods=["GET"])
@jwt_required
def list_users():
    """List all users with pagination."""
    schema = PaginationSchema()
    try:
        params = schema.load(request.args)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    users, total = g.user_service.get_users(
        page=params["page"],
        size=params["size"],
    )

    return jsonify({
        "data": [u.to_dict() for u in users],
        "page": params["page"],
        "size": params["size"],
        "total": total,
        "total_pages": (total + params["size"] - 1) // params["size"],
    })


@user_bp.route("/<user_id>", methods=["GET"])
@jwt_required
def get_user(user_id: str):
    """Get user by ID."""
    user = g.user_service.get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict())


@user_bp.route("", methods=["POST"])
@role_required("admin")
def create_user():
    """Create new user."""
    schema = CreateUserSchema()

    try:
        dto = schema.load(request.json)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    try:
        user = g.user_service.create_user(dto)
        return jsonify(user.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@user_bp.route("/<user_id>", methods=["PUT"])
@jwt_required
def update_user(user_id: str):
    """Update user."""
    # Check permission
    if g.current_user_id != user_id and "admin" not in g.current_user_roles:
        return jsonify({"error": "Forbidden"}), 403

    schema = UpdateUserSchema()

    try:
        dto = schema.load(request.json)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    try:
        user = g.user_service.update_user(user_id, dto)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@user_bp.route("/<user_id>", methods=["DELETE"])
@role_required("admin")
def delete_user(user_id: str):
    """Delete user."""
    if g.user_service.delete_user(user_id):
        return "", 204
    return jsonify({"error": "User not found"}), 404


@user_bp.route("/me", methods=["GET"])
@jwt_required
def get_current_user():
    """Get current authenticated user."""
    user = g.user_service.get_user(g.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict())
```

### Error Handling
```python
# app/middleware/error_handler.py
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "error": "Bad Request",
            "message": str(error.description),
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            "error": "Unauthorized",
            "message": "Authentication required",
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            "error": "Forbidden",
            "message": "Insufficient permissions",
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Not Found",
            "message": "Resource not found",
        }), 404

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            "error": "Unprocessable Entity",
            "message": str(error.description),
        }), 422

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        logger.error(f"Database integrity error: {error}")
        return jsonify({
            "error": "Conflict",
            "message": "Database constraint violation",
        }), 409

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({
            "error": error.name,
            "message": error.description,
        }), error.code

    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.exception("Unhandled exception")
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        }), 500
```

---

## gRPC Services

### Protobuf Definition
```protobuf
// app/grpc/protos/user.proto
syntax = "proto3";

package arcana.user;

option python_generic_services = true;

import "google/protobuf/empty.proto";
import "google/protobuf/timestamp.proto";

service UserService {
    rpc GetUser (GetUserRequest) returns (UserResponse);
    rpc ListUsers (ListUsersRequest) returns (ListUsersResponse);
    rpc CreateUser (CreateUserRequest) returns (UserResponse);
    rpc UpdateUser (UpdateUserRequest) returns (UserResponse);
    rpc DeleteUser (DeleteUserRequest) returns (google.protobuf.Empty);
    rpc StreamUsers (ListUsersRequest) returns (stream UserResponse);
}

message GetUserRequest {
    string id = 1;
}

message ListUsersRequest {
    int32 page = 1;
    int32 size = 2;
    optional string status = 3;
}

message ListUsersResponse {
    repeated UserResponse users = 1;
    int32 total = 2;
    int32 page = 3;
    int32 size = 4;
}

message CreateUserRequest {
    string name = 1;
    string email = 2;
    string password = 3;
}

message UpdateUserRequest {
    string id = 1;
    optional string name = 2;
    optional string email = 3;
}

message DeleteUserRequest {
    string id = 1;
}

message UserResponse {
    string id = 1;
    string name = 2;
    string email = 3;
    string status = 4;
    google.protobuf.Timestamp created_at = 5;
    google.protobuf.Timestamp updated_at = 6;
}
```

### gRPC Servicer Implementation
```python
# app/grpc/user_servicer.py
import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from app.grpc.protos import user_pb2, user_pb2_grpc
from app.service.user_service import UserService
from app.dto.user_dto import CreateUserDTO, UpdateUserDTO


class UserServicer(user_pb2_grpc.UserServiceServicer):
    """gRPC User Service implementation."""

    def __init__(self, user_service: UserService):
        self._service = user_service

    def GetUser(self, request, context):
        user = self._service.get_user(request.id)

        if not user:
            context.abort(grpc.StatusCode.NOT_FOUND, "User not found")
            return user_pb2.UserResponse()

        return self._to_proto(user)

    def ListUsers(self, request, context):
        users, total = self._service.get_users(
            page=request.page,
            size=request.size,
        )

        return user_pb2.ListUsersResponse(
            users=[self._to_proto(u) for u in users],
            total=total,
            page=request.page,
            size=request.size,
        )

    def CreateUser(self, request, context):
        try:
            dto = CreateUserDTO(
                name=request.name,
                email=request.email,
                password=request.password,
            )
            user = self._service.create_user(dto)
            return self._to_proto(user)

        except ValueError as e:
            context.abort(grpc.StatusCode.ALREADY_EXISTS, str(e))
            return user_pb2.UserResponse()

    def UpdateUser(self, request, context):
        dto = UpdateUserDTO(
            name=request.name if request.HasField("name") else None,
            email=request.email if request.HasField("email") else None,
        )

        try:
            user = self._service.update_user(request.id, dto)
            if not user:
                context.abort(grpc.StatusCode.NOT_FOUND, "User not found")
                return user_pb2.UserResponse()
            return self._to_proto(user)

        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
            return user_pb2.UserResponse()

    def DeleteUser(self, request, context):
        from google.protobuf.empty_pb2 import Empty

        if self._service.delete_user(request.id):
            return Empty()

        context.abort(grpc.StatusCode.NOT_FOUND, "User not found")
        return Empty()

    def StreamUsers(self, request, context):
        """Server streaming RPC."""
        users, _ = self._service.get_users(
            page=request.page,
            size=request.size,
        )

        for user in users:
            if context.is_active():
                yield self._to_proto(user)
            else:
                break

    def _to_proto(self, user) -> user_pb2.UserResponse:
        created_at = Timestamp()
        created_at.FromDatetime(user.created_at)

        updated_at = Timestamp()
        updated_at.FromDatetime(user.updated_at)

        return user_pb2.UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            status=user.status.value,
            created_at=created_at,
            updated_at=updated_at,
        )


# app/grpc/server.py
import grpc
from concurrent import futures
import logging
from app.grpc.protos import user_pb2_grpc
from app.grpc.user_servicer import UserServicer
from app.grpc.interceptors import AuthInterceptor, LoggingInterceptor

logger = logging.getLogger(__name__)


def create_grpc_server(
    user_service,
    auth_service,
    port: int = 50051,
    max_workers: int = 10,
) -> grpc.Server:
    """Create and configure gRPC server."""

    # Create server with interceptors
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=max_workers),
        interceptors=[
            LoggingInterceptor(),
            AuthInterceptor(auth_service),
        ],
    )

    # Register servicers
    user_pb2_grpc.add_UserServiceServicer_to_server(
        UserServicer(user_service),
        server,
    )

    # Add port
    server.add_insecure_port(f"[::]:{port}")

    return server


def serve(user_service, auth_service, port: int = 50051):
    """Start gRPC server."""
    server = create_grpc_server(user_service, auth_service, port)
    server.start()
    logger.info(f"gRPC server started on port {port}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(grace=5)
        logger.info("gRPC server stopped")
```

### gRPC Interceptors
```python
# app/grpc/interceptors.py
import grpc
import logging
import time
from typing import Callable, Any

logger = logging.getLogger(__name__)


class LoggingInterceptor(grpc.ServerInterceptor):
    """Interceptor for logging gRPC calls."""

    def intercept_service(self, continuation, handler_call_details):
        method = handler_call_details.method
        start_time = time.time()

        def logging_wrapper(request_or_iterator, context):
            try:
                response = continuation(handler_call_details).unary_unary(
                    request_or_iterator, context
                )
                duration = (time.time() - start_time) * 1000
                logger.info(f"gRPC {method} completed in {duration:.2f}ms")
                return response
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(f"gRPC {method} failed in {duration:.2f}ms: {e}")
                raise

        return grpc.unary_unary_rpc_method_handler(
            logging_wrapper,
            request_deserializer=continuation(handler_call_details).request_deserializer,
            response_serializer=continuation(handler_call_details).response_serializer,
        )


class AuthInterceptor(grpc.ServerInterceptor):
    """Interceptor for JWT authentication."""

    # Methods that don't require authentication
    PUBLIC_METHODS = {
        "/arcana.auth.AuthService/Login",
        "/arcana.auth.AuthService/Register",
        "/grpc.health.v1.Health/Check",
    }

    def __init__(self, auth_service):
        self._auth_service = auth_service

    def intercept_service(self, continuation, handler_call_details):
        method = handler_call_details.method

        # Skip auth for public methods
        if method in self.PUBLIC_METHODS:
            return continuation(handler_call_details)

        def auth_wrapper(request_or_iterator, context):
            # Get metadata
            metadata = dict(context.invocation_metadata())
            auth_header = metadata.get("authorization", "")

            if not auth_header.startswith("Bearer "):
                context.abort(
                    grpc.StatusCode.UNAUTHENTICATED,
                    "Missing or invalid authorization header"
                )
                return

            token = auth_header[7:]  # Remove "Bearer " prefix
            payload = self._auth_service.verify_token(token)

            if not payload:
                context.abort(
                    grpc.StatusCode.UNAUTHENTICATED,
                    "Invalid or expired token"
                )
                return

            # Add user info to context
            context.user_id = payload["sub"]
            context.user_roles = payload.get("roles", [])

            return continuation(handler_call_details).unary_unary(
                request_or_iterator, context
            )

        return grpc.unary_unary_rpc_method_handler(
            auth_wrapper,
            request_deserializer=continuation(handler_call_details).request_deserializer,
            response_serializer=continuation(handler_call_details).response_serializer,
        )
```

---

## Authentication & Security

### JWT Authentication
```python
# app/middleware/auth.py
from functools import wraps
from typing import Optional, List
from flask import request, g, jsonify
import jwt
from datetime import datetime, timedelta


class JWTAuth:
    """JWT authentication handler."""

    def __init__(
        self,
        secret: str,
        algorithm: str = "HS256",
        access_token_expiry: int = 3600,  # 1 hour
        refresh_token_expiry: int = 604800,  # 7 days
    ):
        self._secret = secret
        self._algorithm = algorithm
        self._access_token_expiry = access_token_expiry
        self._refresh_token_expiry = refresh_token_expiry

    def create_access_token(self, user_id: str, roles: List[str]) -> str:
        """Create JWT access token."""
        payload = {
            "sub": user_id,
            "roles": roles,
            "type": "access",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=self._access_token_expiry),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token."""
        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=self._refresh_token_expiry),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def create_token_pair(self, user_id: str, roles: List[str]) -> dict:
        """Create access and refresh token pair."""
        return {
            "access_token": self.create_access_token(user_id, roles),
            "refresh_token": self.create_refresh_token(user_id),
            "token_type": "Bearer",
            "expires_in": self._access_token_expiry,
        }


def jwt_required(f):
    """Decorator for JWT-protected endpoints."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Missing authorization header"}), 401

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Invalid authorization header format"}), 401

        token = auth_header.split(" ")[1]
        jwt_auth: JWTAuth = g.jwt_auth

        payload = jwt_auth.verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        if payload.get("type") != "access":
            return jsonify({"error": "Invalid token type"}), 401

        g.current_user_id = payload["sub"]
        g.current_user_roles = payload.get("roles", [])

        return f(*args, **kwargs)

    return decorated


def role_required(*required_roles):
    """Decorator for role-based access control."""

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


def optional_auth(f):
    """Decorator for optional authentication."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            jwt_auth: JWTAuth = g.jwt_auth

            payload = jwt_auth.verify_token(token)
            if payload and payload.get("type") == "access":
                g.current_user_id = payload["sub"]
                g.current_user_roles = payload.get("roles", [])
            else:
                g.current_user_id = None
                g.current_user_roles = []
        else:
            g.current_user_id = None
            g.current_user_roles = []

        return f(*args, **kwargs)

    return decorated
```

---

## Caching with Redis

### Cache Repository
```python
# app/repository/cache_repository.py
import json
from typing import Optional, Any, TypeVar, Callable
from datetime import timedelta
import redis
import logging

T = TypeVar("T")
logger = logging.getLogger(__name__)


class CacheRepository:
    """Redis cache repository."""

    def __init__(
        self,
        redis_client: redis.Redis,
        default_ttl: int = 3600,
        prefix: str = "arcana:",
    ):
        self._redis = redis_client
        self._default_ttl = default_ttl
        self._prefix = prefix

    def _key(self, key: str) -> str:
        """Generate prefixed key."""
        return f"{self._prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            data = self._redis.get(self._key(key))
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache."""
        try:
            ttl = ttl or self._default_ttl
            self._redis.setex(
                self._key(key),
                ttl,
                json.dumps(value, default=str),
            )
            return True
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            self._redis.delete(self._key(key))
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = self._redis.keys(self._key(pattern))
            if keys:
                return self._redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    def get_or_set(
        self,
        key: str,
        factory: Callable[[], T],
        ttl: Optional[int] = None,
    ) -> T:
        """Get from cache or compute and cache."""
        cached = self.get(key)
        if cached is not None:
            return cached

        value = factory()
        self.set(key, value, ttl)
        return value

    def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        return self._redis.incr(self._key(key), amount)

    def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement counter."""
        return self._redis.decr(self._key(key), amount)

    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on key."""
        return self._redis.expire(self._key(key), ttl)


# Cached service decorator
def cached(
    key_template: str,
    ttl: int = 3600,
    key_builder: Optional[Callable] = None,
):
    """Decorator for caching method results."""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            cache: CacheRepository = getattr(self, "_cache", None)
            if not cache:
                return func(self, *args, **kwargs)

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = key_template.format(*args, **kwargs)

            # Try cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute and cache
            result = func(self, *args, **kwargs)
            if result is not None:
                cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator
```

---

## Testing

### Test Configuration
```python
# tests/conftest.py
import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import create_app
from app.model.base import Base
from app.config.settings import Settings


@pytest.fixture
def test_settings():
    return Settings(
        database_url="sqlite:///:memory:",
        redis_url="redis://localhost:6379/1",
        jwt_secret="test-secret-key",
        debug=True,
    )


@pytest.fixture
def test_app(test_settings):
    app = create_app(test_settings)
    app.config["TESTING"] = True

    with app.app_context():
        # Create tables
        engine = create_engine(test_settings.database_url)
        Base.metadata.create_all(engine)
        yield app
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(test_app):
    return test_app.test_client()


@pytest.fixture
def db_session(test_settings):
    engine = create_engine(test_settings.database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def mock_user_repository():
    return Mock()


@pytest.fixture
def mock_cache_repository():
    return Mock()


@pytest.fixture
def user_service(mock_user_repository, mock_cache_repository):
    from app.service.user_service import UserService
    return UserService(
        repository=mock_user_repository,
        cache=mock_cache_repository,
    )


@pytest.fixture
def auth_token(test_app):
    """Generate valid auth token for testing."""
    from app.middleware.auth import JWTAuth

    jwt_auth = JWTAuth(secret="test-secret-key")
    return jwt_auth.create_access_token(
        user_id="test-user-id",
        roles=["user", "admin"],
    )
```

### Unit Tests
```python
# tests/unit/test_user_service.py
import pytest
from unittest.mock import Mock
from app.service.user_service import UserService
from app.model.user import User, SyncStatus
from app.dto.user_dto import CreateUserDTO, UpdateUserDTO


class TestUserService:
    def test_get_user_found(self, user_service, mock_user_repository):
        # Arrange
        expected_user = User(
            id="123",
            name="John Doe",
            email="john@example.com",
            password_hash="hash",
            sync_status=SyncStatus.SYNCED,
        )
        mock_user_repository.find_by_id.return_value = expected_user

        # Act
        result = user_service.get_user("123")

        # Assert
        assert result == expected_user
        mock_user_repository.find_by_id.assert_called_once_with("123")

    def test_get_user_not_found(self, user_service, mock_user_repository):
        # Arrange
        mock_user_repository.find_by_id.return_value = None

        # Act
        result = user_service.get_user("nonexistent")

        # Assert
        assert result is None

    def test_create_user_success(self, user_service, mock_user_repository):
        # Arrange
        mock_user_repository.find_by_email.return_value = None
        mock_user_repository.save.side_effect = lambda u: u

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
        mock_user_repository.save.assert_called_once()

    def test_create_user_email_exists(self, user_service, mock_user_repository):
        # Arrange
        existing_user = User(
            id="456",
            name="Existing User",
            email="john@example.com",
            password_hash="hash",
        )
        mock_user_repository.find_by_email.return_value = existing_user

        dto = CreateUserDTO(
            name="John Doe",
            email="john@example.com",
            password="password123",
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Email already registered"):
            user_service.create_user(dto)

    def test_update_user_success(self, user_service, mock_user_repository):
        # Arrange
        existing_user = User(
            id="123",
            name="John Doe",
            email="john@example.com",
            password_hash="hash",
        )
        mock_user_repository.find_by_id.return_value = existing_user
        mock_user_repository.update.side_effect = lambda u: u

        dto = UpdateUserDTO(name="Jane Doe")

        # Act
        result = user_service.update_user("123", dto)

        # Assert
        assert result.name == "Jane Doe"

    def test_delete_user_success(self, user_service, mock_user_repository):
        # Arrange
        user = User(id="123", name="John", email="john@example.com", password_hash="hash")
        mock_user_repository.find_by_id.return_value = user

        # Act
        result = user_service.delete_user("123")

        # Assert
        assert result is True
        mock_user_repository.delete.assert_called_once_with(user)

    def test_delete_user_not_found(self, user_service, mock_user_repository):
        # Arrange
        mock_user_repository.find_by_id.return_value = None

        # Act
        result = user_service.delete_user("nonexistent")

        # Assert
        assert result is False
        mock_user_repository.delete.assert_not_called()
```

### Integration Tests
```python
# tests/integration/test_user_controller.py
import pytest
import json


class TestUserController:
    def test_list_users(self, client, auth_token):
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "data" in data
        assert "total" in data

    def test_list_users_unauthorized(self, client):
        response = client.get("/api/v1/users")

        assert response.status_code == 401

    def test_create_user(self, client, auth_token):
        response = client.post(
            "/api/v1/users",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "name": "Test User",
                "email": "test@example.com",
                "password": "password123",
            }),
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"

    def test_create_user_validation_error(self, client, auth_token):
        response = client.post(
            "/api/v1/users",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "name": "Test User",
                "email": "invalid-email",
                "password": "short",
            }),
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "errors" in data

    def test_get_user(self, client, auth_token):
        # First create a user
        create_response = client.post(
            "/api/v1/users",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "name": "Test User",
                "email": "test2@example.com",
                "password": "password123",
            }),
        )

        user_id = json.loads(create_response.data)["id"]

        # Then get the user
        response = client.get(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == user_id

    def test_get_user_not_found(self, client, auth_token):
        response = client.get(
            "/api/v1/users/nonexistent-id",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404
```

---

## Deployment

### Docker Configuration
```dockerfile
# deployment/Dockerfile
FROM python:3.14-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.14-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

# Expose ports
EXPOSE 5000 50051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
```

### Docker Compose
```yaml
# deployment/docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: ..
      dockerfile: deployment/Dockerfile
    ports:
      - "5000:5000"
      - "50051:50051"
    environment:
      - DATABASE_URL=mysql://user:password@db:3306/arcana
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=root
      - MYSQL_DATABASE=arcana
      - MYSQL_USER=user
      - MYSQL_PASSWORD=password
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arcana-python
  labels:
    app: arcana-python
spec:
  replicas: 3
  selector:
    matchLabels:
      app: arcana-python
  template:
    metadata:
      labels:
        app: arcana-python
    spec:
      containers:
        - name: arcana-python
          image: arcana/python:latest
          ports:
            - containerPort: 5000
              name: http
            - containerPort: 50051
              name: grpc
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: arcana-secrets
                  key: database-url
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: arcana-secrets
                  key: redis-url
            - name: JWT_SECRET
              valueFrom:
                secretKeyRef:
                  name: arcana-secrets
                  key: jwt-secret
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 5
```
