# Node.js Developer Skill - Code Examples

## Table of Contents
1. [User Authentication Feature](#user-authentication-feature)
2. [CRUD with REST and gRPC](#crud-with-rest-and-grpc)
3. [Background Task Processing](#background-task-processing)
4. [File Upload Service](#file-upload-service)
5. [Event-Driven Architecture](#event-driven-architecture)

---

## User Authentication Feature

### Domain Layer

```typescript
// src/model/Auth.ts
export enum TokenType {
    ACCESS = "access",
    REFRESH = "refresh",
}

export interface TokenPair {
    accessToken: string;
    refreshToken: string;
    tokenType: string;
    expiresIn: number;
}

export interface RefreshToken {
    id: string;
    token: string;
    userId: string;
    expiresAt: Date;
    revoked: boolean;
    revokedAt: Date | null;
    createdAt: Date;
}

// src/dto/AuthDto.ts
import { z } from "zod";

export const loginSchema = z.object({
    email: z.string().email(),
    password: z.string().min(1),
});

export const registerSchema = z.object({
    name: z.string().min(1).max(255),
    email: z.string().email(),
    password: z.string().min(8),
});

export const changePasswordSchema = z.object({
    currentPassword: z.string().min(1),
    newPassword: z.string().min(8),
});

export const refreshTokenSchema = z.object({
    refreshToken: z.string().min(1),
});

export type LoginDto = z.infer<typeof loginSchema>;
export type RegisterDto = z.infer<typeof registerSchema>;
export type ChangePasswordDto = z.infer<typeof changePasswordSchema>;
export type RefreshTokenDto = z.infer<typeof refreshTokenSchema>;
```

### Service Layer

```typescript
// src/service/AuthService.ts
import { injectable, inject } from "inversify";
import { v4 as uuid } from "uuid";
import bcrypt from "bcrypt";
import jwt from "jsonwebtoken";
import { User, SyncStatus } from "../model/User";
import { TokenPair, RefreshToken } from "../model/Auth";
import { UserRepository } from "../repository/UserRepository";
import { RefreshTokenRepository } from "../repository/RefreshTokenRepository";
import { LoginDto, RegisterDto, ChangePasswordDto, RefreshTokenDto } from "../dto/AuthDto";
import { TYPES } from "../container/types";
import { AppException, ErrorCode } from "../shared/exceptions/AppException";
import { EventPublisher } from "../events/EventPublisher";

export interface IAuthService {
    login(dto: LoginDto): Promise<TokenPair>;
    register(dto: RegisterDto): Promise<User>;
    refreshToken(dto: RefreshTokenDto): Promise<TokenPair>;
    logout(refreshToken: string): Promise<void>;
    logoutAll(userId: string): Promise<void>;
    changePassword(userId: string, dto: ChangePasswordDto): Promise<void>;
    verifyToken(token: string): JwtPayload | null;
}

interface JwtPayload {
    sub: string;
    roles: string[];
    iat: number;
    exp: number;
}

@injectable()
export class AuthService implements IAuthService {
    private readonly jwtSecret = process.env.JWT_SECRET || "your-secret-key";
    private readonly accessTokenExpiry = "24h";
    private readonly refreshTokenExpiry = 7 * 24 * 60 * 60 * 1000; // 7 days

    constructor(
        @inject(TYPES.UserRepository) private readonly userRepo: UserRepository,
        @inject(TYPES.RefreshTokenRepository) private readonly tokenRepo: RefreshTokenRepository,
        @inject(TYPES.EventPublisher) private readonly events: EventPublisher
    ) {}

    async login(dto: LoginDto): Promise<TokenPair> {
        const user = await this.userRepo.findByEmail(dto.email);

        if (!user) {
            throw new AppException(ErrorCode.INVALID_CREDENTIALS, "Invalid email or password", 401);
        }

        const isValid = await bcrypt.compare(dto.password, user.passwordHash);
        if (!isValid) {
            await this.events.publish("auth.login_failed", { email: dto.email });
            throw new AppException(ErrorCode.INVALID_CREDENTIALS, "Invalid email or password", 401);
        }

        // Generate tokens
        const roles = ["user"]; // Get from user.roles in real app
        const accessToken = this.createAccessToken(user.id, roles);
        const refreshToken = await this.createRefreshToken(user.id);

        await this.events.publish("auth.login_success", { userId: user.id });

        return {
            accessToken,
            refreshToken: refreshToken.token,
            tokenType: "Bearer",
            expiresIn: 86400, // 24 hours
        };
    }

    async register(dto: RegisterDto): Promise<User> {
        // Check if email exists
        const existing = await this.userRepo.findByEmail(dto.email);
        if (existing) {
            throw AppException.validation("Email already registered", { email: dto.email });
        }

        // Validate password strength
        this.validatePassword(dto.password);

        // Create user
        const user = await this.userRepo.save({
            name: dto.name,
            email: dto.email,
            passwordHash: await bcrypt.hash(dto.password, 10),
            syncStatus: SyncStatus.SYNCED,
        });

        await this.events.publish("auth.user_registered", {
            userId: user.id,
            email: user.email,
            name: user.name,
        });

        return user;
    }

    async refreshToken(dto: RefreshTokenDto): Promise<TokenPair> {
        const storedToken = await this.tokenRepo.findByToken(dto.refreshToken);

        if (!storedToken || storedToken.revoked || storedToken.expiresAt < new Date()) {
            throw new AppException(ErrorCode.TOKEN_EXPIRED, "Invalid or expired refresh token", 401);
        }

        // Revoke old token
        await this.tokenRepo.revoke(storedToken.id);

        // Generate new tokens
        const user = await this.userRepo.findById(storedToken.userId);
        if (!user) {
            throw AppException.notFound("User not found");
        }

        const roles = ["user"];
        const accessToken = this.createAccessToken(user.id, roles);
        const newRefreshToken = await this.createRefreshToken(user.id);

        return {
            accessToken,
            refreshToken: newRefreshToken.token,
            tokenType: "Bearer",
            expiresIn: 86400,
        };
    }

    async logout(refreshToken: string): Promise<void> {
        const storedToken = await this.tokenRepo.findByToken(refreshToken);
        if (storedToken) {
            await this.tokenRepo.revoke(storedToken.id);
        }
    }

    async logoutAll(userId: string): Promise<void> {
        await this.tokenRepo.revokeAllByUser(userId);
    }

    async changePassword(userId: string, dto: ChangePasswordDto): Promise<void> {
        const user = await this.userRepo.findById(userId);
        if (!user) {
            throw AppException.notFound("User not found");
        }

        const isValid = await bcrypt.compare(dto.currentPassword, user.passwordHash);
        if (!isValid) {
            throw new AppException(ErrorCode.INVALID_CREDENTIALS, "Current password is incorrect", 400);
        }

        this.validatePassword(dto.newPassword);

        user.passwordHash = await bcrypt.hash(dto.newPassword, 10);
        await this.userRepo.update(user);

        // Revoke all refresh tokens
        await this.tokenRepo.revokeAllByUser(userId);

        await this.events.publish("auth.password_changed", { userId });
    }

    verifyToken(token: string): JwtPayload | null {
        try {
            return jwt.verify(token, this.jwtSecret) as JwtPayload;
        } catch {
            return null;
        }
    }

    private createAccessToken(userId: string, roles: string[]): string {
        return jwt.sign({ sub: userId, roles }, this.jwtSecret, {
            expiresIn: this.accessTokenExpiry,
        });
    }

    private async createRefreshToken(userId: string): Promise<RefreshToken> {
        const token = jwt.sign({ sub: userId, type: "refresh" }, this.jwtSecret, {
            expiresIn: "7d",
        });

        return this.tokenRepo.save({
            token,
            userId,
            expiresAt: new Date(Date.now() + this.refreshTokenExpiry),
            revoked: false,
            revokedAt: null,
        });
    }

    private validatePassword(password: string): void {
        if (password.length < 8) {
            throw AppException.validation("Password must be at least 8 characters", {});
        }
        if (!/[A-Z]/.test(password)) {
            throw AppException.validation("Password must contain uppercase letter", {});
        }
        if (!/[a-z]/.test(password)) {
            throw AppException.validation("Password must contain lowercase letter", {});
        }
        if (!/[0-9]/.test(password)) {
            throw AppException.validation("Password must contain a number", {});
        }
    }
}
```

### Controller Layer

```typescript
// src/controller/AuthController.ts
import { Router, Request, Response, NextFunction } from "express";
import { IAuthService } from "../service/AuthService";
import { jwtRequired } from "../middleware/auth";
import {
    loginSchema,
    registerSchema,
    changePasswordSchema,
    refreshTokenSchema,
} from "../dto/AuthDto";

export function createAuthController(authService: IAuthService): Router {
    const router = Router();

    router.post("/login", async (req: Request, res: Response, next: NextFunction) => {
        try {
            const dto = loginSchema.parse(req.body);
            const tokenPair = await authService.login(dto);

            res.json({
                accessToken: tokenPair.accessToken,
                refreshToken: tokenPair.refreshToken,
                tokenType: tokenPair.tokenType,
                expiresIn: tokenPair.expiresIn,
            });
        } catch (error) {
            next(error);
        }
    });

    router.post("/register", async (req: Request, res: Response, next: NextFunction) => {
        try {
            const dto = registerSchema.parse(req.body);
            const user = await authService.register(dto);

            res.status(201).json({
                id: user.id,
                name: user.name,
                email: user.email,
            });
        } catch (error) {
            next(error);
        }
    });

    router.post("/refresh", async (req: Request, res: Response, next: NextFunction) => {
        try {
            const dto = refreshTokenSchema.parse(req.body);
            const tokenPair = await authService.refreshToken(dto);

            res.json({
                accessToken: tokenPair.accessToken,
                refreshToken: tokenPair.refreshToken,
                tokenType: tokenPair.tokenType,
                expiresIn: tokenPair.expiresIn,
            });
        } catch (error) {
            next(error);
        }
    });

    router.post("/logout", async (req: Request, res: Response, next: NextFunction) => {
        try {
            const dto = refreshTokenSchema.parse(req.body);
            await authService.logout(dto.refreshToken);
            res.status(204).send();
        } catch (error) {
            next(error);
        }
    });

    router.post("/logout-all", jwtRequired, async (req: Request, res: Response, next: NextFunction) => {
        try {
            const userId = (req as any).userId;
            await authService.logoutAll(userId);
            res.status(204).send();
        } catch (error) {
            next(error);
        }
    });

    router.post("/change-password", jwtRequired, async (req: Request, res: Response, next: NextFunction) => {
        try {
            const dto = changePasswordSchema.parse(req.body);
            const userId = (req as any).userId;
            await authService.changePassword(userId, dto);
            res.status(204).send();
        } catch (error) {
            next(error);
        }
    });

    router.get("/me", jwtRequired, async (req: Request, res: Response, next: NextFunction) => {
        try {
            const userId = (req as any).userId;
            const user = await authService.getUser(userId);
            if (!user) {
                return res.status(404).json({ error: "User not found" });
            }
            res.json(user);
        } catch (error) {
            next(error);
        }
    });

    return router;
}
```

---

## CRUD with REST and gRPC

### Product Service

```typescript
// src/model/Product.ts
export enum ProductStatus {
    DRAFT = "DRAFT",
    ACTIVE = "ACTIVE",
    INACTIVE = "INACTIVE",
    ARCHIVED = "ARCHIVED",
}

export interface Product {
    id: string;
    name: string;
    description: string | null;
    price: number;
    stock: number;
    category: string | null;
    status: ProductStatus;
    createdAt: Date;
    updatedAt: Date;
}

export interface ProductDto {
    id: string;
    name: string;
    description: string | null;
    price: number;
    stock: number;
    category: string | null;
    status: string;
    createdAt: string;
    updatedAt: string;
}

export function toProductDto(product: Product): ProductDto {
    return {
        id: product.id,
        name: product.name,
        description: product.description,
        price: product.price,
        stock: product.stock,
        category: product.category,
        status: product.status,
        createdAt: product.createdAt.toISOString(),
        updatedAt: product.updatedAt.toISOString(),
    };
}

// src/dto/ProductDto.ts
import { z } from "zod";

export const createProductSchema = z.object({
    name: z.string().min(1).max(255),
    description: z.string().optional(),
    price: z.number().min(0),
    stock: z.number().int().min(0).default(0),
    category: z.string().max(100).optional(),
});

export const updateProductSchema = z.object({
    name: z.string().min(1).max(255).optional(),
    description: z.string().optional(),
    price: z.number().min(0).optional(),
    stock: z.number().int().min(0).optional(),
    category: z.string().max(100).optional(),
    status: z.enum(["DRAFT", "ACTIVE", "INACTIVE", "ARCHIVED"]).optional(),
});

export const stockUpdateSchema = z.object({
    quantityChange: z.number().int(),
});

export type CreateProductDto = z.infer<typeof createProductSchema>;
export type UpdateProductDto = z.infer<typeof updateProductSchema>;
export type StockUpdateDto = z.infer<typeof stockUpdateSchema>;
```

### Service Implementation

```typescript
// src/service/ProductService.ts
import { injectable, inject } from "inversify";
import { v4 as uuid } from "uuid";
import { Product, ProductStatus, ProductDto, toProductDto } from "../model/Product";
import { ProductRepository } from "../repository/ProductRepository";
import { CacheRepository } from "../repository/CacheRepository";
import { CreateProductDto, UpdateProductDto } from "../dto/ProductDto";
import { TYPES } from "../container/types";
import { AppException } from "../shared/exceptions/AppException";
import { EventPublisher } from "../events/EventPublisher";

export interface IProductService {
    getProduct(productId: string): Promise<ProductDto | null>;
    getProducts(page: number, size: number, category?: string, status?: string): Promise<{ data: ProductDto[]; total: number }>;
    searchProducts(query: string, options?: SearchOptions): Promise<ProductDto[]>;
    createProduct(dto: CreateProductDto): Promise<ProductDto>;
    updateProduct(productId: string, dto: UpdateProductDto): Promise<ProductDto | null>;
    updateStock(productId: string, quantityChange: number): Promise<ProductDto>;
    deleteProduct(productId: string): Promise<boolean>;
}

interface SearchOptions {
    category?: string;
    minPrice?: number;
    maxPrice?: number;
    limit?: number;
}

@injectable()
export class ProductService implements IProductService {
    private readonly cachePrefix = "product:";
    private readonly cacheTtl = 3600; // 1 hour

    constructor(
        @inject(TYPES.ProductRepository) private readonly repo: ProductRepository,
        @inject(TYPES.CacheRepository) private readonly cache: CacheRepository,
        @inject(TYPES.EventPublisher) private readonly events: EventPublisher
    ) {}

    async getProduct(productId: string): Promise<ProductDto | null> {
        const cacheKey = `${this.cachePrefix}${productId}`;

        // Try cache first
        const cached = await this.cache.get<ProductDto>(cacheKey);
        if (cached) {
            return cached;
        }

        // Load from database
        const product = await this.repo.findById(productId);
        if (product) {
            const dto = toProductDto(product);
            await this.cache.set(cacheKey, dto, this.cacheTtl);
            return dto;
        }

        return null;
    }

    async getProducts(
        page: number = 0,
        size: number = 10,
        category?: string,
        status?: string
    ): Promise<{ data: ProductDto[]; total: number }> {
        const filters: Record<string, unknown> = {};
        if (category) filters.category = category;
        if (status) filters.status = status as ProductStatus;

        const [products, total] = await this.repo.findAll(page, size, filters);

        return {
            data: products.map(toProductDto),
            total,
        };
    }

    async searchProducts(query: string, options: SearchOptions = {}): Promise<ProductDto[]> {
        const products = await this.repo.search(query, options);
        return products.map(toProductDto);
    }

    async createProduct(dto: CreateProductDto): Promise<ProductDto> {
        const product = await this.repo.save({
            name: dto.name,
            description: dto.description || null,
            price: dto.price,
            stock: dto.stock || 0,
            category: dto.category || null,
            status: ProductStatus.DRAFT,
        });

        await this.events.publish("product.created", { productId: product.id });

        return toProductDto(product);
    }

    async updateProduct(productId: string, dto: UpdateProductDto): Promise<ProductDto | null> {
        const product = await this.repo.findById(productId);
        if (!product) {
            return null;
        }

        if (dto.name !== undefined) product.name = dto.name;
        if (dto.description !== undefined) product.description = dto.description;
        if (dto.price !== undefined) product.price = dto.price;
        if (dto.stock !== undefined) product.stock = dto.stock;
        if (dto.category !== undefined) product.category = dto.category;
        if (dto.status !== undefined) product.status = dto.status as ProductStatus;

        const updated = await this.repo.update(product);

        // Invalidate cache
        await this.cache.delete(`${this.cachePrefix}${productId}`);

        await this.events.publish("product.updated", { productId });

        return toProductDto(updated);
    }

    async updateStock(productId: string, quantityChange: number): Promise<ProductDto> {
        const product = await this.repo.findById(productId);
        if (!product) {
            throw AppException.notFound("Product not found");
        }

        const newStock = product.stock + quantityChange;
        if (newStock < 0) {
            throw AppException.validation(`Insufficient stock. Available: ${product.stock}`, {
                available: product.stock,
                requested: -quantityChange,
            });
        }

        product.stock = newStock;
        const updated = await this.repo.update(product);

        // Invalidate cache
        await this.cache.delete(`${this.cachePrefix}${productId}`);

        // Publish stock events
        if (newStock === 0) {
            await this.events.publish("product.out_of_stock", { productId });
        } else if (newStock <= 10) {
            await this.events.publish("product.low_stock", { productId, stock: newStock });
        }

        return toProductDto(updated);
    }

    async deleteProduct(productId: string): Promise<boolean> {
        const product = await this.repo.findById(productId);
        if (!product) {
            return false;
        }

        await this.repo.delete(product);

        // Invalidate cache
        await this.cache.delete(`${this.cachePrefix}${productId}`);

        await this.events.publish("product.deleted", { productId });

        return true;
    }
}
```

### REST Controller

```typescript
// src/controller/ProductController.ts
import { Router, Request, Response, NextFunction } from "express";
import { IProductService } from "../service/ProductService";
import { jwtRequired, roleRequired } from "../middleware/auth";
import { createProductSchema, updateProductSchema, stockUpdateSchema } from "../dto/ProductDto";

export function createProductController(productService: IProductService): Router {
    const router = Router();

    router.get("/", async (req: Request, res: Response, next: NextFunction) => {
        try {
            const page = parseInt(req.query.page as string) || 0;
            const size = parseInt(req.query.size as string) || 10;
            const category = req.query.category as string | undefined;
            const status = req.query.status as string | undefined;

            const result = await productService.getProducts(page, size, category, status);

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

    router.get("/search", async (req: Request, res: Response, next: NextFunction) => {
        try {
            const query = (req.query.q as string) || "";
            const category = req.query.category as string | undefined;
            const minPrice = req.query.min_price ? parseFloat(req.query.min_price as string) : undefined;
            const maxPrice = req.query.max_price ? parseFloat(req.query.max_price as string) : undefined;
            const limit = parseInt(req.query.limit as string) || 20;

            const products = await productService.searchProducts(query, {
                category,
                minPrice,
                maxPrice,
                limit,
            });

            res.json(products);
        } catch (error) {
            next(error);
        }
    });

    router.get("/:productId", async (req: Request, res: Response, next: NextFunction) => {
        try {
            const product = await productService.getProduct(req.params.productId);
            if (!product) {
                return res.status(404).json({ error: "Product not found" });
            }
            res.json(product);
        } catch (error) {
            next(error);
        }
    });

    router.post(
        "/",
        jwtRequired,
        roleRequired("admin"),
        async (req: Request, res: Response, next: NextFunction) => {
            try {
                const dto = createProductSchema.parse(req.body);
                const product = await productService.createProduct(dto);
                res.status(201).json(product);
            } catch (error) {
                next(error);
            }
        }
    );

    router.put(
        "/:productId",
        jwtRequired,
        roleRequired("admin"),
        async (req: Request, res: Response, next: NextFunction) => {
            try {
                const dto = updateProductSchema.parse(req.body);
                const product = await productService.updateProduct(req.params.productId, dto);
                if (!product) {
                    return res.status(404).json({ error: "Product not found" });
                }
                res.json(product);
            } catch (error) {
                next(error);
            }
        }
    );

    router.patch(
        "/:productId/stock",
        jwtRequired,
        roleRequired("admin"),
        async (req: Request, res: Response, next: NextFunction) => {
            try {
                const dto = stockUpdateSchema.parse(req.body);
                const product = await productService.updateStock(
                    req.params.productId,
                    dto.quantityChange
                );
                res.json(product);
            } catch (error) {
                next(error);
            }
        }
    );

    router.delete(
        "/:productId",
        jwtRequired,
        roleRequired("admin"),
        async (req: Request, res: Response, next: NextFunction) => {
            try {
                const deleted = await productService.deleteProduct(req.params.productId);
                if (!deleted) {
                    return res.status(404).json({ error: "Product not found" });
                }
                res.status(204).send();
            } catch (error) {
                next(error);
            }
        }
    );

    return router;
}
```

### gRPC Servicer

```typescript
// src/grpc/ProductServicer.ts
import * as grpc from "@grpc/grpc-js";
import { IProductService } from "../service/ProductService";
import {
    GetProductRequest,
    ListProductsRequest,
    CreateProductRequest,
    UpdateProductRequest,
    UpdateStockRequest,
    DeleteProductRequest,
    ProductResponse,
    ListProductsResponse,
} from "./generated/product_pb";

export class ProductServicer {
    constructor(private readonly productService: IProductService) {}

    async getProduct(
        call: grpc.ServerUnaryCall<GetProductRequest, ProductResponse>,
        callback: grpc.sendUnaryData<ProductResponse>
    ): Promise<void> {
        try {
            const product = await this.productService.getProduct(call.request.getId());

            if (!product) {
                callback({
                    code: grpc.status.NOT_FOUND,
                    message: "Product not found",
                });
                return;
            }

            const response = new ProductResponse();
            response.setId(product.id);
            response.setName(product.name);
            response.setDescription(product.description || "");
            response.setPrice(product.price);
            response.setStock(product.stock);
            response.setCategory(product.category || "");
            response.setStatus(product.status);

            callback(null, response);
        } catch (error) {
            callback({
                code: grpc.status.INTERNAL,
                message: String(error),
            });
        }
    }

    async listProducts(
        call: grpc.ServerUnaryCall<ListProductsRequest, ListProductsResponse>,
        callback: grpc.sendUnaryData<ListProductsResponse>
    ): Promise<void> {
        try {
            const result = await this.productService.getProducts(
                call.request.getPage(),
                call.request.getSize(),
                call.request.getCategory() || undefined,
                call.request.getStatus() || undefined
            );

            const response = new ListProductsResponse();
            response.setTotal(result.total);
            response.setPage(call.request.getPage());
            response.setSize(call.request.getSize());
            response.setHasnext(result.data.length === call.request.getSize());

            result.data.forEach((product) => {
                const productResponse = new ProductResponse();
                productResponse.setId(product.id);
                productResponse.setName(product.name);
                productResponse.setPrice(product.price);
                productResponse.setStock(product.stock);
                response.addProducts(productResponse);
            });

            callback(null, response);
        } catch (error) {
            callback({
                code: grpc.status.INTERNAL,
                message: String(error),
            });
        }
    }

    async createProduct(
        call: grpc.ServerUnaryCall<CreateProductRequest, ProductResponse>,
        callback: grpc.sendUnaryData<ProductResponse>
    ): Promise<void> {
        try {
            const product = await this.productService.createProduct({
                name: call.request.getName(),
                description: call.request.getDescription(),
                price: call.request.getPrice(),
                stock: call.request.getStock(),
                category: call.request.getCategory(),
            });

            const response = new ProductResponse();
            response.setId(product.id);
            response.setName(product.name);
            response.setPrice(product.price);
            response.setStock(product.stock);

            callback(null, response);
        } catch (error) {
            callback({
                code: grpc.status.INVALID_ARGUMENT,
                message: String(error),
            });
        }
    }

    async updateStock(
        call: grpc.ServerUnaryCall<UpdateStockRequest, ProductResponse>,
        callback: grpc.sendUnaryData<ProductResponse>
    ): Promise<void> {
        try {
            const product = await this.productService.updateStock(
                call.request.getProductId(),
                call.request.getQuantityChange()
            );

            const response = new ProductResponse();
            response.setId(product.id);
            response.setName(product.name);
            response.setStock(product.stock);

            callback(null, response);
        } catch (error) {
            callback({
                code: grpc.status.INVALID_ARGUMENT,
                message: String(error),
            });
        }
    }
}
```

---

## Background Task Processing

### BullMQ Task Queue

```typescript
// src/jobs/queue.ts
import { Queue, Worker, Job } from "bullmq";
import Redis from "ioredis";

const connection = new Redis(process.env.REDIS_URL || "redis://localhost:6379");

// Email queue
export const emailQueue = new Queue("emails", { connection });

// Sync queue
export const syncQueue = new Queue("sync", { connection });

// src/jobs/emailWorker.ts
import { Worker, Job } from "bullmq";
import { sendEmail } from "../util/email";

interface WelcomeEmailJob {
    userId: string;
    email: string;
    name: string;
}

interface PasswordResetJob {
    email: string;
    resetToken: string;
}

const emailWorker = new Worker(
    "emails",
    async (job: Job) => {
        switch (job.name) {
            case "welcome":
                await handleWelcomeEmail(job.data as WelcomeEmailJob);
                break;
            case "password-reset":
                await handlePasswordResetEmail(job.data as PasswordResetJob);
                break;
            default:
                console.warn(`Unknown job type: ${job.name}`);
        }
    },
    {
        connection: new Redis(process.env.REDIS_URL || "redis://localhost:6379"),
        concurrency: 5,
    }
);

async function handleWelcomeEmail(data: WelcomeEmailJob): Promise<void> {
    console.log(`Sending welcome email to ${data.email}`);
    await sendEmail({
        to: data.email,
        subject: "Welcome to Arcana!",
        template: "welcome",
        context: { name: data.name },
    });
}

async function handlePasswordResetEmail(data: PasswordResetJob): Promise<void> {
    console.log(`Sending password reset email to ${data.email}`);
    const resetUrl = `https://arcana.com/reset-password?token=${data.resetToken}`;
    await sendEmail({
        to: data.email,
        subject: "Password Reset Request",
        template: "password_reset",
        context: { resetUrl },
    });
}

emailWorker.on("completed", (job) => {
    console.log(`Email job ${job.id} completed`);
});

emailWorker.on("failed", (job, error) => {
    console.error(`Email job ${job?.id} failed:`, error);
});

export { emailWorker };

// src/jobs/syncWorker.ts
import { Worker, Job } from "bullmq";
import { container } from "../container/container";
import { TYPES } from "../container/types";
import { UserRepository } from "../repository/UserRepository";
import { SyncStatus } from "../model/User";

const syncWorker = new Worker(
    "sync",
    async (job: Job) => {
        switch (job.name) {
            case "sync-pending-users":
                await syncPendingUsers();
                break;
            case "cleanup-expired-tokens":
                await cleanupExpiredTokens();
                break;
            default:
                console.warn(`Unknown sync job: ${job.name}`);
        }
    },
    {
        connection: new Redis(process.env.REDIS_URL || "redis://localhost:6379"),
        concurrency: 1,
    }
);

async function syncPendingUsers(): Promise<void> {
    const userRepo = container.get<UserRepository>(TYPES.UserRepository);
    const pendingUsers = await userRepo.findPendingSync();

    console.log(`Syncing ${pendingUsers.length} pending users`);

    for (const user of pendingUsers) {
        try {
            // Call external API to sync user
            // await externalApi.syncUser(user);
            user.syncStatus = SyncStatus.SYNCED;
            await userRepo.update(user);
            console.log(`User ${user.id} synced successfully`);
        } catch (error) {
            user.syncStatus = SyncStatus.FAILED;
            await userRepo.update(user);
            console.error(`Failed to sync user ${user.id}:`, error);
        }
    }
}

async function cleanupExpiredTokens(): Promise<void> {
    const tokenRepo = container.get<RefreshTokenRepository>(TYPES.RefreshTokenRepository);
    const deletedCount = await tokenRepo.deleteExpired(new Date());
    console.log(`Cleaned up ${deletedCount} expired tokens`);
}

export { syncWorker };

// src/jobs/scheduler.ts
import { emailQueue, syncQueue } from "./queue";

export async function setupScheduledJobs(): Promise<void> {
    // Sync pending users every 5 minutes
    await syncQueue.add(
        "sync-pending-users",
        {},
        {
            repeat: { every: 5 * 60 * 1000 },
        }
    );

    // Cleanup expired tokens every hour
    await syncQueue.add(
        "cleanup-expired-tokens",
        {},
        {
            repeat: { every: 60 * 60 * 1000 },
        }
    );

    console.log("Scheduled jobs configured");
}

// Queue job from service
export async function queueWelcomeEmail(userId: string, email: string, name: string): Promise<void> {
    await emailQueue.add("welcome", { userId, email, name }, {
        attempts: 3,
        backoff: { type: "exponential", delay: 1000 },
    });
}
```

---

## File Upload Service

```typescript
// src/service/FileService.ts
import { injectable, inject } from "inversify";
import { v4 as uuid } from "uuid";
import crypto from "crypto";
import path from "path";
import { File, FileStatus } from "../model/File";
import { FileRepository } from "../repository/FileRepository";
import { StorageBackend } from "../util/storage";
import { TYPES } from "../container/types";
import { AppException } from "../shared/exceptions/AppException";
import { EventPublisher } from "../events/EventPublisher";

export interface IFileService {
    uploadFile(
        fileBuffer: Buffer,
        filename: string,
        contentType: string,
        userId: string
    ): Promise<File>;
    getFile(fileId: string): Promise<File | null>;
    deleteFile(fileId: string, userId: string): Promise<boolean>;
    getDownloadUrl(fileId: string, expiresIn?: number): Promise<string | null>;
}

@injectable()
export class FileService implements IFileService {
    private readonly allowedExtensions = new Set([
        "pdf", "png", "jpg", "jpeg", "gif", "doc", "docx", "xls", "xlsx"
    ]);
    private readonly maxFileSize = 10 * 1024 * 1024; // 10MB

    constructor(
        @inject(TYPES.FileRepository) private readonly repo: FileRepository,
        @inject(TYPES.StorageBackend) private readonly storage: StorageBackend,
        @inject(TYPES.EventPublisher) private readonly events: EventPublisher
    ) {}

    async uploadFile(
        fileBuffer: Buffer,
        filename: string,
        contentType: string,
        userId: string
    ): Promise<File> {
        // Validate file
        this.validateFile(filename, fileBuffer.length);

        // Generate unique filename
        const ext = this.getExtension(filename);
        const uniqueFilename = `${uuid()}.${ext}`;

        // Calculate checksum
        const checksum = crypto.createHash("md5").update(fileBuffer).digest("hex");

        // Generate storage path
        const now = new Date();
        const storagePath = `${now.getFullYear()}/${String(now.getMonth() + 1).padStart(2, "0")}/${String(now.getDate()).padStart(2, "0")}/${uniqueFilename}`;

        // Upload to storage
        const url = await this.storage.upload(storagePath, fileBuffer, contentType);

        // Create file record
        const file = await this.repo.save({
            originalFilename: path.basename(filename),
            storagePath,
            url,
            contentType,
            fileSize: fileBuffer.length,
            checksum,
            uploadedBy: userId,
            status: FileStatus.ACTIVE,
        });

        await this.events.publish("file.uploaded", {
            fileId: file.id,
            userId,
        });

        return file;
    }

    async getFile(fileId: string): Promise<File | null> {
        return this.repo.findById(fileId);
    }

    async deleteFile(fileId: string, userId: string): Promise<boolean> {
        const file = await this.repo.findById(fileId);
        if (!file) {
            return false;
        }

        // Check permission
        if (file.uploadedBy !== userId) {
            throw new AppException(
                "FORBIDDEN" as any,
                "Not authorized to delete this file",
                403
            );
        }

        // Delete from storage
        await this.storage.delete(file.storagePath);

        // Soft delete record
        file.status = FileStatus.DELETED;
        await this.repo.update(file);

        await this.events.publish("file.deleted", {
            fileId,
            userId,
        });

        return true;
    }

    async getDownloadUrl(fileId: string, expiresIn: number = 3600): Promise<string | null> {
        const file = await this.repo.findById(fileId);
        if (!file || file.status !== FileStatus.ACTIVE) {
            return null;
        }

        return this.storage.getPresignedUrl(file.storagePath, expiresIn);
    }

    private validateFile(filename: string, size: number): void {
        const ext = this.getExtension(filename);
        if (!this.allowedExtensions.has(ext)) {
            throw AppException.validation(`File type not allowed: ${ext}`, { extension: ext });
        }

        if (size > this.maxFileSize) {
            throw AppException.validation(
                `File too large. Max size: ${this.maxFileSize} bytes`,
                { maxSize: this.maxFileSize, actualSize: size }
            );
        }
    }

    private getExtension(filename: string): string {
        const parts = filename.split(".");
        return parts.length > 1 ? parts.pop()!.toLowerCase() : "";
    }
}

// src/controller/FileController.ts
import { Router, Request, Response, NextFunction } from "express";
import multer from "multer";
import { IFileService } from "../service/FileService";
import { jwtRequired } from "../middleware/auth";

const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: 10 * 1024 * 1024 },
});

export function createFileController(fileService: IFileService): Router {
    const router = Router();

    router.post(
        "/",
        jwtRequired,
        upload.single("file"),
        async (req: Request, res: Response, next: NextFunction) => {
            try {
                if (!req.file) {
                    return res.status(400).json({ error: "No file provided" });
                }

                const userId = (req as any).userId;
                const file = await fileService.uploadFile(
                    req.file.buffer,
                    req.file.originalname,
                    req.file.mimetype,
                    userId
                );

                res.status(201).json({
                    id: file.id,
                    filename: file.originalFilename,
                    url: file.url,
                    size: file.fileSize,
                    contentType: file.contentType,
                });
            } catch (error) {
                next(error);
            }
        }
    );

    router.get("/:fileId", jwtRequired, async (req: Request, res: Response, next: NextFunction) => {
        try {
            const file = await fileService.getFile(req.params.fileId);
            if (!file) {
                return res.status(404).json({ error: "File not found" });
            }

            res.json({
                id: file.id,
                filename: file.originalFilename,
                url: file.url,
                size: file.fileSize,
                contentType: file.contentType,
                uploadedAt: file.createdAt.toISOString(),
            });
        } catch (error) {
            next(error);
        }
    });

    router.get("/:fileId/download", jwtRequired, async (req: Request, res: Response, next: NextFunction) => {
        try {
            const url = await fileService.getDownloadUrl(req.params.fileId);
            if (!url) {
                return res.status(404).json({ error: "File not found" });
            }

            res.json({ downloadUrl: url });
        } catch (error) {
            next(error);
        }
    });

    router.delete("/:fileId", jwtRequired, async (req: Request, res: Response, next: NextFunction) => {
        try {
            const userId = (req as any).userId;
            const deleted = await fileService.deleteFile(req.params.fileId, userId);
            if (!deleted) {
                return res.status(404).json({ error: "File not found" });
            }
            res.status(204).send();
        } catch (error) {
            next(error);
        }
    });

    return router;
}
```

---

## Event-Driven Architecture

```typescript
// src/events/EventPublisher.ts
import { injectable, inject } from "inversify";
import Redis from "ioredis";
import { v4 as uuid } from "uuid";
import { TYPES } from "../container/types";

export interface DomainEvent {
    id: string;
    type: string;
    data: Record<string, unknown>;
    timestamp: string;
    source: string;
}

export interface EventPublisher {
    publish(eventType: string, data: Record<string, unknown>): Promise<string>;
    subscribe(eventType: string, handler: (event: DomainEvent) => void): void;
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
    private subscriber: Redis | null = null;

    constructor(@inject(TYPES.RedisClient) private readonly redis: Redis) {}

    register(eventType: string, handler: (event: DomainEvent) => Promise<void>): void {
        this.handlers.set(eventType, handler);
    }

    async start(): Promise<void> {
        this.running = true;
        this.subscriber = this.redis.duplicate();

        const channels = Array.from(this.handlers.keys()).map(
            (type) => `events:${type}`
        );

        await this.subscriber.subscribe(...channels);
        console.log(`Started consuming events from: ${channels.join(", ")}`);

        this.subscriber.on("message", async (channel, message) => {
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

    async stop(): Promise<void> {
        this.running = false;
        if (this.subscriber) {
            await this.subscriber.quit();
        }
    }
}

// src/events/handlers/userHandlers.ts
import { DomainEvent } from "../EventPublisher";
import { queueWelcomeEmail } from "../../jobs/scheduler";

export async function handleUserRegistered(event: DomainEvent): Promise<void> {
    const { userId, email, name } = event.data as {
        userId: string;
        email: string;
        name: string;
    };

    // Queue welcome email
    await queueWelcomeEmail(userId, email, name);
    console.log(`Queued welcome email for user ${userId}`);
}

export async function handlePasswordChanged(event: DomainEvent): Promise<void> {
    const { userId } = event.data as { userId: string };
    // Send security alert, etc.
    console.log(`Password changed for user ${userId}`);
}

export async function handleProductOutOfStock(event: DomainEvent): Promise<void> {
    const { productId } = event.data as { productId: string };
    // Notify admin, update status
    console.log(`Product out of stock: ${productId}`);
}

// Register handlers
export function registerEventHandlers(consumer: RedisEventConsumer): void {
    consumer.register("auth.user_registered", handleUserRegistered);
    consumer.register("auth.password_changed", handlePasswordChanged);
    consumer.register("product.out_of_stock", handleProductOutOfStock);
}
```
