# Node.js Developer Skill - Design Patterns

## Table of Contents
1. [Architecture Patterns](#architecture-patterns)
2. [Service Layer Patterns](#service-layer-patterns)
3. [Data Access Patterns](#data-access-patterns)
4. [API Design Patterns](#api-design-patterns)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Testing Patterns](#testing-patterns)
7. [Event-Driven Patterns](#event-driven-patterns)

---

## Architecture Patterns

### Clean Architecture Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                         Controllers                              │
│  ┌─────────────────────┐     ┌─────────────────────────────┐   │
│  │   Express Routes    │     │      gRPC Servicers         │   │
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
│  │  Pure TypeScript classes, no framework dependencies         ││
│  └─────────────────────────────────────────────────────────────┘│
│                             │                                    │
│                             ↓                                    │
├─────────────────────────────────────────────────────────────────┤
│                       Repositories                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│
│  │ Prisma       │ │ Redis Cache  │ │ External API Clients     ││
│  │ Repositories │ │ Repository   │ │ (gRPC/REST)              ││
│  └──────────────┘ └──────────────┘ └──────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```typescript
// Controller Layer - HTTP concerns only
router.get("/:userId", jwtRequired, async (req, res, next) => {
    try {
        const user = await userService.getUser(req.params.userId);
        if (!user) {
            return res.status(404).json({ error: "User not found" });
        }
        res.json(user);
    } catch (error) {
        next(error);
    }
});

// Service Layer - Business logic
@injectable()
class UserService implements IUserService {
    constructor(
        @inject(TYPES.UserRepository) private readonly repo: UserRepository,
        @inject(TYPES.CacheRepository) private readonly cache: CacheRepository,
        @inject(TYPES.EventPublisher) private readonly events: EventPublisher
    ) {}

    async getUser(userId: string): Promise<UserDto | null> {
        // Try cache first
        const cached = await this.cache.get(`user:${userId}`);
        if (cached) {
            return JSON.parse(cached);
        }

        // Load from database
        const user = await this.repo.findById(userId);
        if (user) {
            await this.cache.set(`user:${userId}`, JSON.stringify(toUserDto(user)));
        }

        return user ? toUserDto(user) : null;
    }
}

// Repository Layer - Data access
@injectable()
class UserRepositoryImpl implements UserRepository {
    constructor(@inject(TYPES.PrismaClient) private readonly prisma: PrismaClient) {}

    async findByEmail(email: string): Promise<User | null> {
        return this.prisma.user.findUnique({ where: { email } });
    }
}
```

### InversifyJS Dependency Injection Container

```typescript
// src/container/types.ts
export const TYPES = {
    // Infrastructure
    PrismaClient: Symbol.for("PrismaClient"),
    RedisClient: Symbol.for("RedisClient"),

    // Repositories
    UserRepository: Symbol.for("UserRepository"),
    CacheRepository: Symbol.for("CacheRepository"),

    // Services
    UserService: Symbol.for("UserService"),
    AuthService: Symbol.for("AuthService"),

    // Event publishing
    EventPublisher: Symbol.for("EventPublisher"),
};

// src/container/container.ts
import { Container } from "inversify";
import { PrismaClient } from "@prisma/client";
import Redis from "ioredis";

const container = new Container();

// Infrastructure
container.bind<PrismaClient>(TYPES.PrismaClient)
    .toConstantValue(new PrismaClient());

container.bind<Redis>(TYPES.RedisClient)
    .toConstantValue(new Redis(process.env.REDIS_URL));

// Repositories
container.bind<UserRepository>(TYPES.UserRepository)
    .to(UserRepositoryImpl)
    .inSingletonScope();

container.bind<CacheRepository>(TYPES.CacheRepository)
    .to(RedisCacheRepository)
    .inSingletonScope();

// Services
container.bind<IUserService>(TYPES.UserService)
    .to(UserService)
    .inSingletonScope();

container.bind<IAuthService>(TYPES.AuthService)
    .to(AuthService)
    .inSingletonScope();

// Event publishing
container.bind<EventPublisher>(TYPES.EventPublisher)
    .to(RedisEventPublisher)
    .inSingletonScope();

export { container };

// Usage
const userService = container.get<IUserService>(TYPES.UserService);
```

---

## Service Layer Patterns

### Strategy Pattern

```typescript
// Pricing strategy interface
interface PricingStrategy {
    calculate(basePrice: number, quantity: number): number;
}

class RegularPricing implements PricingStrategy {
    calculate(basePrice: number, quantity: number): number {
        return basePrice * quantity;
    }
}

class BulkPricing implements PricingStrategy {
    constructor(
        private readonly threshold: number = 10,
        private readonly discountRate: number = 0.10
    ) {}

    calculate(basePrice: number, quantity: number): number {
        const total = basePrice * quantity;
        if (quantity >= this.threshold) {
            return total * (1 - this.discountRate);
        }
        return total;
    }
}

class PremiumPricing implements PricingStrategy {
    constructor(private readonly discountRate: number = 0.15) {}

    calculate(basePrice: number, quantity: number): number {
        return basePrice * quantity * (1 - this.discountRate);
    }
}

// Strategy factory
class PricingStrategyFactory {
    private static strategies: Record<string, new (...args: any[]) => PricingStrategy> = {
        regular: RegularPricing,
        bulk: BulkPricing,
        premium: PremiumPricing,
    };

    static create(strategyType: string): PricingStrategy {
        const StrategyClass = this.strategies[strategyType];
        if (!StrategyClass) {
            throw new Error(`Unknown strategy: ${strategyType}`);
        }
        return new StrategyClass();
    }
}

// Usage
@injectable()
class OrderService {
    calculateOrderTotal(items: OrderItem[], customerType: string): number {
        const strategy = PricingStrategyFactory.create(customerType);
        return items.reduce(
            (total, item) => total + strategy.calculate(item.price, item.quantity),
            0
        );
    }
}
```

### Command Pattern

```typescript
// Command interface
interface Command<T> {
    execute(): Promise<T>;
}

// Commands
class CreateUserCommand implements Command<User> {
    constructor(
        private readonly dto: CreateUserDto,
        private readonly repository: UserRepository,
        private readonly events: EventPublisher
    ) {}

    async execute(): Promise<User> {
        // Validation
        const existing = await this.repository.findByEmail(this.dto.email);
        if (existing) {
            throw new Error("Email already exists");
        }

        // Create user
        const user = await this.repository.save({
            name: this.dto.name,
            email: this.dto.email,
            passwordHash: await bcrypt.hash(this.dto.password, 10),
            syncStatus: SyncStatus.SYNCED,
        });

        // Publish event
        await this.events.publish("user.created", { userId: user.id });

        return user;
    }
}

class UpdateUserCommand implements Command<User> {
    constructor(
        private readonly userId: string,
        private readonly dto: UpdateUserDto,
        private readonly repository: UserRepository
    ) {}

    async execute(): Promise<User> {
        const user = await this.repository.findById(this.userId);
        if (!user) {
            throw new Error("User not found");
        }

        if (this.dto.name) user.name = this.dto.name;
        if (this.dto.email) user.email = this.dto.email;

        return this.repository.update(user);
    }
}

// Command bus
class CommandBus {
    async dispatch<T>(command: Command<T>): Promise<T> {
        return command.execute();
    }
}

// Usage
const bus = new CommandBus();
const user = await bus.dispatch(new CreateUserCommand(dto, repo, events));
```

### Unit of Work Pattern

```typescript
import { PrismaClient } from "@prisma/client";

class UnitOfWork {
    private committed = false;

    constructor(private readonly prisma: PrismaClient) {}

    async execute<T>(work: (tx: PrismaClient) => Promise<T>): Promise<T> {
        return this.prisma.$transaction(async (tx) => {
            const result = await work(tx as PrismaClient);
            this.committed = true;
            return result;
        });
    }
}

// Usage
@injectable()
class OrderService {
    constructor(
        @inject(TYPES.PrismaClient) private readonly prisma: PrismaClient
    ) {}

    async createOrder(userId: string, items: OrderItemDto[]): Promise<Order> {
        const uow = new UnitOfWork(this.prisma);

        return uow.execute(async (tx) => {
            // Create order
            const order = await tx.order.create({
                data: {
                    userId,
                    status: OrderStatus.PENDING,
                },
            });

            // Add items
            for (const item of items) {
                await tx.orderItem.create({
                    data: {
                        orderId: order.id,
                        productId: item.productId,
                        quantity: item.quantity,
                    },
                });

                // Update inventory
                await tx.product.update({
                    where: { id: item.productId },
                    data: {
                        stock: { decrement: item.quantity },
                    },
                });
            }

            return order;
        });
    }
}
```

---

## Data Access Patterns

### Repository Pattern

```typescript
// Base repository interface
interface Repository<T> {
    findById(id: string): Promise<T | null>;
    findAll(options?: PaginationOptions): Promise<[T[], number]>;
    save(entity: Omit<T, "id" | "createdAt" | "updatedAt">): Promise<T>;
    update(entity: T): Promise<T>;
    delete(entity: T): Promise<void>;
}

interface PaginationOptions {
    page?: number;
    size?: number;
    orderBy?: string;
    order?: "asc" | "desc";
}

// Prisma implementation
@injectable()
class PrismaRepository<T> implements Repository<T> {
    constructor(
        protected readonly prisma: PrismaClient,
        protected readonly modelName: string
    ) {}

    async findById(id: string): Promise<T | null> {
        return (this.prisma as any)[this.modelName].findUnique({
            where: { id },
        });
    }

    async findAll(options: PaginationOptions = {}): Promise<[T[], number]> {
        const { page = 0, size = 10, orderBy = "createdAt", order = "desc" } = options;

        const [items, total] = await Promise.all([
            (this.prisma as any)[this.modelName].findMany({
                skip: page * size,
                take: size,
                orderBy: { [orderBy]: order },
            }),
            (this.prisma as any)[this.modelName].count(),
        ]);

        return [items, total];
    }

    async save(entity: Omit<T, "id" | "createdAt" | "updatedAt">): Promise<T> {
        return (this.prisma as any)[this.modelName].create({
            data: entity,
        });
    }

    async update(entity: T): Promise<T> {
        return (this.prisma as any)[this.modelName].update({
            where: { id: (entity as any).id },
            data: entity,
        });
    }

    async delete(entity: T): Promise<void> {
        await (this.prisma as any)[this.modelName].delete({
            where: { id: (entity as any).id },
        });
    }
}

// Specific repository with custom methods
@injectable()
class UserRepositoryImpl extends PrismaRepository<User> implements UserRepository {
    constructor(@inject(TYPES.PrismaClient) prisma: PrismaClient) {
        super(prisma, "user");
    }

    async findByEmail(email: string): Promise<User | null> {
        return this.prisma.user.findUnique({ where: { email } });
    }

    async findPendingSync(): Promise<User[]> {
        return this.prisma.user.findMany({
            where: { syncStatus: SyncStatus.PENDING },
        });
    }

    async existsByEmail(email: string): Promise<boolean> {
        const count = await this.prisma.user.count({ where: { email } });
        return count > 0;
    }
}
```

### Cache-Aside Pattern

```typescript
import Redis from "ioredis";

@injectable()
class CacheAside {
    constructor(
        @inject(TYPES.RedisClient) private readonly redis: Redis,
        private readonly defaultTtl: number = 3600,
        private readonly prefix: string = ""
    ) {}

    private makeKey(key: string): string {
        return `${this.prefix}${key}`;
    }

    async get<T>(key: string): Promise<T | null> {
        const data = await this.redis.get(this.makeKey(key));
        return data ? JSON.parse(data) : null;
    }

    async set<T>(key: string, value: T, ttl?: number): Promise<void> {
        await this.redis.setex(
            this.makeKey(key),
            ttl ?? this.defaultTtl,
            JSON.stringify(value)
        );
    }

    async delete(key: string): Promise<void> {
        await this.redis.del(this.makeKey(key));
    }

    async getOrLoad<T>(
        key: string,
        loader: () => Promise<T>,
        ttl?: number
    ): Promise<T> {
        const cached = await this.get<T>(key);
        if (cached !== null) {
            return cached;
        }

        const value = await loader();
        if (value !== null && value !== undefined) {
            await this.set(key, value, ttl);
        }

        return value;
    }
}

// Decorator pattern for caching
function cached(keyTemplate: string, ttl: number = 3600) {
    return function (
        target: any,
        propertyKey: string,
        descriptor: PropertyDescriptor
    ) {
        const originalMethod = descriptor.value;

        descriptor.value = async function (...args: any[]) {
            const cache = (this as any).cache as CacheAside;
            if (!cache) {
                return originalMethod.apply(this, args);
            }

            const cacheKey = keyTemplate.replace(/\{(\d+)\}/g, (_, index) =>
                String(args[parseInt(index)])
            );

            return cache.getOrLoad(cacheKey, () => originalMethod.apply(this, args), ttl);
        };

        return descriptor;
    };
}

// Usage
@injectable()
class UserService {
    constructor(
        @inject(TYPES.UserRepository) private readonly repo: UserRepository,
        @inject(TYPES.CacheRepository) private readonly cache: CacheAside
    ) {}

    @cached("user:{0}", 1800)
    async getUser(userId: string): Promise<UserDto | null> {
        const user = await this.repo.findById(userId);
        return user ? toUserDto(user) : null;
    }
}
```

---

## API Design Patterns

### Router Factory Pattern

```typescript
import { Router, Request, Response, NextFunction } from "express";
import { z, ZodSchema } from "zod";

interface CrudOptions<T> {
    service: {
        getAll: (page: number, size: number) => Promise<{ data: T[]; total: number }>;
        getById: (id: string) => Promise<T | null>;
        create: (data: any) => Promise<T>;
        update: (id: string, data: any) => Promise<T | null>;
        delete: (id: string) => Promise<boolean>;
    };
    createSchema: ZodSchema;
    updateSchema: ZodSchema;
    authRequired?: boolean;
}

function createCrudRouter<T>(options: CrudOptions<T>): Router {
    const router = Router();
    const { service, createSchema, updateSchema, authRequired = true } = options;

    const auth = authRequired ? [jwtRequired] : [];

    router.get("/", ...auth, async (req: Request, res: Response, next: NextFunction) => {
        try {
            const page = parseInt(req.query.page as string) || 0;
            const size = parseInt(req.query.size as string) || 10;

            const result = await service.getAll(page, size);

            res.json({
                data: result.data,
                page,
                size,
                total: result.total,
            });
        } catch (error) {
            next(error);
        }
    });

    router.get("/:id", ...auth, async (req: Request, res: Response, next: NextFunction) => {
        try {
            const item = await service.getById(req.params.id);
            if (!item) {
                return res.status(404).json({ error: "Not found" });
            }
            res.json(item);
        } catch (error) {
            next(error);
        }
    });

    router.post("/", ...auth, async (req: Request, res: Response, next: NextFunction) => {
        try {
            const data = createSchema.parse(req.body);
            const item = await service.create(data);
            res.status(201).json(item);
        } catch (error) {
            next(error);
        }
    });

    router.put("/:id", ...auth, async (req: Request, res: Response, next: NextFunction) => {
        try {
            const data = updateSchema.parse(req.body);
            const item = await service.update(req.params.id, data);
            if (!item) {
                return res.status(404).json({ error: "Not found" });
            }
            res.json(item);
        } catch (error) {
            next(error);
        }
    });

    router.delete("/:id", ...auth, async (req: Request, res: Response, next: NextFunction) => {
        try {
            const deleted = await service.delete(req.params.id);
            if (!deleted) {
                return res.status(404).json({ error: "Not found" });
            }
            res.status(204).send();
        } catch (error) {
            next(error);
        }
    });

    return router;
}

// Usage
const userRouter = createCrudRouter({
    service: container.get<IUserService>(TYPES.UserService),
    createSchema: createUserSchema,
    updateSchema: updateUserSchema,
});
```

### Request/Response DTO Pattern

```typescript
import { z } from "zod";

// Request DTOs with Zod validation
export const createUserSchema = z.object({
    name: z.string().min(1).max(255),
    email: z.string().email(),
    password: z.string().min(8),
});

export const updateUserSchema = z.object({
    name: z.string().min(1).max(255).optional(),
    email: z.string().email().optional(),
});

export type CreateUserDto = z.infer<typeof createUserSchema>;
export type UpdateUserDto = z.infer<typeof updateUserSchema>;

// Response DTOs
export interface UserDto {
    id: string;
    name: string;
    email: string;
    createdAt: string;
    updatedAt: string;
}

export interface ApiResponse<T> {
    data: T;
    message: string;
    timestamp: string;
}

export interface PaginatedResponse<T> {
    data: T[];
    page: number;
    size: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrevious: boolean;
}

export interface ErrorResponse {
    error: string;
    message: string;
    details?: Record<string, unknown>;
    timestamp: string;
}

// Response helpers
export function successResponse<T>(data: T, message = "Success"): ApiResponse<T> {
    return {
        data,
        message,
        timestamp: new Date().toISOString(),
    };
}

export function paginatedResponse<T>(
    data: T[],
    page: number,
    size: number,
    total: number
): PaginatedResponse<T> {
    const totalPages = Math.ceil(total / size);
    return {
        data,
        page,
        size,
        total,
        totalPages,
        hasNext: page < totalPages - 1,
        hasPrevious: page > 0,
    };
}

export function errorResponse(
    error: string,
    message: string,
    details?: Record<string, unknown>
): ErrorResponse {
    return {
        error,
        message,
        details,
        timestamp: new Date().toISOString(),
    };
}
```

---

## Error Handling Patterns

### Custom Exception Hierarchy

```typescript
export enum ErrorCode {
    // Network errors
    NETWORK_UNAVAILABLE = "NETWORK_UNAVAILABLE",
    TIMEOUT = "TIMEOUT",
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE",

    // Auth errors
    UNAUTHORIZED = "UNAUTHORIZED",
    TOKEN_EXPIRED = "TOKEN_EXPIRED",
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS",

    // Data errors
    NOT_FOUND = "NOT_FOUND",
    VALIDATION_FAILED = "VALIDATION_FAILED",
    CONFLICT = "CONFLICT",

    // General errors
    INTERNAL_ERROR = "INTERNAL_ERROR",
}

export class AppException extends Error {
    constructor(
        public readonly errorCode: ErrorCode,
        public readonly message: string,
        public readonly httpStatus: number = 500,
        public readonly details?: Record<string, unknown>
    ) {
        super(message);
        this.name = "AppException";
    }

    static notFound(message: string): AppException {
        return new AppException(ErrorCode.NOT_FOUND, message, 404);
    }

    static unauthorized(message: string): AppException {
        return new AppException(ErrorCode.UNAUTHORIZED, message, 401);
    }

    static validation(message: string, details: Record<string, unknown>): AppException {
        return new AppException(ErrorCode.VALIDATION_FAILED, message, 400, details);
    }

    static conflict(message: string): AppException {
        return new AppException(ErrorCode.CONFLICT, message, 409);
    }

    static internal(message: string): AppException {
        return new AppException(ErrorCode.INTERNAL_ERROR, message, 500);
    }

    toJSON() {
        return {
            code: this.errorCode,
            message: this.message,
            details: this.details,
            timestamp: new Date().toISOString(),
        };
    }
}

// Entity-specific exceptions
export class UserNotFoundException extends AppException {
    constructor(userId: string) {
        super(ErrorCode.NOT_FOUND, `User not found: ${userId}`, 404, { userId });
    }
}

export class EmailAlreadyExistsException extends AppException {
    constructor(email: string) {
        super(ErrorCode.CONFLICT, `Email already registered: ${email}`, 409, { email });
    }
}

// Global error handler middleware
export function errorHandler(
    error: Error,
    req: Request,
    res: Response,
    next: NextFunction
): void {
    if (error instanceof AppException) {
        res.status(error.httpStatus).json(error.toJSON());
        return;
    }

    if (error instanceof z.ZodError) {
        res.status(400).json({
            code: ErrorCode.VALIDATION_FAILED,
            message: "Validation failed",
            details: error.flatten(),
            timestamp: new Date().toISOString(),
        });
        return;
    }

    console.error("Unexpected error:", error);

    res.status(500).json({
        code: ErrorCode.INTERNAL_ERROR,
        message: "An internal error occurred",
        timestamp: new Date().toISOString(),
    });
}
```

### Result Pattern

```typescript
type Result<T, E = Error> = Success<T> | Failure<E>;

class Success<T> {
    readonly isSuccess = true;
    readonly isFailure = false;

    constructor(public readonly value: T) {}
}

class Failure<E> {
    readonly isSuccess = false;
    readonly isFailure = true;

    constructor(public readonly error: E) {}
}

function success<T>(value: T): Result<T, never> {
    return new Success(value);
}

function failure<E>(error: E): Result<never, E> {
    return new Failure(error);
}

// Usage in service
@injectable()
class UserService {
    async createUser(dto: CreateUserDto): Promise<Result<UserDto, string>> {
        const existing = await this.repo.findByEmail(dto.email);
        if (existing) {
            return failure("Email already exists");
        }

        try {
            const user = await this.repo.save({
                name: dto.name,
                email: dto.email,
                passwordHash: await bcrypt.hash(dto.password, 10),
                syncStatus: SyncStatus.SYNCED,
            });
            return success(toUserDto(user));
        } catch (error) {
            return failure(String(error));
        }
    }
}

// Usage in controller
router.post("/", async (req, res, next) => {
    const dto = createUserSchema.parse(req.body);
    const result = await userService.createUser(dto);

    if (result.isSuccess) {
        res.status(201).json(result.value);
    } else {
        res.status(400).json({ error: result.error });
    }
});
```

---

## Testing Patterns

### Test Fixtures with Vitest

```typescript
// tests/fixtures/index.ts
import { User, SyncStatus } from "../../src/model/User";

export function createMockUser(overrides: Partial<User> = {}): User {
    return {
        id: "test-user-id",
        name: "Test User",
        email: "test@example.com",
        passwordHash: "hashed_password",
        syncStatus: SyncStatus.SYNCED,
        createdAt: new Date(),
        updatedAt: new Date(),
        ...overrides,
    };
}

export function createMockUsers(count: number): User[] {
    return Array.from({ length: count }, (_, i) =>
        createMockUser({
            id: `user-${i}`,
            name: `User ${i}`,
            email: `user${i}@example.com`,
        })
    );
}

// tests/mocks/UserRepository.mock.ts
import { vi } from "vitest";
import { UserRepository } from "../../src/repository/UserRepository";

export function createMockUserRepository(): UserRepository {
    return {
        findById: vi.fn(),
        findByEmail: vi.fn(),
        findAll: vi.fn(),
        findPendingSync: vi.fn(),
        save: vi.fn(),
        update: vi.fn(),
        delete: vi.fn(),
    };
}
```

### Service Layer Tests

```typescript
// tests/service/UserService.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { UserService } from "../../src/service/UserService";
import { createMockUserRepository } from "../mocks/UserRepository.mock";
import { createMockUser } from "../fixtures";

describe("UserService", () => {
    let userService: UserService;
    let mockRepository: ReturnType<typeof createMockUserRepository>;

    beforeEach(() => {
        mockRepository = createMockUserRepository();
        userService = new UserService(mockRepository);
    });

    describe("getUser", () => {
        it("should return user when found", async () => {
            const mockUser = createMockUser();
            vi.mocked(mockRepository.findById).mockResolvedValue(mockUser);

            const result = await userService.getUser("test-user-id");

            expect(result).not.toBeNull();
            expect(result?.id).toBe("test-user-id");
            expect(mockRepository.findById).toHaveBeenCalledWith("test-user-id");
        });

        it("should return null when user not found", async () => {
            vi.mocked(mockRepository.findById).mockResolvedValue(null);

            const result = await userService.getUser("nonexistent");

            expect(result).toBeNull();
        });
    });

    describe("createUser", () => {
        it("should create user successfully", async () => {
            vi.mocked(mockRepository.findByEmail).mockResolvedValue(null);
            vi.mocked(mockRepository.save).mockImplementation(async (user) =>
                createMockUser({ ...user, id: "new-id" })
            );

            const result = await userService.createUser({
                name: "John Doe",
                email: "john@example.com",
                password: "password123",
            });

            expect(result.name).toBe("John Doe");
            expect(result.email).toBe("john@example.com");
            expect(mockRepository.save).toHaveBeenCalled();
        });

        it("should throw error when email exists", async () => {
            vi.mocked(mockRepository.findByEmail).mockResolvedValue(
                createMockUser({ email: "john@example.com" })
            );

            await expect(
                userService.createUser({
                    name: "John Doe",
                    email: "john@example.com",
                    password: "password123",
                })
            ).rejects.toThrow("Email already registered");
        });
    });
});
```

### Integration Tests

```typescript
// tests/integration/UserController.test.ts
import { describe, it, expect, beforeAll, afterAll, beforeEach } from "vitest";
import request from "supertest";
import { app } from "../../src/app";
import { container } from "../../src/container/container";
import { PrismaClient } from "@prisma/client";
import { TYPES } from "../../src/container/types";

describe("UserController Integration", () => {
    let prisma: PrismaClient;
    let authToken: string;

    beforeAll(async () => {
        prisma = container.get<PrismaClient>(TYPES.PrismaClient);
        // Setup test authentication
        authToken = await getTestAuthToken();
    });

    beforeEach(async () => {
        // Clean database
        await prisma.user.deleteMany();
    });

    afterAll(async () => {
        await prisma.$disconnect();
    });

    describe("GET /api/v1/users", () => {
        it("should return paginated users", async () => {
            // Seed test data
            await prisma.user.createMany({
                data: [
                    { name: "User 1", email: "user1@test.com", passwordHash: "hash" },
                    { name: "User 2", email: "user2@test.com", passwordHash: "hash" },
                ],
            });

            const response = await request(app)
                .get("/api/v1/users")
                .set("Authorization", `Bearer ${authToken}`);

            expect(response.status).toBe(200);
            expect(response.body.data).toHaveLength(2);
            expect(response.body.total).toBe(2);
        });

        it("should return 401 without auth", async () => {
            const response = await request(app).get("/api/v1/users");

            expect(response.status).toBe(401);
        });
    });

    describe("POST /api/v1/users", () => {
        it("should create user with valid data", async () => {
            const response = await request(app)
                .post("/api/v1/users")
                .set("Authorization", `Bearer ${authToken}`)
                .send({
                    name: "New User",
                    email: "new@test.com",
                    password: "password123",
                });

            expect(response.status).toBe(201);
            expect(response.body.name).toBe("New User");
            expect(response.body.email).toBe("new@test.com");
        });

        it("should return 400 for invalid data", async () => {
            const response = await request(app)
                .post("/api/v1/users")
                .set("Authorization", `Bearer ${authToken}`)
                .send({
                    name: "",
                    email: "invalid",
                    password: "short",
                });

            expect(response.status).toBe(400);
        });
    });
});
```

---

## Event-Driven Patterns

### Domain Events with Redis Pub/Sub

```typescript
// src/events/EventPublisher.ts
import Redis from "ioredis";
import { v4 as uuid } from "uuid";

export interface DomainEvent {
    id: string;
    type: string;
    data: Record<string, unknown>;
    timestamp: string;
    source: string;
}

@injectable()
export class RedisEventPublisher implements EventPublisher {
    private readonly channelPrefix = "events:";
    private localHandlers: Map<string, ((event: DomainEvent) => void)[]> = new Map();

    constructor(@inject(TYPES.RedisClient) private readonly redis: Redis) {}

    async publish(eventType: string, data: Record<string, unknown>): Promise<string> {
        const event: DomainEvent = {
            id: uuid(),
            type: eventType,
            data,
            timestamp: new Date().toISOString(),
            source: "arcana-nodejs",
        };

        // Publish to Redis
        const channel = `${this.channelPrefix}${eventType}`;
        await this.redis.publish(channel, JSON.stringify(event));

        console.log(`Published event: ${eventType} (${event.id})`);

        // Call local handlers
        this.callLocalHandlers(event);

        return event.id;
    }

    subscribe(eventType: string, handler: (event: DomainEvent) => void): void {
        if (!this.localHandlers.has(eventType)) {
            this.localHandlers.set(eventType, []);
        }
        this.localHandlers.get(eventType)!.push(handler);
    }

    private callLocalHandlers(event: DomainEvent): void {
        const handlers = this.localHandlers.get(event.type) || [];
        for (const handler of handlers) {
            try {
                handler(event);
            } catch (error) {
                console.error(`Event handler error for ${event.type}:`, error);
            }
        }
    }
}

// src/events/EventConsumer.ts
@injectable()
export class RedisEventConsumer {
    private handlers: Map<string, (event: DomainEvent) => Promise<void>> = new Map();
    private running = false;

    constructor(@inject(TYPES.RedisClient) private readonly redis: Redis) {}

    register(eventType: string, handler: (event: DomainEvent) => Promise<void>): void {
        this.handlers.set(eventType, handler);
    }

    async start(): Promise<void> {
        this.running = true;
        const subscriber = this.redis.duplicate();

        const channels = Array.from(this.handlers.keys()).map(
            (type) => `events:${type}`
        );

        await subscriber.subscribe(...channels);
        console.log(`Started consuming events from: ${channels.join(", ")}`);

        subscriber.on("message", async (channel, message) => {
            if (!this.running) return;

            try {
                const event: DomainEvent = JSON.parse(message);
                const handler = this.handlers.get(event.type);

                if (handler) {
                    console.log(`Processing event: ${event.type} (${event.id})`);
                    await handler(event);
                }
            } catch (error) {
                console.error("Error processing event:", error);
            }
        });
    }

    stop(): void {
        this.running = false;
    }
}

// Event handlers
// src/events/handlers/userHandlers.ts
export function handleUserRegistered(event: DomainEvent): Promise<void> {
    const { userId, email, name } = event.data;
    // Queue welcome email
    console.log(`Queuing welcome email for user ${userId}`);
    return Promise.resolve();
}

export function handlePasswordChanged(event: DomainEvent): Promise<void> {
    const { userId } = event.data;
    // Revoke all sessions, send security alert
    console.log(`Password changed for user ${userId}`);
    return Promise.resolve();
}

// Register handlers
export function registerEventHandlers(consumer: RedisEventConsumer): void {
    consumer.register("user.registered", handleUserRegistered);
    consumer.register("user.password_changed", handlePasswordChanged);
}
```
