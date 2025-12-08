# Service Layer Patterns

Deep dive into service layer patterns for Node.js enterprise applications.

---

## Core Principles

1. **Single Responsibility**: Each service handles one domain
2. **Dependency Injection**: Use InversifyJS for IoC
3. **Interface Segregation**: Define clear interfaces
4. **Pure Business Logic**: No HTTP/gRPC concerns

---

## Service Interface Pattern

```typescript
// Define interface first
export interface IUserService {
    getUser(userId: string): Promise<UserDto | null>;
    getUsers(page: number, size: number): Promise<{ data: UserDto[]; total: number }>;
    createUser(dto: CreateUserDto): Promise<UserDto>;
    updateUser(userId: string, dto: UpdateUserDto): Promise<UserDto | null>;
    deleteUser(userId: string): Promise<boolean>;
}

// Implement with @injectable
@injectable()
export class UserService implements IUserService {
    constructor(
        @inject(TYPES.UserRepository) private readonly repo: UserRepository,
        @inject(TYPES.CacheRepository) private readonly cache: CacheRepository,
        @inject(TYPES.EventPublisher) private readonly events: EventPublisher
    ) {}

    // Implementation...
}
```

---

## Repository Injection Pattern

```typescript
@injectable()
export class OrderService implements IOrderService {
    constructor(
        @inject(TYPES.OrderRepository) private readonly orderRepo: OrderRepository,
        @inject(TYPES.ProductRepository) private readonly productRepo: ProductRepository,
        @inject(TYPES.UserRepository) private readonly userRepo: UserRepository
    ) {}

    async createOrder(userId: string, items: OrderItemDto[]): Promise<Order> {
        // Validate user exists
        const user = await this.userRepo.findById(userId);
        if (!user) {
            throw AppException.notFound("User not found");
        }

        // Validate products and stock
        for (const item of items) {
            const product = await this.productRepo.findById(item.productId);
            if (!product) {
                throw AppException.notFound(`Product not found: ${item.productId}`);
            }
            if (product.stock < item.quantity) {
                throw AppException.validation("Insufficient stock", {
                    productId: item.productId,
                    available: product.stock,
                    requested: item.quantity,
                });
            }
        }

        // Create order
        return this.orderRepo.createWithItems(userId, items);
    }
}
```

---

## Caching Pattern

```typescript
@injectable()
export class ProductService implements IProductService {
    private readonly CACHE_PREFIX = "product:";
    private readonly CACHE_TTL = 3600; // 1 hour

    constructor(
        @inject(TYPES.ProductRepository) private readonly repo: ProductRepository,
        @inject(TYPES.CacheRepository) private readonly cache: CacheRepository
    ) {}

    async getProduct(productId: string): Promise<ProductDto | null> {
        const cacheKey = `${this.CACHE_PREFIX}${productId}`;

        // Try cache first
        const cached = await this.cache.get<ProductDto>(cacheKey);
        if (cached) {
            return cached;
        }

        // Load from database
        const product = await this.repo.findById(productId);
        if (product) {
            const dto = toProductDto(product);
            await this.cache.set(cacheKey, dto, this.CACHE_TTL);
            return dto;
        }

        return null;
    }

    async updateProduct(productId: string, dto: UpdateProductDto): Promise<ProductDto | null> {
        const product = await this.repo.findById(productId);
        if (!product) {
            return null;
        }

        // Update fields...
        const updated = await this.repo.update(product);

        // Invalidate cache
        await this.cache.delete(`${this.CACHE_PREFIX}${productId}`);

        return toProductDto(updated);
    }
}
```

---

## Event Publishing Pattern

```typescript
@injectable()
export class UserService implements IUserService {
    constructor(
        @inject(TYPES.UserRepository) private readonly repo: UserRepository,
        @inject(TYPES.EventPublisher) private readonly events: EventPublisher
    ) {}

    async createUser(dto: CreateUserDto): Promise<UserDto> {
        // Business logic...
        const user = await this.repo.save({
            name: dto.name,
            email: dto.email,
            passwordHash: await bcrypt.hash(dto.password, 10),
            syncStatus: SyncStatus.SYNCED,
        });

        // Publish domain event
        await this.events.publish("user.registered", {
            userId: user.id,
            email: user.email,
            name: user.name,
        });

        return toUserDto(user);
    }

    async changePassword(userId: string, dto: ChangePasswordDto): Promise<void> {
        const user = await this.repo.findById(userId);
        if (!user) {
            throw AppException.notFound("User not found");
        }

        // Validate current password...
        user.passwordHash = await bcrypt.hash(dto.newPassword, 10);
        await this.repo.update(user);

        // Publish security event
        await this.events.publish("user.password_changed", {
            userId,
            timestamp: new Date().toISOString(),
        });
    }
}
```

---

## Transaction Pattern

