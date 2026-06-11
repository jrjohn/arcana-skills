# Python Developer Skill - Code Examples

## Table of Contents
1. [User Authentication Feature](#user-authentication-feature)
2. [CRUD with REST and gRPC](#crud-with-rest-and-grpc)
3. [Background Task Processing](#background-task-processing)
4. [File Upload Service](#file-upload-service)
5. [Event-Driven Architecture](#event-driven-architecture)

---

## User Authentication Feature

### Domain Layer

```python
# app/model/auth.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.model.base import BaseModel


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600


class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="refresh_tokens")

    def is_valid(self) -> bool:
        return not self.revoked and self.expires_at > datetime.utcnow()


# app/dto/auth_dto.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class LoginDTO:
    email: str
    password: str


@dataclass
class RegisterDTO:
    name: str
    email: str
    password: str


@dataclass
class ChangePasswordDTO:
    current_password: str
    new_password: str


@dataclass
class RefreshTokenDTO:
    refresh_token: str
```

### Service Layer

```python
# app/service/auth_service.py
from typing import Optional
from datetime import datetime, timedelta
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash
from app.model.user import User, UserStatus
from app.model.auth import RefreshToken, TokenPair
from app.repository.user_repository import UserRepository
from app.repository.refresh_token_repository import RefreshTokenRepository
from app.dto.auth_dto import LoginDTO, RegisterDTO, ChangePasswordDTO, RefreshTokenDTO
from app.middleware.auth import JWTAuth
from app.util.events import EventPublisher


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: RefreshTokenRepository,
        jwt_auth: JWTAuth,
        event_publisher: EventPublisher,
    ):
        self._user_repo = user_repository
        self._token_repo = token_repository
        self._jwt_auth = jwt_auth
        self._events = event_publisher
        self._refresh_token_expiry = timedelta(days=7)

    def login(self, dto: LoginDTO) -> TokenPair:
        """Authenticate user and return token pair."""
        user = self._user_repo.find_by_email(dto.email)

        if not user:
            raise AuthenticationError("Invalid email or password")

        if not check_password_hash(user.password_hash, dto.password):
            self._events.publish("auth.login_failed", {"email": dto.email})
            raise AuthenticationError("Invalid email or password")

        if user.status != UserStatus.ACTIVE:
            raise AuthenticationError(f"Account is {user.status.value}")

        # Generate tokens
        roles = [role.name for role in user.roles]
        access_token = self._jwt_auth.create_access_token(user.id, roles)
        refresh_token = self._create_refresh_token(user.id)

        # Update last login
        user.last_login_at = datetime.utcnow()
        self._user_repo.save(user)

        self._events.publish("auth.login_success", {"user_id": user.id})

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token.token,
            expires_in=self._jwt_auth._access_token_expiry,
        )

    def register(self, dto: RegisterDTO) -> User:
        """Register new user."""
        # Check if email exists
        if self._user_repo.exists_by_email(dto.email):
            raise ValueError("Email already registered")

        # Validate password strength
        self._validate_password(dto.password)

        # Create user
        user = User(
            id=str(uuid4()),
            name=dto.name,
            email=dto.email,
            password_hash=generate_password_hash(dto.password),
            status=UserStatus.ACTIVE,
        )

        user = self._user_repo.save(user)

        self._events.publish("auth.user_registered", {"user_id": user.id})

        return user

    def refresh_token(self, dto: RefreshTokenDTO) -> TokenPair:
        """Refresh access token using refresh token."""
        stored_token = self._token_repo.find_by_token(dto.refresh_token)

        if not stored_token or not stored_token.is_valid():
            raise AuthenticationError("Invalid or expired refresh token")

        user = stored_token.user

        # Revoke old refresh token
        stored_token.revoked = True
        stored_token.revoked_at = datetime.utcnow()
        self._token_repo.save(stored_token)

        # Generate new tokens
        roles = [role.name for role in user.roles]
        access_token = self._jwt_auth.create_access_token(user.id, roles)
        new_refresh_token = self._create_refresh_token(user.id)

        return TokenPair(
            access_token=access_token,
            refresh_token=new_refresh_token.token,
            expires_in=self._jwt_auth._access_token_expiry,
        )

    def logout(self, refresh_token: str) -> None:
        """Revoke refresh token."""
        stored_token = self._token_repo.find_by_token(refresh_token)
        if stored_token:
            stored_token.revoked = True
            stored_token.revoked_at = datetime.utcnow()
            self._token_repo.save(stored_token)

    def logout_all(self, user_id: str) -> None:
        """Revoke all refresh tokens for user."""
        self._token_repo.revoke_all_by_user(user_id)

    def change_password(self, user_id: str, dto: ChangePasswordDTO) -> None:
        """Change user password."""
        user = self._user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if not check_password_hash(user.password_hash, dto.current_password):
            raise AuthenticationError("Current password is incorrect")

        self._validate_password(dto.new_password)

        user.password_hash = generate_password_hash(dto.new_password)
        self._user_repo.save(user)

        # Revoke all refresh tokens
        self._token_repo.revoke_all_by_user(user_id)

        self._events.publish("auth.password_changed", {"user_id": user_id})

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token."""
        return self._jwt_auth.verify_token(token)

    def _create_refresh_token(self, user_id: str) -> RefreshToken:
        """Create and store refresh token."""
        token = RefreshToken(
            id=str(uuid4()),
            token=self._jwt_auth.create_refresh_token(user_id),
            user_id=user_id,
            expires_at=datetime.utcnow() + self._refresh_token_expiry,
        )
        return self._token_repo.save(token)

    def _validate_password(self, password: str) -> None:
        """Validate password strength."""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain a number")


class AuthenticationError(Exception):
    """Authentication error."""
    pass
```

### Controller Layer

```python
# app/controller/auth_controller.py
from flask import Blueprint, request, jsonify, g
from marshmallow import Schema, fields, validate, post_load, ValidationError
from app.dto.auth_dto import LoginDTO, RegisterDTO, ChangePasswordDTO, RefreshTokenDTO
from app.middleware.auth import jwt_required
from app.service.auth_service import AuthenticationError

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

    @post_load
    def make_dto(self, data, **kwargs):
        return LoginDTO(**data)


class RegisterSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8),
        load_only=True,
    )

    @post_load
    def make_dto(self, data, **kwargs):
        return RegisterDTO(**data)


class RefreshTokenSchema(Schema):
    refresh_token = fields.Str(required=True)

    @post_load
    def make_dto(self, data, **kwargs):
        return RefreshTokenDTO(**data)


class ChangePasswordSchema(Schema):
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8))

    @post_load
    def make_dto(self, data, **kwargs):
        return ChangePasswordDTO(**data)


@auth_bp.route("/login", methods=["POST"])
def login():
    """User login endpoint."""
    schema = LoginSchema()

    try:
        dto = schema.load(request.json)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    try:
        token_pair = g.auth_service.login(dto)
        return jsonify({
            "access_token": token_pair.access_token,
            "refresh_token": token_pair.refresh_token,
            "token_type": token_pair.token_type,
            "expires_in": token_pair.expires_in,
        })
    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401


@auth_bp.route("/register", methods=["POST"])
def register():
    """User registration endpoint."""
    schema = RegisterSchema()

    try:
        dto = schema.load(request.json)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    try:
        user = g.auth_service.register(dto)
        return jsonify({
            "id": user.id,
            "name": user.name,
            "email": user.email,
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """Refresh access token endpoint."""
    schema = RefreshTokenSchema()

    try:
        dto = schema.load(request.json)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    try:
        token_pair = g.auth_service.refresh_token(dto)
        return jsonify({
            "access_token": token_pair.access_token,
            "refresh_token": token_pair.refresh_token,
            "token_type": token_pair.token_type,
            "expires_in": token_pair.expires_in,
        })
    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Logout endpoint."""
    schema = RefreshTokenSchema()

    try:
        dto = schema.load(request.json)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    g.auth_service.logout(dto.refresh_token)
    return "", 204


@auth_bp.route("/logout-all", methods=["POST"])
@jwt_required
def logout_all():
    """Logout from all devices endpoint."""
    g.auth_service.logout_all(g.current_user_id)
    return "", 204


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required
def change_password():
    """Change password endpoint."""
    schema = ChangePasswordSchema()

    try:
        dto = schema.load(request.json)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    try:
        g.auth_service.change_password(g.current_user_id, dto)
        return "", 204
    except (ValueError, AuthenticationError) as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/me", methods=["GET"])
@jwt_required
def get_current_user():
    """Get current user endpoint."""
    user = g.user_service.get_user(g.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict())
```

---

## CRUD with REST and gRPC

### Product Service

```python
# app/model/product.py
from enum import Enum
from decimal import Decimal
from sqlalchemy import Column, String, Text, Numeric, Integer, Enum as SQLEnum
from app.model.base import BaseModel


class ProductStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Product(BaseModel):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    category = Column(String(100), index=True)
    status = Column(SQLEnum(ProductStatus), default=ProductStatus.DRAFT)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "stock": self.stock,
            "category": self.category,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# app/dto/product_dto.py
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal


@dataclass
class CreateProductDTO:
    name: str
    description: Optional[str] = None
    price: Decimal = Decimal("0.00")
    stock: int = 0
    category: Optional[str] = None


@dataclass
class UpdateProductDTO:
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    status: Optional[str] = None


# app/service/product_service.py
from typing import Optional, List, Tuple
from uuid import uuid4
from decimal import Decimal
from app.model.product import Product, ProductStatus
from app.repository.product_repository import ProductRepository
from app.repository.cache_repository import CacheRepository
from app.dto.product_dto import CreateProductDTO, UpdateProductDTO
from app.util.events import EventPublisher


class ProductService:
    CACHE_PREFIX = "product:"
    CACHE_TTL = 3600  # 1 hour

    def __init__(
        self,
        repository: ProductRepository,
        cache: CacheRepository,
        event_publisher: EventPublisher,
    ):
        self._repo = repository
        self._cache = cache
        self._events = event_publisher

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get product by ID with caching."""
        cache_key = f"{self.CACHE_PREFIX}{product_id}"

        # Try cache first
        cached = self._cache.get(cache_key)
        if cached:
            return self._dict_to_product(cached)

        # Load from database
        product = self._repo.find_by_id(product_id)
        if product:
            self._cache.set(cache_key, product.to_dict(), self.CACHE_TTL)

        return product

    def get_products(
        self,
        page: int = 0,
        size: int = 10,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[Product], int]:
        """Get products with pagination and filters."""
        filters = {}
        if category:
            filters["category"] = category
        if status:
            filters["status"] = ProductStatus(status)

        return self._repo.find_all(page=page, size=size, **filters)

    def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 20,
    ) -> List[Product]:
        """Search products."""
        return self._repo.search(
            query=query,
            category=category,
            min_price=min_price,
            max_price=max_price,
            limit=limit,
        )

    def create_product(self, dto: CreateProductDTO) -> Product:
        """Create new product."""
        product = Product(
            id=str(uuid4()),
            name=dto.name,
            description=dto.description,
            price=dto.price,
            stock=dto.stock,
            category=dto.category,
            status=ProductStatus.DRAFT,
        )

        product = self._repo.save(product)

        self._events.publish("product.created", {"product_id": product.id})

        return product

    def update_product(self, product_id: str, dto: UpdateProductDTO) -> Optional[Product]:
        """Update product."""
        product = self._repo.find_by_id(product_id)
        if not product:
            return None

        if dto.name is not None:
            product.name = dto.name
        if dto.description is not None:
            product.description = dto.description
        if dto.price is not None:
            product.price = dto.price
        if dto.stock is not None:
            product.stock = dto.stock
        if dto.category is not None:
            product.category = dto.category
        if dto.status is not None:
            product.status = ProductStatus(dto.status)

        product = self._repo.save(product)

        # Invalidate cache
        self._cache.delete(f"{self.CACHE_PREFIX}{product_id}")

        self._events.publish("product.updated", {"product_id": product.id})

        return product

    def update_stock(self, product_id: str, quantity_change: int) -> Product:
        """Update product stock."""
        product = self._repo.find_by_id(product_id)
        if not product:
            raise ValueError("Product not found")

        new_stock = product.stock + quantity_change
        if new_stock < 0:
            raise ValueError(f"Insufficient stock. Available: {product.stock}")

        product.stock = new_stock
        product = self._repo.save(product)

        # Invalidate cache
        self._cache.delete(f"{self.CACHE_PREFIX}{product_id}")

        if new_stock == 0:
            self._events.publish("product.out_of_stock", {"product_id": product_id})
        elif new_stock <= 10:
            self._events.publish("product.low_stock", {
                "product_id": product_id,
                "stock": new_stock,
            })

        return product

    def delete_product(self, product_id: str) -> bool:
        """Delete product."""
        product = self._repo.find_by_id(product_id)
        if not product:
            return False

        self._repo.delete(product)

        # Invalidate cache
        self._cache.delete(f"{self.CACHE_PREFIX}{product_id}")

        self._events.publish("product.deleted", {"product_id": product_id})

        return True

    def _dict_to_product(self, data: dict) -> Product:
        """Convert dict back to Product object."""
        product = Product(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            price=Decimal(str(data["price"])),
            stock=data["stock"],
            category=data.get("category"),
            status=ProductStatus(data["status"]),
        )
        return product
```

### REST Controller

```python
# app/controller/product_controller.py
from flask import Blueprint, request, jsonify, g
from marshmallow import Schema, fields, validate, post_load, ValidationError
from app.dto.product_dto import CreateProductDTO, UpdateProductDTO
from app.middleware.auth import jwt_required, role_required

product_bp = Blueprint("products", __name__, url_prefix="/api/v1/products")


class CreateProductSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str()
    price = fields.Decimal(required=True, places=2)
    stock = fields.Int(load_default=0, validate=validate.Range(min=0))
    category = fields.Str(validate=validate.Length(max=100))

    @post_load
    def make_dto(self, data, **kwargs):
        return CreateProductDTO(**data)


class UpdateProductSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str()
    price = fields.Decimal(places=2)
    stock = fields.Int(validate=validate.Range(min=0))
    category = fields.Str(validate=validate.Length(max=100))
    status = fields.Str(validate=validate.OneOf(["draft", "active", "inactive", "archived"]))

    @post_load
    def make_dto(self, data, **kwargs):
        return UpdateProductDTO(**data)


class StockUpdateSchema(Schema):
    quantity_change = fields.Int(required=True)


@product_bp.route("", methods=["GET"])
def list_products():
    """List products with pagination."""
    page = request.args.get("page", 0, type=int)
    size = request.args.get("size", 10, type=int)
    category = request.args.get("category")
    status = request.args.get("status")

    products, total = g.product_service.get_products(
        page=page,
        size=size,
        category=category,
        status=status,
    )

    return jsonify({
        "data": [p.to_dict() for p in products],
        "page": page,
        "size": size,
        "total": total,
    })


@product_bp.route("/search", methods=["GET"])
def search_products():
    """Search products."""
    query = request.args.get("q", "")
    category = request.args.get("category")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    limit = request.args.get("limit", 20, type=int)

    products = g.product_service.search_products(
        query=query,
        category=category,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
    )

    return jsonify([p.to_dict() for p in products])


@product_bp.route("/<product_id>", methods=["GET"])
def get_product(product_id: str):
    """Get product by ID."""
    product = g.product_service.get_product(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product.to_dict())


@product_bp.route("", methods=["POST"])
@role_required("admin")
def create_product():
    """Create new product."""
    schema = CreateProductSchema()

    try:
        dto = schema.load(request.json)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    product = g.product_service.create_product(dto)
    return jsonify(product.to_dict()), 201


@product_bp.route("/<product_id>", methods=["PUT"])
@role_required("admin")
def update_product(product_id: str):
    """Update product."""
    schema = UpdateProductSchema()

    try:
        dto = schema.load(request.json)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    product = g.product_service.update_product(product_id, dto)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product.to_dict())


@product_bp.route("/<product_id>/stock", methods=["PATCH"])
@role_required("admin")
def update_stock(product_id: str):
    """Update product stock."""
    schema = StockUpdateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    try:
        product = g.product_service.update_stock(product_id, data["quantity_change"])
        return jsonify(product.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@product_bp.route("/<product_id>", methods=["DELETE"])
@role_required("admin")
def delete_product(product_id: str):
    """Delete product."""
    if g.product_service.delete_product(product_id):
        return "", 204
    return jsonify({"error": "Product not found"}), 404
```

### gRPC Servicer

```python
# app/grpc/product_servicer.py
import grpc
from decimal import Decimal
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.empty_pb2 import Empty
from app.grpc.protos import product_pb2, product_pb2_grpc
from app.service.product_service import ProductService
from app.dto.product_dto import CreateProductDTO, UpdateProductDTO


class ProductServicer(product_pb2_grpc.ProductServiceServicer):
    def __init__(self, product_service: ProductService):
        self._service = product_service

    def GetProduct(self, request, context):
        product = self._service.get_product(request.id)

        if not product:
            context.abort(grpc.StatusCode.NOT_FOUND, "Product not found")
            return product_pb2.ProductResponse()

        return self._to_proto(product)

    def ListProducts(self, request, context):
        products, total = self._service.get_products(
            page=request.page,
            size=request.size,
            category=request.category if request.HasField("category") else None,
            status=request.status if request.HasField("status") else None,
        )

        return product_pb2.ListProductsResponse(
            products=[self._to_proto(p) for p in products],
            total=total,
            page=request.page,
            size=request.size,
            has_next=len(products) == request.size,
        )

    def SearchProducts(self, request, context):
        """Server streaming - returns products one by one."""
        products = self._service.search_products(
            query=request.query,
            category=request.category if request.HasField("category") else None,
            min_price=request.min_price if request.HasField("min_price") else None,
            max_price=request.max_price if request.HasField("max_price") else None,
            limit=request.limit,
        )

        for product in products:
            if context.is_active():
                yield self._to_proto(product)
            else:
                break

    def CreateProduct(self, request, context):
        try:
            dto = CreateProductDTO(
                name=request.name,
                description=request.description,
                price=Decimal(str(request.price)),
                stock=request.stock,
                category=request.category,
            )
            product = self._service.create_product(dto)
            return self._to_proto(product)

        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
            return product_pb2.ProductResponse()

    def UpdateProduct(self, request, context):
        dto = UpdateProductDTO(
            name=request.name if request.HasField("name") else None,
            description=request.description if request.HasField("description") else None,
            price=Decimal(str(request.price)) if request.HasField("price") else None,
            stock=request.stock if request.HasField("stock") else None,
            category=request.category if request.HasField("category") else None,
            status=request.status if request.HasField("status") else None,
        )

        product = self._service.update_product(request.id, dto)
        if not product:
            context.abort(grpc.StatusCode.NOT_FOUND, "Product not found")
            return product_pb2.ProductResponse()

        return self._to_proto(product)

    def UpdateStock(self, request, context):
        try:
            product = self._service.update_stock(request.product_id, request.quantity_change)
            return self._to_proto(product)
        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
            return product_pb2.ProductResponse()

    def BatchUpdateStock(self, request_iterator, context):
        """Client streaming - batch stock updates."""
        success_count = 0
        failure_count = 0
        errors = []

        for request in request_iterator:
            try:
                self._service.update_stock(request.product_id, request.quantity_change)
                success_count += 1
            except Exception as e:
                failure_count += 1
                errors.append(product_pb2.StockUpdateError(
                    product_id=request.product_id,
                    error_message=str(e),
                ))

        return product_pb2.BatchStockUpdateResponse(
            success_count=success_count,
            failure_count=failure_count,
            errors=errors,
        )

    def DeleteProduct(self, request, context):
        if self._service.delete_product(request.id):
            return Empty()

        context.abort(grpc.StatusCode.NOT_FOUND, "Product not found")
        return Empty()

    def _to_proto(self, product) -> product_pb2.ProductResponse:
        created_at = Timestamp()
        created_at.FromDatetime(product.created_at)

        updated_at = Timestamp()
        updated_at.FromDatetime(product.updated_at)

        return product_pb2.ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description or "",
            price=float(product.price),
            stock=product.stock,
            category=product.category or "",
            status=product.status.value,
            created_at=created_at,
            updated_at=updated_at,
        )
```

---

## Background Task Processing

### Celery Task Queue

```python
# app/tasks/__init__.py
from celery import Celery


def create_celery(app=None):
    celery = Celery(
        "arcana",
        broker="redis://localhost:6379/0",
        backend="redis://localhost:6379/1",
        include=["app.tasks.email_tasks", "app.tasks.sync_tasks"],
    )

    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,
        worker_prefetch_multiplier=4,
    )

    if app:
        celery.conf.update(app.config)

        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask

    return celery


celery = create_celery()


# app/tasks/email_tasks.py
from app.tasks import celery
from app.util.email import EmailClient
import logging

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_id: str, email: str, name: str):
    """Send welcome email to new user."""
    try:
        client = EmailClient()
        client.send(
            to=email,
            subject="Welcome to Arcana!",
            template="welcome",
            context={"name": name},
        )
        logger.info(f"Welcome email sent to {email}")

    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {e}")
        raise self.retry(exc=e)


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email(self, email: str, reset_token: str):
    """Send password reset email."""
    try:
        client = EmailClient()
        reset_url = f"https://arcana.com/reset-password?token={reset_token}"

        client.send(
            to=email,
            subject="Password Reset Request",
            template="password_reset",
            context={"reset_url": reset_url},
        )
        logger.info(f"Password reset email sent to {email}")

    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {e}")
        raise self.retry(exc=e)


@celery.task
def send_bulk_email(user_ids: list, subject: str, template: str, context: dict):
    """Send bulk email to multiple users."""
    from app.service.user_service import UserService
    from app.container import Container

    container = Container()
    user_service = container.user_service()

    for user_id in user_ids:
        user = user_service.get_user(user_id)
        if user and user.email:
            send_email.delay(user.email, subject, template, {**context, "name": user.name})


@celery.task(bind=True, max_retries=3)
def send_email(self, to: str, subject: str, template: str, context: dict):
    """Generic send email task."""
    try:
        client = EmailClient()
        client.send(to=to, subject=subject, template=template, context=context)

    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        raise self.retry(exc=e)


# app/tasks/sync_tasks.py
from app.tasks import celery
from app.model.user import SyncStatus
import logging

logger = logging.getLogger(__name__)


@celery.task
def sync_pending_users():
    """Sync users with pending status to external system."""
    from app.container import Container

    container = Container()
    user_repo = container.user_repository()
    external_api = container.external_api_client()

    pending_users = user_repo.find_pending_sync()
    logger.info(f"Syncing {len(pending_users)} pending users")

    for user in pending_users:
        try:
            external_api.sync_user(user)
            user.sync_status = SyncStatus.SYNCED
            user_repo.save(user)
            logger.info(f"User {user.id} synced successfully")

        except Exception as e:
            user.sync_status = SyncStatus.FAILED
            user_repo.save(user)
            logger.error(f"Failed to sync user {user.id}: {e}")


@celery.task
def cleanup_expired_tokens():
    """Clean up expired refresh tokens."""
    from datetime import datetime
    from app.container import Container

    container = Container()
    token_repo = container.refresh_token_repository()

    deleted_count = token_repo.delete_expired(datetime.utcnow())
    logger.info(f"Cleaned up {deleted_count} expired tokens")


@celery.task
def generate_daily_report():
    """Generate daily analytics report."""
    from datetime import date, timedelta
    from app.container import Container

    container = Container()
    analytics_service = container.analytics_service()

    yesterday = date.today() - timedelta(days=1)
    report = analytics_service.generate_report(yesterday)

    # Save or send report
    logger.info(f"Generated daily report for {yesterday}")


# Celery Beat Schedule
celery.conf.beat_schedule = {
    "sync-pending-users": {
        "task": "app.tasks.sync_tasks.sync_pending_users",
        "schedule": 300.0,  # Every 5 minutes
    },
    "cleanup-expired-tokens": {
        "task": "app.tasks.sync_tasks.cleanup_expired_tokens",
        "schedule": 3600.0,  # Every hour
    },
    "generate-daily-report": {
        "task": "app.tasks.sync_tasks.generate_daily_report",
        "schedule": {
            "hour": 2,
            "minute": 0,
        },  # Daily at 2 AM
    },
}
```

---

## File Upload Service

```python
# app/service/file_service.py
import os
import hashlib
from uuid import uuid4
from datetime import datetime
from typing import Optional, BinaryIO
from werkzeug.utils import secure_filename
from app.model.file import File, FileStatus
from app.repository.file_repository import FileRepository
from app.util.storage import StorageBackend
from app.util.events import EventPublisher


class FileService:
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "doc", "docx", "xls", "xlsx"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(
        self,
        repository: FileRepository,
        storage: StorageBackend,
        event_publisher: EventPublisher,
    ):
        self._repo = repository
        self._storage = storage
        self._events = event_publisher

    def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: str,
        user_id: str,
    ) -> File:
        """Upload a file."""
        # Validate file
        self._validate_file(filename, file_data)

        # Generate unique filename
        ext = self._get_extension(filename)
        safe_filename = secure_filename(filename)
        unique_filename = f"{uuid4()}.{ext}"

        # Calculate checksum
        file_data.seek(0)
        checksum = hashlib.md5(file_data.read()).hexdigest()
        file_data.seek(0)

        # Get file size
        file_data.seek(0, 2)
        file_size = file_data.tell()
        file_data.seek(0)

        # Generate storage path
        now = datetime.utcnow()
        storage_path = f"{now.year}/{now.month:02d}/{now.day:02d}/{unique_filename}"

        # Upload to storage
        url = self._storage.upload(storage_path, file_data, content_type)

        # Create file record
        file = File(
            id=str(uuid4()),
            original_filename=safe_filename,
            storage_path=storage_path,
            url=url,
            content_type=content_type,
            file_size=file_size,
            checksum=checksum,
            uploaded_by=user_id,
            status=FileStatus.ACTIVE,
        )

        file = self._repo.save(file)

        self._events.publish("file.uploaded", {
            "file_id": file.id,
            "user_id": user_id,
        })

        return file

    def get_file(self, file_id: str) -> Optional[File]:
        """Get file by ID."""
        return self._repo.find_by_id(file_id)

    def delete_file(self, file_id: str, user_id: str) -> bool:
        """Delete file."""
        file = self._repo.find_by_id(file_id)
        if not file:
            return False

        # Check permission
        if file.uploaded_by != user_id:
            raise PermissionError("Not authorized to delete this file")

        # Delete from storage
        self._storage.delete(file.storage_path)

        # Soft delete record
        file.status = FileStatus.DELETED
        self._repo.save(file)

        self._events.publish("file.deleted", {
            "file_id": file_id,
            "user_id": user_id,
        })

        return True

    def get_download_url(self, file_id: str, expires_in: int = 3600) -> Optional[str]:
        """Get presigned download URL."""
        file = self._repo.find_by_id(file_id)
        if not file or file.status != FileStatus.ACTIVE:
            return None

        return self._storage.get_presigned_url(file.storage_path, expires_in)

    def _validate_file(self, filename: str, file_data: BinaryIO) -> None:
        """Validate file before upload."""
        ext = self._get_extension(filename)
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"File type not allowed: {ext}")

        file_data.seek(0, 2)
        size = file_data.tell()
        file_data.seek(0)

        if size > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large. Max size: {self.MAX_FILE_SIZE} bytes")

    def _get_extension(self, filename: str) -> str:
        """Get file extension."""
        if "." not in filename:
            return ""
        return filename.rsplit(".", 1)[1].lower()


# app/controller/file_controller.py
from flask import Blueprint, request, jsonify, g, send_file
from app.middleware.auth import jwt_required

file_bp = Blueprint("files", __name__, url_prefix="/api/v1/files")


@file_bp.route("", methods=["POST"])
@jwt_required
def upload_file():
    """Upload file endpoint."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        result = g.file_service.upload_file(
            file_data=file.stream,
            filename=file.filename,
            content_type=file.content_type,
            user_id=g.current_user_id,
        )

        return jsonify({
            "id": result.id,
            "filename": result.original_filename,
            "url": result.url,
            "size": result.file_size,
            "content_type": result.content_type,
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@file_bp.route("/<file_id>", methods=["GET"])
@jwt_required
def get_file(file_id: str):
    """Get file info endpoint."""
    file = g.file_service.get_file(file_id)
    if not file:
        return jsonify({"error": "File not found"}), 404

    return jsonify({
        "id": file.id,
        "filename": file.original_filename,
        "url": file.url,
        "size": file.file_size,
        "content_type": file.content_type,
        "uploaded_at": file.created_at.isoformat(),
    })


@file_bp.route("/<file_id>/download", methods=["GET"])
@jwt_required
def download_file(file_id: str):
    """Get download URL endpoint."""
    url = g.file_service.get_download_url(file_id)
    if not url:
        return jsonify({"error": "File not found"}), 404

    return jsonify({"download_url": url})


@file_bp.route("/<file_id>", methods=["DELETE"])
@jwt_required
def delete_file(file_id: str):
    """Delete file endpoint."""
    try:
        if g.file_service.delete_file(file_id, g.current_user_id):
            return "", 204
        return jsonify({"error": "File not found"}), 404

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
```

---

## Event-Driven Architecture

```python
# app/util/events.py
from typing import Callable, Dict, List, Any
from datetime import datetime
from uuid import uuid4
import json
import logging
import redis
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Event:
    id: str
    type: str
    data: Dict[str, Any]
    timestamp: str
    source: str = "arcana-python"

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        data = json.loads(json_str)
        return cls(**data)


class EventPublisher:
    """Event publisher using Redis pub/sub."""

    def __init__(self, redis_client: redis.Redis, channel_prefix: str = "events:"):
        self._redis = redis_client
        self._channel_prefix = channel_prefix
        self._local_handlers: Dict[str, List[Callable]] = {}

    def publish(self, event_type: str, data: Dict[str, Any]) -> str:
        """Publish event to Redis and local handlers."""
        event = Event(
            id=str(uuid4()),
            type=event_type,
            data=data,
            timestamp=datetime.utcnow().isoformat(),
        )

        # Publish to Redis
        channel = f"{self._channel_prefix}{event_type}"
        self._redis.publish(channel, event.to_json())

        logger.info(f"Published event: {event_type} ({event.id})")

        # Call local handlers
        self._call_local_handlers(event)

        return event.id

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe to event type with local handler."""
        if event_type not in self._local_handlers:
            self._local_handlers[event_type] = []
        self._local_handlers[event_type].append(handler)

    def _call_local_handlers(self, event: Event) -> None:
        """Call local handlers for event."""
        handlers = self._local_handlers.get(event.type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error for {event.type}: {e}")


class EventConsumer:
    """Event consumer for processing events from Redis."""

    def __init__(
        self,
        redis_client: redis.Redis,
        channel_prefix: str = "events:",
        group: str = "arcana-consumers",
    ):
        self._redis = redis_client
        self._channel_prefix = channel_prefix
        self._group = group
        self._handlers: Dict[str, Callable[[Event], None]] = {}
        self._running = False

    def register(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Register handler for event type."""
        self._handlers[event_type] = handler

    def start(self) -> None:
        """Start consuming events."""
        self._running = True
        pubsub = self._redis.pubsub()

        # Subscribe to all registered event types
        channels = [f"{self._channel_prefix}{et}" for et in self._handlers.keys()]
        pubsub.subscribe(*channels)

        logger.info(f"Started consuming events from: {channels}")

        for message in pubsub.listen():
            if not self._running:
                break

            if message["type"] == "message":
                self._process_message(message)

    def stop(self) -> None:
        """Stop consuming events."""
        self._running = False

    def _process_message(self, message: dict) -> None:
        """Process received message."""
        try:
            event = Event.from_json(message["data"].decode())
            handler = self._handlers.get(event.type)

            if handler:
                logger.info(f"Processing event: {event.type} ({event.id})")
                handler(event)

        except Exception as e:
            logger.error(f"Error processing event: {e}")


# Event handlers
# app/events/handlers.py
from app.util.events import Event
from app.tasks.email_tasks import send_welcome_email, send_password_reset_email
import logging

logger = logging.getLogger(__name__)


def handle_user_registered(event: Event) -> None:
    """Handle user registration event."""
    user_id = event.data.get("user_id")
    email = event.data.get("email")
    name = event.data.get("name")

    if user_id and email and name:
        send_welcome_email.delay(user_id, email, name)
        logger.info(f"Queued welcome email for user {user_id}")


def handle_password_reset_requested(event: Event) -> None:
    """Handle password reset request event."""
    email = event.data.get("email")
    reset_token = event.data.get("reset_token")

    if email and reset_token:
        send_password_reset_email.delay(email, reset_token)
        logger.info(f"Queued password reset email for {email}")


def handle_order_created(event: Event) -> None:
    """Handle order creation event."""
    order_id = event.data.get("order_id")
    user_id = event.data.get("user_id")

    logger.info(f"Order created: {order_id} by user {user_id}")
    # Process order...


def handle_product_out_of_stock(event: Event) -> None:
    """Handle product out of stock event."""
    product_id = event.data.get("product_id")

    logger.warning(f"Product out of stock: {product_id}")
    # Notify admin, update status...


# Register handlers
def register_event_handlers(consumer: EventConsumer) -> None:
    """Register all event handlers."""
    consumer.register("auth.user_registered", handle_user_registered)
    consumer.register("auth.password_reset_requested", handle_password_reset_requested)
    consumer.register("order.created", handle_order_created)
    consumer.register("product.out_of_stock", handle_product_out_of_stock)
```
