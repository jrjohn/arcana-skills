# Python Developer Skill - Design Patterns

## Table of Contents
1. [Architecture Patterns](#architecture-patterns)
2. [Service Layer Patterns](#service-layer-patterns)
3. [Data Access Patterns](#data-access-patterns)
4. [API Design Patterns](#api-design-patterns)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Testing Patterns](#testing-patterns)
7. [Concurrency Patterns](#concurrency-patterns)

---

## Architecture Patterns

### Clean Architecture Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                         Controllers                              │
│  ┌─────────────────────┐     ┌─────────────────────────────┐   │
│  │   Flask Blueprints  │     │      gRPC Servicers         │   │
│  │   (REST API)        │     │      (Protobuf)             │   │
│  └──────────┬──────────┘     └──────────────┬──────────────┘   │
│             │                                │                   │
│             └───────────────┬────────────────┘                   │
│                             ↓                                    │
├─────────────────────────────────────────────────────────────────┤
│                         Services                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Business Logic │ Validation │ Event Publishing             ││
│  │                                                              ││
│  │  Pure Python classes, no framework dependencies             ││
│  └─────────────────────────────────────────────────────────────┘│
│                             │                                    │
│                             ↓                                    │
├─────────────────────────────────────────────────────────────────┤
│                       Repositories                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│
│  │ SQLAlchemy   │ │ Redis Cache  │ │ External API Clients     ││
│  │ Repositories │ │ Repository   │ │ (gRPC/REST)              ││
│  └──────────────┘ └──────────────┘ └──────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Implementation
```python
# Controller Layer - HTTP concerns only
@user_bp.route("/<user_id>", methods=["GET"])
@jwt_required
def get_user(user_id: str):
    user = g.user_service.get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict())


# Service Layer - Business logic
class UserService:
    def __init__(
        self,
        repository: UserRepository,
        cache: CacheRepository,
        event_publisher: EventPublisher,
    ):
        self._repo = repository
        self._cache = cache
        self._events = event_publisher

    def get_user(self, user_id: str) -> Optional[User]:
        # Try cache first
        cached = self._cache.get(f"user:{user_id}")
        if cached:
            return self._dict_to_user(cached)

        # Load from database
        user = self._repo.find_by_id(user_id)
        if user:
            self._cache.set(f"user:{user_id}", user.to_dict())

        return user


# Repository Layer - Data access
class UserRepository(BaseRepository[User]):
    def find_by_email(self, email: str) -> Optional[User]:
        with self.session as session:
            return session.query(User).filter(User.email == email).first()
```

### Dependency Injection Container

```python
# app/container.py
from dependency_injector import containers, providers
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis


class Container(containers.DeclarativeContainer):
    """Dependency injection container."""

    config = providers.Configuration()

    # Infrastructure
    engine = providers.Singleton(
        create_engine,
        config.database_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

    session_factory = providers.Singleton(
        sessionmaker,
        bind=engine,
        expire_on_commit=False,
    )

    redis_client = providers.Singleton(
        redis.Redis.from_url,
        config.redis_url,
        decode_responses=True,
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

    # Event publishing
    event_publisher = providers.Singleton(
        EventPublisher,
        redis_client=redis_client,
    )

    # Services
    user_service = providers.Factory(
        UserService,
        repository=user_repository,
        cache=cache_repository,
        event_publisher=event_publisher,
    )

    auth_service = providers.Factory(
        AuthService,
        user_repository=user_repository,
        jwt_secret=config.jwt_secret,
    )


# Usage
container = Container()
container.config.from_pydantic(settings)

user_service = container.user_service()
```

---

## Service Layer Patterns

### Strategy Pattern

```python
from abc import ABC, abstractmethod
from typing import Dict, Type
from decimal import Decimal


class PricingStrategy(ABC):
    """Abstract pricing strategy."""

    @abstractmethod
    def calculate(self, base_price: Decimal, quantity: int) -> Decimal:
        pass


class RegularPricing(PricingStrategy):
    def calculate(self, base_price: Decimal, quantity: int) -> Decimal:
        return base_price * quantity


class BulkPricing(PricingStrategy):
    def __init__(self, discount_threshold: int = 10, discount_rate: Decimal = Decimal("0.10")):
        self.threshold = discount_threshold
        self.discount = discount_rate

    def calculate(self, base_price: Decimal, quantity: int) -> Decimal:
        total = base_price * quantity
        if quantity >= self.threshold:
            total *= (1 - self.discount)
        return total


class PremiumPricing(PricingStrategy):
    def __init__(self, discount_rate: Decimal = Decimal("0.15")):
        self.discount = discount_rate

    def calculate(self, base_price: Decimal, quantity: int) -> Decimal:
        return base_price * quantity * (1 - self.discount)


class PricingStrategyFactory:
    """Factory for creating pricing strategies."""

    _strategies: Dict[str, Type[PricingStrategy]] = {
        "regular": RegularPricing,
        "bulk": BulkPricing,
        "premium": PremiumPricing,
    }

    @classmethod
    def create(cls, strategy_type: str, **kwargs) -> PricingStrategy:
        strategy_class = cls._strategies.get(strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {strategy_type}")
        return strategy_class(**kwargs)


# Usage
class OrderService:
    def calculate_order_total(
        self,
        items: list,
        customer_type: str,
    ) -> Decimal:
        strategy = PricingStrategyFactory.create(customer_type)
        total = Decimal("0")

        for item in items:
            total += strategy.calculate(item.price, item.quantity)

        return total
```

### Command Pattern

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, Dict, Type
from datetime import datetime

T = TypeVar("T")


class Command(ABC):
    """Base command class."""
    pass


class CommandHandler(ABC, Generic[T]):
    """Base command handler."""

    @abstractmethod
    def handle(self, command: Command) -> T:
        pass


# Commands
@dataclass
class CreateUserCommand(Command):
    name: str
    email: str
    password: str


@dataclass
class UpdateUserCommand(Command):
    user_id: str
    name: str = None
    email: str = None


@dataclass
class DeleteUserCommand(Command):
    user_id: str


# Handlers
class CreateUserHandler(CommandHandler[User]):
    def __init__(self, repository: UserRepository, event_publisher: EventPublisher):
        self._repo = repository
        self._events = event_publisher

    def handle(self, command: CreateUserCommand) -> User:
        # Validation
        if self._repo.exists_by_email(command.email):
            raise ValueError("Email already exists")

        # Create user
        user = User(
            id=str(uuid4()),
            name=command.name,
            email=command.email,
            password_hash=generate_password_hash(command.password),
        )

        user = self._repo.save(user)

        # Publish event
        self._events.publish("user.created", {"user_id": user.id})

        return user


class UpdateUserHandler(CommandHandler[User]):
    def __init__(self, repository: UserRepository):
        self._repo = repository

    def handle(self, command: UpdateUserCommand) -> User:
        user = self._repo.find_by_id(command.user_id)
        if not user:
            raise ValueError("User not found")

        if command.name:
            user.name = command.name
        if command.email:
            user.email = command.email

        return self._repo.save(user)


# Command Bus
class CommandBus:
    """Dispatches commands to handlers."""

    def __init__(self):
        self._handlers: Dict[Type[Command], CommandHandler] = {}

    def register(self, command_type: Type[Command], handler: CommandHandler) -> None:
        self._handlers[command_type] = handler

    def dispatch(self, command: Command) -> any:
        handler = self._handlers.get(type(command))
        if not handler:
            raise ValueError(f"No handler for command: {type(command).__name__}")
        return handler.handle(command)


# Usage
bus = CommandBus()
bus.register(CreateUserCommand, CreateUserHandler(repo, events))
bus.register(UpdateUserCommand, UpdateUserHandler(repo))

user = bus.dispatch(CreateUserCommand(name="John", email="john@example.com", password="secret"))
```

### Unit of Work Pattern

```python
from contextlib import contextmanager
from typing import List, TypeVar, Generic
from sqlalchemy.orm import Session

T = TypeVar("T")


class UnitOfWork:
    """Unit of Work for managing transactions."""

    def __init__(self, session_factory):
        self._session_factory = session_factory
        self._session: Session = None
        self._committed = False

    def __enter__(self):
        self._session = self._session_factory()
        self._committed = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        elif not self._committed:
            self.rollback()
        self._session.close()

    @property
    def session(self) -> Session:
        return self._session

    def commit(self) -> None:
        self._session.commit()
        self._committed = True

    def rollback(self) -> None:
        self._session.rollback()

    def add(self, entity: T) -> T:
        self._session.add(entity)
        return entity

    def add_all(self, entities: List[T]) -> List[T]:
        self._session.add_all(entities)
        return entities

    def delete(self, entity: T) -> None:
        self._session.delete(entity)


# Usage
class OrderService:
    def __init__(self, uow_factory):
        self._uow_factory = uow_factory

    def create_order(self, user_id: str, items: List[OrderItem]) -> Order:
        with self._uow_factory() as uow:
            # Create order
            order = Order(
                id=str(uuid4()),
                user_id=user_id,
                status=OrderStatus.PENDING,
            )
            uow.add(order)

            # Add items
            for item in items:
                item.order_id = order.id
                uow.add(item)

            # Update inventory
            for item in items:
                product = uow.session.query(Product).filter_by(id=item.product_id).first()
                product.stock -= item.quantity

            uow.commit()
            return order
```

---

## Data Access Patterns

### Repository Pattern

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Callable, Any
from sqlalchemy.orm import Session

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Abstract repository interface."""

    @abstractmethod
    def find_by_id(self, entity_id: str) -> Optional[T]:
        pass

    @abstractmethod
    def find_all(self, **filters) -> List[T]:
        pass

    @abstractmethod
    def save(self, entity: T) -> T:
        pass

    @abstractmethod
    def delete(self, entity: T) -> None:
        pass


class SQLAlchemyRepository(Repository[T]):
    """SQLAlchemy implementation of repository."""

    def __init__(self, session_factory: Callable[[], Session], model_class: type):
        self._session_factory = session_factory
        self._model_class = model_class

    @property
    def session(self) -> Session:
        return self._session_factory()

    def find_by_id(self, entity_id: str) -> Optional[T]:
        with self.session as session:
            return session.query(self._model_class).filter_by(id=entity_id).first()

    def find_all(self, page: int = 0, size: int = 100, **filters) -> tuple[List[T], int]:
        with self.session as session:
            query = session.query(self._model_class)

            for key, value in filters.items():
                if hasattr(self._model_class, key) and value is not None:
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

    def delete(self, entity: T) -> None:
        with self.session as session:
            session.delete(entity)
            session.commit()


# Specification Pattern for complex queries
class Specification(ABC):
    """Base specification for filtering."""

    @abstractmethod
    def is_satisfied_by(self, query):
        pass

    def __and__(self, other: "Specification") -> "AndSpecification":
        return AndSpecification(self, other)

    def __or__(self, other: "Specification") -> "OrSpecification":
        return OrSpecification(self, other)


class AndSpecification(Specification):
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, query):
        return self.left.is_satisfied_by(self.right.is_satisfied_by(query))


class OrSpecification(Specification):
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, query):
        from sqlalchemy import or_
        # Implementation depends on how you want to combine queries
        pass


# Concrete specifications
class UserByStatusSpec(Specification):
    def __init__(self, status: str):
        self.status = status

    def is_satisfied_by(self, query):
        return query.filter(User.status == self.status)


class UserByDepartmentSpec(Specification):
    def __init__(self, department: str):
        self.department = department

    def is_satisfied_by(self, query):
        return query.filter(User.department == self.department)


class UserCreatedAfterSpec(Specification):
    def __init__(self, date: datetime):
        self.date = date

    def is_satisfied_by(self, query):
        return query.filter(User.created_at >= self.date)


# Usage
class UserRepository(SQLAlchemyRepository[User]):
    def find_by_specification(self, spec: Specification) -> List[User]:
        with self.session as session:
            query = session.query(User)
            query = spec.is_satisfied_by(query)
            return query.all()


# Example
spec = UserByStatusSpec("active") & UserByDepartmentSpec("engineering")
users = user_repo.find_by_specification(spec)
```

### Cache-Aside Pattern

```python
from typing import Optional, Callable, TypeVar, Any
import json
import hashlib
from functools import wraps

T = TypeVar("T")


class CacheAside:
    """Cache-aside pattern implementation."""

    def __init__(self, cache_client, default_ttl: int = 3600, prefix: str = ""):
        self._cache = cache_client
        self._default_ttl = default_ttl
        self._prefix = prefix

    def _make_key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        data = self._cache.get(self._make_key(key))
        if data:
            return json.loads(data)
        return None

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache."""
        self._cache.setex(
            self._make_key(key),
            ttl or self._default_ttl,
            json.dumps(value, default=str),
        )

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        self._cache.delete(self._make_key(key))

    def get_or_load(
        self,
        key: str,
        loader: Callable[[], T],
        ttl: int = None,
    ) -> T:
        """Get from cache or load from source."""
        cached = self.get(key)
        if cached is not None:
            return cached

        value = loader()
        if value is not None:
            self.set(key, value, ttl)

        return value


def cached(key_template: str, ttl: int = 3600):
    """Decorator for caching method results."""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Build cache key
            cache_key = key_template.format(*args, **kwargs)

            # Get cache instance
            cache = getattr(self, "_cache", None)
            if not cache:
                return func(self, *args, **kwargs)

            # Try cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute and cache
            result = func(self, *args, **kwargs)
            if result is not None:
                cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def cache_invalidate(*key_templates: str):
    """Decorator to invalidate cache after method execution."""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)

            cache = getattr(self, "_cache", None)
            if cache:
                for template in key_templates:
                    key = template.format(*args, **kwargs)
                    cache.delete(key)

            return result

        return wrapper

    return decorator


# Usage
class UserService:
    def __init__(self, repository: UserRepository, cache: CacheAside):
        self._repo = repository
        self._cache = cache

    @cached("user:{0}", ttl=1800)
    def get_user(self, user_id: str) -> Optional[User]:
        return self._repo.find_by_id(user_id)

    @cache_invalidate("user:{0}")
    def update_user(self, user_id: str, data: dict) -> User:
        user = self._repo.find_by_id(user_id)
        user.update(**data)
        return self._repo.save(user)

    @cache_invalidate("user:{0}")
    def delete_user(self, user_id: str) -> None:
        user = self._repo.find_by_id(user_id)
        if user:
            self._repo.delete(user)
```

---

## API Design Patterns

### Blueprint Factory Pattern

```python
from flask import Blueprint
from typing import Callable


def create_crud_blueprint(
    name: str,
    url_prefix: str,
    service_getter: Callable,
    schema_class: type,
    auth_required: bool = True,
) -> Blueprint:
    """Factory for creating CRUD blueprints."""

    bp = Blueprint(name, __name__, url_prefix=url_prefix)
    schema = schema_class()

    @bp.route("", methods=["GET"])
    def list_items():
        service = service_getter()
        page = request.args.get("page", 0, type=int)
        size = request.args.get("size", 10, type=int)

        items, total = service.get_all(page=page, size=size)

        return jsonify({
            "data": [schema.dump(item) for item in items],
            "page": page,
            "size": size,
            "total": total,
        })

    @bp.route("/<item_id>", methods=["GET"])
    def get_item(item_id: str):
        service = service_getter()
        item = service.get_by_id(item_id)

        if not item:
            return jsonify({"error": "Not found"}), 404

        return jsonify(schema.dump(item))

    @bp.route("", methods=["POST"])
    def create_item():
        service = service_getter()

        try:
            data = schema.load(request.json)
        except ValidationError as e:
            return jsonify({"errors": e.messages}), 400

        item = service.create(data)
        return jsonify(schema.dump(item)), 201

    @bp.route("/<item_id>", methods=["PUT"])
    def update_item(item_id: str):
        service = service_getter()

        try:
            data = schema.load(request.json, partial=True)
        except ValidationError as e:
            return jsonify({"errors": e.messages}), 400

        item = service.update(item_id, data)
        if not item:
            return jsonify({"error": "Not found"}), 404

        return jsonify(schema.dump(item))

    @bp.route("/<item_id>", methods=["DELETE"])
    def delete_item(item_id: str):
        service = service_getter()

        if service.delete(item_id):
            return "", 204

        return jsonify({"error": "Not found"}), 404

    if auth_required:
        bp.before_request(jwt_required_wrapper)

    return bp


# Usage
user_bp = create_crud_blueprint(
    name="users",
    url_prefix="/api/v1/users",
    service_getter=lambda: g.user_service,
    schema_class=UserSchema,
)
```

### Request/Response DTO Pattern

```python
from dataclasses import dataclass, field
from typing import Optional, List, TypeVar, Generic
from datetime import datetime
from marshmallow import Schema, fields, post_load, validate

T = TypeVar("T")


# Response wrapper
@dataclass
class ApiResponse(Generic[T]):
    data: T
    message: str = "Success"
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "data": self.data if not hasattr(self.data, "to_dict") else self.data.to_dict(),
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PaginatedResponse(Generic[T]):
    data: List[T]
    page: int
    size: int
    total: int

    @property
    def total_pages(self) -> int:
        return (self.total + self.size - 1) // self.size

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages - 1

    @property
    def has_previous(self) -> bool:
        return self.page > 0

    def to_dict(self) -> dict:
        return {
            "data": [item.to_dict() if hasattr(item, "to_dict") else item for item in self.data],
            "page": self.page,
            "size": self.size,
            "total": self.total,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_previous": self.has_previous,
        }


@dataclass
class ErrorResponse:
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        result = {
            "error": self.error,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.details:
            result["details"] = self.details
        return result


# Schema with automatic DTO conversion
class CreateUserRequestSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8), load_only=True)

    @post_load
    def make_dto(self, data, **kwargs):
        return CreateUserDTO(**data)


class UserResponseSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    email = fields.Str()
    status = fields.Str()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


# Helper for consistent responses
def success_response(data, message: str = "Success"):
    return jsonify(ApiResponse(data=data, message=message).to_dict())


def paginated_response(items: List, page: int, size: int, total: int):
    return jsonify(PaginatedResponse(
        data=items,
        page=page,
        size=size,
        total=total,
    ).to_dict())


def error_response(error: str, message: str, status_code: int, details: dict = None):
    return jsonify(ErrorResponse(
        error=error,
        message=message,
        details=details,
    ).to_dict()), status_code
```

---

## Error Handling Patterns

### Custom Exception Hierarchy

```python
from typing import Optional, Dict, Any


class AppException(Exception):
    """Base application exception."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An internal error occurred"

    def __init__(
        self,
        message: str = None,
        details: Dict[str, Any] = None,
    ):
        self.message = message or self.__class__.message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ValidationException(AppException):
    status_code = 400
    error_code = "VALIDATION_ERROR"
    message = "Validation failed"


class AuthenticationException(AppException):
    status_code = 401
    error_code = "AUTHENTICATION_ERROR"
    message = "Authentication failed"


class AuthorizationException(AppException):
    status_code = 403
    error_code = "AUTHORIZATION_ERROR"
    message = "Not authorized"


class NotFoundException(AppException):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"


class ConflictException(AppException):
    status_code = 409
    error_code = "CONFLICT"
    message = "Resource conflict"


class RateLimitException(AppException):
    status_code = 429
    error_code = "RATE_LIMIT"
    message = "Rate limit exceeded"


# Entity-specific exceptions
class UserNotFoundException(NotFoundException):
    error_code = "USER_NOT_FOUND"
    message = "User not found"

    def __init__(self, user_id: str):
        super().__init__(f"User not found: {user_id}", {"user_id": user_id})


class EmailAlreadyExistsException(ConflictException):
    error_code = "EMAIL_EXISTS"
    message = "Email already registered"

    def __init__(self, email: str):
        super().__init__(f"Email already registered: {email}", {"email": email})


# Global error handler
def register_error_handlers(app):
    @app.errorhandler(AppException)
    def handle_app_exception(error: AppException):
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        return jsonify({
            "error": "VALIDATION_ERROR",
            "message": "Validation failed",
            "details": error.messages,
        }), 400

    @app.errorhandler(Exception)
    def handle_exception(error: Exception):
        app.logger.exception("Unhandled exception")
        return jsonify({
            "error": "INTERNAL_ERROR",
            "message": "An internal error occurred",
        }), 500
```

### Result Pattern

```python
from dataclasses import dataclass
from typing import TypeVar, Generic, Union, Optional, Callable

T = TypeVar("T")
E = TypeVar("E")


@dataclass
class Success(Generic[T]):
    value: T

    @property
    def is_success(self) -> bool:
        return True

    @property
    def is_failure(self) -> bool:
        return False


@dataclass
class Failure(Generic[E]):
    error: E

    @property
    def is_success(self) -> bool:
        return False

    @property
    def is_failure(self) -> bool:
        return True


Result = Union[Success[T], Failure[E]]


def success(value: T) -> Result[T, E]:
    return Success(value)


def failure(error: E) -> Result[T, E]:
    return Failure(error)


# Helper functions
def map_result(result: Result[T, E], func: Callable[[T], U]) -> Result[U, E]:
    if result.is_success:
        return success(func(result.value))
    return result


def flat_map_result(result: Result[T, E], func: Callable[[T], Result[U, E]]) -> Result[U, E]:
    if result.is_success:
        return func(result.value)
    return result


# Usage in service
class UserService:
    def create_user(self, dto: CreateUserDTO) -> Result[User, str]:
        # Validation
        if self._repo.exists_by_email(dto.email):
            return failure("Email already exists")

        try:
            user = User(
                id=str(uuid4()),
                name=dto.name,
                email=dto.email,
                password_hash=generate_password_hash(dto.password),
            )
            user = self._repo.save(user)
            return success(user)

        except Exception as e:
            return failure(str(e))


# Usage in controller
@user_bp.route("", methods=["POST"])
def create_user():
    dto = CreateUserSchema().load(request.json)
    result = g.user_service.create_user(dto)

    if result.is_success:
        return jsonify(result.value.to_dict()), 201
    else:
        return jsonify({"error": result.error}), 400
```

---

## Testing Patterns

### Test Fixtures with pytest

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.model.base import Base


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(engine):
    """Create database session."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def mock_repository():
    """Create mock repository."""
    return Mock()


@pytest.fixture
def mock_cache():
    """Create mock cache."""
    mock = Mock()
    mock.get.return_value = None
    return mock


@pytest.fixture
def mock_event_publisher():
    """Create mock event publisher."""
    return Mock()


@pytest.fixture
def user_service(mock_repository, mock_cache, mock_event_publisher):
    """Create user service with mocks."""
    return UserService(
        repository=mock_repository,
        cache=mock_cache,
        event_publisher=mock_event_publisher,
    )


# Test fixtures for models
@pytest.fixture
def sample_user():
    """Create sample user."""
    return User(
        id="test-user-id",
        name="Test User",
        email="test@example.com",
        password_hash="hashed_password",
        status=UserStatus.ACTIVE,
    )


@pytest.fixture
def sample_users():
    """Create list of sample users."""
    return [
        User(id=f"user-{i}", name=f"User {i}", email=f"user{i}@example.com", password_hash="hash")
        for i in range(5)
    ]
```

### Service Layer Tests

```python
# tests/unit/test_user_service.py
import pytest
from unittest.mock import Mock, patch
from app.service.user_service import UserService
from app.model.user import User, UserStatus
from app.dto.user_dto import CreateUserDTO


class TestUserService:
    def test_get_user_from_cache(self, user_service, mock_repository, mock_cache, sample_user):
        """Should return user from cache when available."""
        mock_cache.get.return_value = sample_user.to_dict()

        result = user_service.get_user("test-user-id")

        assert result.id == sample_user.id
        mock_cache.get.assert_called_once()
        mock_repository.find_by_id.assert_not_called()

    def test_get_user_from_database(self, user_service, mock_repository, mock_cache, sample_user):
        """Should return user from database when not in cache."""
        mock_cache.get.return_value = None
        mock_repository.find_by_id.return_value = sample_user

        result = user_service.get_user("test-user-id")

        assert result.id == sample_user.id
        mock_repository.find_by_id.assert_called_once_with("test-user-id")
        mock_cache.set.assert_called_once()

    def test_get_user_not_found(self, user_service, mock_repository, mock_cache):
        """Should return None when user not found."""
        mock_cache.get.return_value = None
        mock_repository.find_by_id.return_value = None

        result = user_service.get_user("nonexistent")

        assert result is None

    def test_create_user_success(self, user_service, mock_repository, mock_event_publisher):
        """Should create user successfully."""
        mock_repository.exists_by_email.return_value = False
        mock_repository.save.side_effect = lambda u: u

        dto = CreateUserDTO(name="John", email="john@example.com", password="password123")
        result = user_service.create_user(dto)

        assert result.name == "John"
        assert result.email == "john@example.com"
        mock_repository.save.assert_called_once()
        mock_event_publisher.publish.assert_called_once()

    def test_create_user_email_exists(self, user_service, mock_repository):
        """Should raise error when email exists."""
        mock_repository.exists_by_email.return_value = True

        dto = CreateUserDTO(name="John", email="existing@example.com", password="password123")

        with pytest.raises(ValueError, match="Email already exists"):
            user_service.create_user(dto)

        mock_repository.save.assert_not_called()
```

### Integration Tests

```python
# tests/integration/test_user_controller.py
import pytest
import json


class TestUserController:
    def test_list_users(self, client, auth_headers):
        """Should list users with pagination."""
        response = client.get("/api/v1/users", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "data" in data
        assert "total" in data
        assert "page" in data

    def test_list_users_unauthorized(self, client):
        """Should return 401 without auth."""
        response = client.get("/api/v1/users")

        assert response.status_code == 401

    def test_create_user(self, client, admin_auth_headers):
        """Should create user with valid data."""
        response = client.post(
            "/api/v1/users",
            headers=admin_auth_headers,
            data=json.dumps({
                "name": "New User",
                "email": "new@example.com",
                "password": "password123",
            }),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "New User"
        assert data["email"] == "new@example.com"
        assert "id" in data

    def test_create_user_validation_error(self, client, admin_auth_headers):
        """Should return 400 for invalid data."""
        response = client.post(
            "/api/v1/users",
            headers=admin_auth_headers,
            data=json.dumps({
                "name": "",
                "email": "invalid",
                "password": "short",
            }),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "errors" in data

    def test_get_user(self, client, auth_headers, created_user):
        """Should get user by ID."""
        response = client.get(
            f"/api/v1/users/{created_user['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == created_user["id"]

    def test_get_user_not_found(self, client, auth_headers):
        """Should return 404 for nonexistent user."""
        response = client.get(
            "/api/v1/users/nonexistent-id",
            headers=auth_headers,
        )

        assert response.status_code == 404


@pytest.fixture
def created_user(client, admin_auth_headers):
    """Create a user for testing."""
    response = client.post(
        "/api/v1/users",
        headers=admin_auth_headers,
        data=json.dumps({
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
        }),
        content_type="application/json",
    )
    return json.loads(response.data)
```

---

## Concurrency Patterns

### Thread Pool for CPU-Bound Tasks

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, TypeVar
import logging

T = TypeVar("T")
logger = logging.getLogger(__name__)


class TaskExecutor:
    """Execute tasks in parallel using thread pool."""

    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def execute_all(
        self,
        tasks: List[Callable[[], T]],
        timeout: float = None,
    ) -> List[T]:
        """Execute all tasks and return results."""
        futures = [self._executor.submit(task) for task in tasks]
        results = []

        for future in as_completed(futures, timeout=timeout):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Task failed: {e}")

        return results

    def map(
        self,
        func: Callable[[T], U],
        items: List[T],
        timeout: float = None,
    ) -> List[U]:
        """Apply function to items in parallel."""
        return list(self._executor.map(func, items, timeout=timeout))

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown executor."""
        self._executor.shutdown(wait=wait)


# Usage
executor = TaskExecutor(max_workers=4)

# Process items in parallel
def process_item(item):
    # CPU-bound processing
    return transformed_item

results = executor.map(process_item, items)
```

### Async Pattern with asyncio

```python
import asyncio
from typing import List, Callable, TypeVar
import aiohttp
import aioredis

T = TypeVar("T")


class AsyncService:
    """Service with async operations."""

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._redis = None
        self._http_session = None

    async def __aenter__(self):
        self._redis = await aioredis.from_url(self._redis_url)
        self._http_session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._redis.close()
        await self._http_session.close()

    async def fetch_multiple(self, urls: List[str]) -> List[dict]:
        """Fetch multiple URLs concurrently."""
        tasks = [self._fetch_url(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _fetch_url(self, url: str) -> dict:
        """Fetch single URL."""
        async with self._http_session.get(url) as response:
            return await response.json()

    async def get_cached(self, key: str) -> Optional[str]:
        """Get value from Redis cache."""
        return await self._redis.get(key)

    async def set_cached(self, key: str, value: str, ttl: int = 3600) -> None:
        """Set value in Redis cache."""
        await self._redis.setex(key, ttl, value)


# Usage
async def main():
    async with AsyncService("redis://localhost:6379") as service:
        urls = ["https://api.example.com/1", "https://api.example.com/2"]
        results = await service.fetch_multiple(urls)
        print(results)


asyncio.run(main())
```