```typescript
@injectable()
export class OrderService implements IOrderService {
    constructor(
        @inject(TYPES.PrismaClient) private readonly prisma: PrismaClient,
        @inject(TYPES.EventPublisher) private readonly events: EventPublisher
    ) {}

    async createOrder(userId: string, items: OrderItemDto[]): Promise<Order> {
        // Use Prisma transaction
        const order = await this.prisma.$transaction(async (tx) => {
            // Create order
            const order = await tx.order.create({
                data: {
                    userId,
                    status: OrderStatus.PENDING,
                    totalAmount: 0,
                },
            });

            let totalAmount = 0;

            // Create order items and update stock
            for (const item of items) {
                const product = await tx.product.findUnique({
                    where: { id: item.productId },
                });

                if (!product || product.stock < item.quantity) {
                    throw new Error("Insufficient stock");
                }

                await tx.orderItem.create({
                    data: {
                        orderId: order.id,
                        productId: item.productId,
                        quantity: item.quantity,
                        price: product.price,
                    },
                });

                await tx.product.update({
                    where: { id: item.productId },
                    data: { stock: { decrement: item.quantity } },
                });

                totalAmount += product.price * item.quantity;
            }

            // Update order total
            return tx.order.update({
                where: { id: order.id },
                data: { totalAmount },
                include: { items: true },
            });
        });

        // Publish event after successful transaction
        await this.events.publish("order.created", {
            orderId: order.id,
            userId,
            totalAmount: order.totalAmount,
        });

        return order;
    }
}
```

---

## Validation Pattern

```typescript
@injectable()
export class AuthService implements IAuthService {
    async register(dto: RegisterDto): Promise<User> {
        // Business validation (beyond schema validation)
        const existing = await this.userRepo.findByEmail(dto.email);
        if (existing) {
            throw AppException.validation("Email already registered", {
                email: dto.email,
            });
        }

        // Password strength validation
        this.validatePasswordStrength(dto.password);

        // Create user
        return this.userRepo.save({
            name: dto.name,
            email: dto.email,
            passwordHash: await bcrypt.hash(dto.password, 10),
            syncStatus: SyncStatus.SYNCED,
        });
    }

    private validatePasswordStrength(password: string): void {
        const errors: string[] = [];

        if (password.length < 8) {
            errors.push("Password must be at least 8 characters");
        }
        if (!/[A-Z]/.test(password)) {
            errors.push("Password must contain uppercase letter");
        }
        if (!/[a-z]/.test(password)) {
            errors.push("Password must contain lowercase letter");
        }
        if (!/[0-9]/.test(password)) {
            errors.push("Password must contain a number");
        }

        if (errors.length > 0) {
            throw AppException.validation("Password too weak", {
                requirements: errors,
            });
        }
    }
}
```

---

## Error Handling Pattern

```typescript
@injectable()
export class UserService implements IUserService {
    async getUser(userId: string): Promise<UserDto | null> {
        try {
            const user = await this.repo.findById(userId);
            return user ? toUserDto(user) : null;
        } catch (error) {
            // Log error but don't expose internal details
            console.error("Error fetching user:", error);
            throw AppException.internal("Failed to fetch user");
        }
    }

    async updateUser(userId: string, dto: UpdateUserDto): Promise<UserDto> {
        const user = await this.repo.findById(userId);
        if (!user) {
            throw AppException.notFound(`User not found: ${userId}`);
        }

        if (dto.email) {
            const existing = await this.repo.findByEmail(dto.email);
            if (existing && existing.id !== userId) {
                throw AppException.conflict("Email already in use");
            }
        }

        // Update and return
        const updated = await this.repo.update({ ...user, ...dto });
        return toUserDto(updated);
    }
}
```

---

## Testing Service Layer

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { UserService } from "../UserService";
import { createMockUserRepository } from "../../test/mocks";
import { createMockUser } from "../../test/fixtures";

describe("UserService", () => {
    let service: UserService;
    let mockRepo: ReturnType<typeof createMockUserRepository>;
    let mockCache: any;
    let mockEvents: any;

    beforeEach(() => {
        mockRepo = createMockUserRepository();
        mockCache = { get: vi.fn(), set: vi.fn(), delete: vi.fn() };
        mockEvents = { publish: vi.fn() };

        service = new UserService(mockRepo, mockCache, mockEvents);
    });

    describe("getUser", () => {
        it("should return cached user when available", async () => {
            const cachedUser = { id: "123", name: "Cached User" };
            mockCache.get.mockResolvedValue(cachedUser);

            const result = await service.getUser("123");

            expect(result).toEqual(cachedUser);
            expect(mockRepo.findById).not.toHaveBeenCalled();
        });

        it("should fetch from database and cache when not cached", async () => {
            const dbUser = createMockUser({ id: "123" });
            mockCache.get.mockResolvedValue(null);
            mockRepo.findById.mockResolvedValue(dbUser);

            const result = await service.getUser("123");

            expect(result).toBeDefined();
            expect(mockRepo.findById).toHaveBeenCalledWith("123");
            expect(mockCache.set).toHaveBeenCalled();
        });
    });

    describe("createUser", () => {
        it("should create user and publish event", async () => {
            mockRepo.findByEmail.mockResolvedValue(null);
            mockRepo.save.mockImplementation(async (user) => ({
                ...user,
                id: "new-id",
                createdAt: new Date(),
                updatedAt: new Date(),
            }));

            const result = await service.createUser({
                name: "New User",
                email: "new@example.com",
                password: "Password123",
            });

            expect(result.name).toBe("New User");
            expect(mockEvents.publish).toHaveBeenCalledWith(
                "user.registered",
                expect.objectContaining({ userId: "new-id" })
            );
        });

        it("should throw when email exists", async () => {
            mockRepo.findByEmail.mockResolvedValue(createMockUser());

            await expect(
                service.createUser({
                    name: "New User",
                    email: "existing@example.com",
                    password: "Password123",
                })
            ).rejects.toThrow("Email already registered");
        });
    });
});
```
