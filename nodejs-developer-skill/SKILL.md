---
name: nodejs-developer-skill
description: Node.js/Express development guide based on Arcana Cloud Node.js enterprise architecture. Provides comprehensive support for Clean Architecture, InversifyJS DI, gRPC-first communication (1.80x faster), dual-protocol support, Prisma ORM, and multiple deployment modes. Suitable for Node.js microservices development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# Node.js Developer Skill

Professional Node.js/Express/TypeScript development skill based on [Arcana Cloud Node.js](https://github.com/jrjohn/arcana-cloud-nodejs) enterprise architecture.

---

## Quick Reference Card

### New Endpoint Checklist:
```
1. Add route with router.get/post/put/delete in controller
2. Add method to Service interface (abstract class)
3. Implement method in ServiceImpl with @injectable
4. Add Repository method if data access needed
5. Add Zod schema for request validation
6. Register route in Express app
7. Verify mock data returns non-empty values
```

### New gRPC Service Checklist:
```
1. Define service in protos/*.proto
2. Run protoc to generate TypeScript code
3. Create Servicer class implementing generated interface
4. Implement ALL rpc methods (count must match)
5. Wire to existing Service layer via DI container
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Empty response | `grep -rn "\[\]\|return \[\]" src/repository/*Impl.ts` |
| 500 error | `grep -rn "throw new Error\|NotImplemented" src/` |
| gRPC UNIMPLEMENTED | Compare `rpc ` count in .proto vs methods in servicer |
| DI error | Check `@injectable()` decorator and container bindings |

---

## Rules Priority

### 🔴 CRITICAL (Must Fix Immediately)

| Rule | Description | Verification |
|------|-------------|--------------|
| Zero-Empty Policy | Repository stubs NEVER return empty arrays | `grep -rn "= \[\]\|return \[\]" src/repository/*Impl.ts` |
| API Wiring | ALL routes must call existing Service methods | Check route→service calls |
| gRPC Implementation | ALL proto rpc methods MUST be implemented | Count rpc vs method definitions |
| Type Safety | ALL functions have TypeScript types | `npm run type-check` |
| DI Registration | ALL services registered in container | Check `container.bind()` calls |

### 🟡 IMPORTANT (Should Fix Before PR)

| Rule | Description | Verification |
|------|-------------|--------------|
| Input Validation | Zod schemas for all requests | Check request schemas |
| Mock Data Quality | Realistic, varied values | Review mock data |
| Error Handling | AppException for all errors | Check exception usage |
| Logging | Structured logging | Check logger calls |

### 🟢 RECOMMENDED (Nice to Have)

| Rule | Description |
|------|-------------|
| API Documentation | OpenAPI/Swagger annotations |
| Monitoring | Prometheus metrics |
| Caching | Redis caching for hot data |
| Rate Limiting | API rate limits |

---

## Error Handling Pattern

### AppException - Unified Error Model

```typescript
// src/shared/exceptions/AppException.ts
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

    toJSON() {
        return {
            code: this.errorCode,
            message: this.message,
            details: this.details,
            timestamp: new Date().toISOString(),
        };
    }
}
```

### Global Exception Handler

```typescript
// src/middleware/errorHandler.ts
import { Request, Response, NextFunction } from "express";
import { AppException } from "../shared/exceptions/AppException";

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

    // Log unexpected errors
    console.error("Unexpected error:", error);

    res.status(500).json({
        code: "INTERNAL_ERROR",
        message: "An internal error occurred",
        timestamp: new Date().toISOString(),
    });
}
```

---

## Test Coverage Targets

### Coverage by Layer

| Layer | Target | Focus Areas |
|-------|--------|-------------|
| Service | 90%+ | Business logic, edge cases |
| Repository | 80%+ | Data mapping, error handling |
| Controller | 75%+ | Request handling, validation |

### Test Commands
```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- src/service/__tests__/UserService.test.ts

# View coverage report
open coverage/lcov-report/index.html
```

---

## Spec Gap Prediction System

When implementing API from incomplete specifications, PROACTIVELY predict missing requirements:

### CRUD Prediction Matrix

When a spec mentions "User management API", predict ALL CRUD operations:

| Entity | Predicted Endpoints | Status |
|--------|---------------------|--------|
| User | GET /users | Check |
| User | GET /users/:id | Check |
| User | POST /users | Check |
| User | PUT /users/:id | Check |
| User | DELETE /users/:id | Check |
| User | PATCH /users/:id | Check |

### Response State Prediction

For every endpoint, predict required response states:

```typescript
// Predicted states for GET /users/:id:
// ✅ 200 OK - User found
// ✅ 404 Not Found - User doesn't exist
// ✅ 401 Unauthorized - Not logged in
// ✅ 403 Forbidden - No permission
// ✅ 500 Internal Server Error - Server error
```

### Pagination Prediction

List endpoints SHOULD support pagination:

```typescript
// GET /users
// Predicted query parameters:
// - page: number = 0
// - size: number = 10
// - sort: string = "createdAt"
// - order: "asc" | "desc" = "desc"
```

### Filtering Prediction

List endpoints SHOULD support filtering:

```typescript
// GET /users
// Predicted filters:
// - status?: string - Filter by status
// - createdAfter?: Date - Created after date
// - search?: string - Search in name/email
```

### Ask Clarification Prompt

When specs are incomplete, ASK before implementing:

```
The specification mentions "User API" but doesn't specify:
1. Should DELETE be soft-delete or hard-delete?
2. What fields are required for user creation?
3. Is email verification required?
4. What roles/permissions exist?

Please clarify before I proceed with implementation.
```

---

## Core Architecture Principles

### Clean Architecture - Three Layers

```
┌─────────────────────────────────────────────────────┐
│                  Controller Layer                    │
│       Express.js + JWT Auth + Zod Validation        │
│                   Port 3000                          │
├─────────────────────────────────────────────────────┤
│                   Service Layer                      │
│       Business Logic + Domain Events                 │
│                   Port 50051                         │
├─────────────────────────────────────────────────────┤
│                  Repository Layer                    │
│       Prisma ORM + Redis Cache                      │
│                   Port 50052                         │
└─────────────────────────────────────────────────────┘
```

### Deployment Modes
1. **Monolithic**: Single process/container (development) - Direct calls
2. **Layered**: Separate containers per layer with gRPC/HTTP
3. **Microservices**: Fine-grained services with independent scaling (Kubernetes)

### Performance
- gRPC delivers **1.80x average speedup** over HTTP REST
- Read operations: **2.32x faster** with gRPC in layered deployment

## Instructions

When handling Node.js/Express/TypeScript development tasks, follow these principles:

### Quick Verification Commands

Use these commands to quickly check for common issues:

```bash
# 1. Check for unimplemented methods (MUST be empty)
grep -rn "throw new Error.*NotImplemented\|TODO.*implement\|// TODO" src/

# 2. Check for empty route handlers (MUST be empty)
grep -rn "async.*Request.*Response.*{}" src/controller/

# 3. Check all routes have handlers
echo "Routes defined:" && grep -c "router\.\(get\|post\|put\|delete\|patch\)" src/controller/*.ts 2>/dev/null || echo 0
echo "Handler functions:" && grep -c "async.*req.*res" src/controller/*.ts 2>/dev/null || echo 0

# 4. Check gRPC services are implemented
echo "gRPC methods defined in proto:" && grep -c "rpc " src/grpc/protos/*.proto 2>/dev/null || echo 0
echo "gRPC methods implemented:" && grep -c "async.*call.*callback\|async.*request" src/grpc/*Servicer.ts 2>/dev/null || echo 0

# 5. Verify tests pass
npm test

# 6. 🚨 Check Controller routes call existing Service methods (CRITICAL!)
echo "=== Service Methods Called in Controllers ===" && \
grep -roh "this\.\w*Service\.\w*(" src/controller/*.ts | sort -u
echo "=== Service Methods Defined ===" && \
grep -rh "async \w*(" src/service/*.ts | grep -oE "async \w+\(" | sort -u

# 7. 🚨 Verify ALL Controller endpoints have Service layer implementation
echo "=== Controller Service Injections ===" && \
grep -rn "@inject\|container\.get" src/controller/*.ts
echo "=== Service Class Definitions ===" && \
grep -rn "class.*Service\|@injectable" src/service/*.ts

# 8. 🚨 Check for placeholder returns in route handlers
grep -rn "router\.\(get\|post\|put\|delete\)" -A10 src/controller/*.ts | grep -E "Coming Soon\|TODO\|NotImplemented"

# 9. 🚨 Check Service→Repository wiring (CRITICAL!)
echo "=== Repository Methods Called in Services ===" && \
grep -roh "this\.\w*Repository\.\w*(" src/service/*.ts | sort -u
echo "=== Repository Class Methods ===" && \
grep -rh "async \w*(" src/repository/*.ts | grep -oE "async \w+\(" | sort -u

# 10. 🚨 Check InversifyJS DI bindings
echo "=== DI Container Bindings ===" && \
grep -rn "container\.bind\|bind<" src/container/*.ts

# 11. TypeScript type checking
npm run type-check
```

⚠️ **CRITICAL**: All routes MUST have corresponding handler functions. All gRPC methods defined in .proto files MUST be implemented in servicer classes.

⚠️ **API WIRING CRITICAL**: Commands #6-#8 detect Controller routes that call Service methods that don't exist. A Controller can call `this.userService.getAccountInfo()` but if the Service class doesn't have this method, the route fails at runtime!

If any of these return results or counts don't match, FIX THEM before completing the task.

---

## 📊 Mock Data Requirements for Repository Stubs

### The Chart Data Problem

When implementing Repository stubs, **NEVER return empty arrays for data that powers UI charts or API responses**. This causes:
- Frontend charts that render but show nothing
- API responses with empty data arrays
- Client applications showing "No data" even when structure exists

### Mock Data Rules

**Rule 1: List data for charts MUST have at least 7 items**
```typescript
// ❌ BAD - Chart will be blank
async getCurrentWeekSummary(userId: string): Promise<WeeklySummary> {
    return {
        dailyReports: []  // ← Chart has no data to render!
    };
}

// ✅ GOOD - Chart has data to display
async getCurrentWeekSummary(userId: string): Promise<WeeklySummary> {
    const scores = [72, 78, 85, 80, 76, 88, 82];
    const durations = [390, 420, 450, 410, 380, 460, 435];
    const mockDailyReports = scores.map((score, i) =>
        this.createMockDailyReport(score, durations[i])
    );
    return { dailyReports: mockDailyReports };
}
```

**Rule 2: Use realistic, varied sample values**
```typescript
// ❌ BAD - Monotonous test data
const scores = Array(7).fill(80);

// ✅ GOOD - Realistic variation
const scores = [72, 78, 85, 80, 76, 88, 82];  // Shows trend
```

**Rule 3: Data must match interface exactly**
```bash
# Before creating mock data, ALWAYS verify the interface:
grep -A 20 "interface TherapyData" src/model/*.ts
grep -A 20 "interface TherapyData" src/dto/*.ts
```

**Rule 4: Create helper methods for complex mock data**
```typescript
// ✅ Create reusable mock factory
private createMockDailyReport(score: number, duration: number): DailySleepReport {
    return {
        id: `mock_${Date.now()}`,
        sleepScore: score,
        sleepDuration: { totalMinutes: duration },
        // ... all required fields
    };
}
```

### Quick Verification Commands for Mock Data

```bash
# 12. 🚨 Check for empty array returns in Repository stubs (MUST FIX)
grep -rn "= \[\]\|return \[\]" src/repository/*Impl.ts

# 13. 🚨 Verify chart-related data has mock values
grep -rn "dailyReports\|weeklyData\|chartData" src/repository/ | grep -E "= \[\]|return \[\]"
```

---

### 0. Project Setup - CRITICAL

⚠️ **IMPORTANT**: This reference project has been validated with tested package.json and gRPC settings. **NEVER reconfigure project structure or modify package.json dependencies**, or it will cause runtime errors.

**Step 1**: Clone the reference project
```bash
git clone https://github.com/jrjohn/arcana-cloud-nodejs.git [new-project-directory]
cd [new-project-directory]
```

**Step 2**: Reinitialize Git (remove original repo history)
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit from arcana-cloud-nodejs template"
```

**Step 3**: Modify project name
Only modify the following required items:
- `name` field in `package.json`
- Application name in `src/config/settings.ts`
- Service names in Docker-related configuration files
- Update settings in `.env.example` file

**Step 4**: Clean up example code
The cloned project contains example API (e.g., Arcana User Management). Clean up and replace with new project business logic:

**Core architecture files to KEEP** (do not delete):
- `src/config/` - Common configuration (Database, Settings)
- `src/middleware/` - Middleware (Auth, Error handling)
- `src/grpc/server.ts` - gRPC server configuration
- `src/container/` - InversifyJS DI container
- `src/shared/` - Shared utilities and types
- `prisma/` - Prisma configuration
- `deploy/` - Docker & K8s manifests

**Example files to REPLACE**:
- `src/controller/` - Delete example Controller, create new HTTP endpoints
- `src/service/` - Delete example Service, create new business logic
- `src/repository/` - Delete example Repository, create new data access
- `src/model/` - Delete example Models, create new Domain Models
- `src/dto/` - Delete example DTOs, create new DTOs
- `src/grpc/protos/*.proto` - Modify gRPC proto definitions
- `tests/` - Update test cases

**Step 5**: Install dependencies and verify
```bash
npm install
npm run prisma:generate
npm test
```

### ❌ Prohibited Actions
- **DO NOT** create new Express project from scratch
- **DO NOT** modify version numbers in `package.json`
- **DO NOT** add or remove dependencies (unless explicitly required)
- **DO NOT** modify gRPC protobuf compilation settings
- **DO NOT** reconfigure Prisma, InversifyJS, or other library settings

### ✅ Allowed Modifications
- Add business-related TypeScript code (following existing architecture)
- Add Controller, Service, Repository
- Add Domain Models, DTOs
- Add Prisma migration scripts
- Modify gRPC proto files (and recompile)

### 1. TDD & Spec-Driven Development Workflow - MANDATORY

⚠️ **CRITICAL**: All development MUST follow this TDD workflow. Every SRS/SDD requirement must have corresponding tests BEFORE implementation.

🚨 **ABSOLUTE RULE**: TDD = Tests + Implementation. Writing tests without implementation is **INCOMPLETE**. Every test file MUST have corresponding production code that passes the tests.

```
┌─────────────────────────────────────────────────────────────────┐
│                    TDD Development Workflow                      │
├─────────────────────────────────────────────────────────────────┤
│  Step 1: Analyze Spec → Extract all SRS & SDD requirements      │
│  Step 2: Create Tests → Write tests for EACH Spec item          │
│  Step 3: Verify Coverage → Ensure 100% Spec coverage in tests   │
│  Step 4: Implement → Build features to pass tests  ⚠️ MANDATORY │
│  Step 5: Mock APIs → Use mock data for unfinished dependencies  │
│  Step 6: Run All Tests → ALL tests must pass before completion  │
│  Step 7: Verify 100% → Tests written = Features implemented     │
└─────────────────────────────────────────────────────────────────┘
```

#### ⛔ FORBIDDEN: Tests Without Implementation

```typescript
// ❌ WRONG - Test exists but no implementation
// Test file exists: AuthService.test.ts (32 tests)
// Production file: AuthService.ts → MISSING or throws NotImplementedError
// This is INCOMPLETE TDD!

// ✅ CORRECT - Test AND Implementation both exist
// Test file: AuthService.test.ts (32 tests)
// Production file: AuthService.ts (fully implemented)
// All 32 tests PASS
```

#### ⛔ Placeholder Endpoint Policy

Placeholder endpoints are **ONLY** allowed as a temporary route during active development. They are **FORBIDDEN** as a final state.

```typescript
// ❌ WRONG - Placeholder endpoint left in production
router.get("/training", async (req, res) => {
    res.json({ message: "Coming Soon" });  // FORBIDDEN!
});

// ✅ CORRECT - Real endpoint implementation
router.get("/training", async (req, res) => {
    const data = await trainingService.getAll();
    res.json(data);
});
```

**Placeholder Check Command:**
```bash
# This command MUST return empty for production-ready code
grep -rn "NotImplemented\|throw new Error.*implement\|TODO.*implement\|Coming Soon" src/
```

### 2. Project Structure
```
arcana-cloud-nodejs/
├── src/
│   ├── controller/        # HTTP endpoints (Express routes)
│   │   ├── UserController.ts
│   │   └── AuthController.ts
│   ├── service/           # Business logic
│   │   ├── UserService.ts
│   │   └── AuthService.ts
│   ├── repository/        # Data access (Prisma)
│   │   ├── UserRepository.ts
│   │   └── UserRepositoryImpl.ts
│   ├── model/             # Domain models
│   │   └── User.ts
│   ├── dto/               # Data transfer objects
│   │   └── UserDto.ts
│   ├── grpc/              # gRPC services
│   │   ├── server.ts
│   │   ├── protos/
│   │   └── UserServicer.ts
│   ├── container/         # InversifyJS DI container
│   │   └── container.ts
│   ├── middleware/        # Express middleware
│   │   ├── auth.ts
│   │   └── errorHandler.ts
│   ├── config/            # Configuration
│   │   └── settings.ts
│   └── shared/            # Shared utilities
│       ├── types/
│       └── exceptions/
├── prisma/                # Prisma schema & migrations
├── tests/                 # Test suite
├── deploy/                # Docker/K8s configs
└── package.json
```

### 3. Domain Model with Prisma

```prisma
// prisma/schema.prisma
generator client {
    provider = "prisma-client-js"
}

datasource db {
    provider = "mysql"
    url      = env("DATABASE_URL")
}

enum SyncStatus {
    SYNCED
    PENDING
    FAILED
}

model User {
    id           String     @id @default(uuid())
    name         String     @db.VarChar(255)
    email        String     @unique @db.VarChar(255)
    passwordHash String     @map("password_hash") @db.VarChar(255)
    syncStatus   SyncStatus @default(SYNCED) @map("sync_status")
    createdAt    DateTime   @default(now()) @map("created_at")
    updatedAt    DateTime   @updatedAt @map("updated_at")

    refreshTokens RefreshToken[]

    @@map("users")
}
```

```typescript
// src/model/User.ts
export interface User {
    id: string;
    name: string;
    email: string;
    passwordHash: string;
    syncStatus: SyncStatus;
    createdAt: Date;
    updatedAt: Date;
}

export enum SyncStatus {
    SYNCED = "SYNCED",
    PENDING = "PENDING",
    FAILED = "FAILED",
}

export function toUserDto(user: User): UserDto {
    return {
        id: user.id,
        name: user.name,
        email: user.email,
        createdAt: user.createdAt.toISOString(),
        updatedAt: user.updatedAt.toISOString(),
    };
}
```

### 4. Repository Layer

```typescript
// src/repository/UserRepository.ts
import { User, SyncStatus } from "../model/User";

export interface UserRepository {
    findById(userId: string): Promise<User | null>;
    findByEmail(email: string): Promise<User | null>;
    findAll(page: number, size: number): Promise<[User[], number]>;
    findPendingSync(): Promise<User[]>;
    save(user: User): Promise<User>;
    update(user: User): Promise<User>;
    delete(user: User): Promise<void>;
}

// src/repository/UserRepositoryImpl.ts
import { injectable } from "inversify";
import { PrismaClient } from "@prisma/client";
import { UserRepository } from "./UserRepository";
import { User, SyncStatus } from "../model/User";

@injectable()
export class UserRepositoryImpl implements UserRepository {
    constructor(private readonly prisma: PrismaClient) {}

    async findById(userId: string): Promise<User | null> {
        return this.prisma.user.findUnique({
            where: { id: userId },
        });
    }

    async findByEmail(email: string): Promise<User | null> {
        return this.prisma.user.findUnique({
            where: { email },
        });
    }

    async findAll(page: number = 0, size: number = 10): Promise<[User[], number]> {
        const [users, total] = await Promise.all([
            this.prisma.user.findMany({
                skip: page * size,
                take: size,
                orderBy: { createdAt: "desc" },
            }),
            this.prisma.user.count(),
        ]);
        return [users, total];
    }

    async findPendingSync(): Promise<User[]> {
        return this.prisma.user.findMany({
            where: { syncStatus: SyncStatus.PENDING },
        });
    }

    async save(user: Omit<User, "id" | "createdAt" | "updatedAt">): Promise<User> {
        return this.prisma.user.create({
            data: user,
        });
    }

    async update(user: User): Promise<User> {
        return this.prisma.user.update({
            where: { id: user.id },
            data: user,
        });
    }

    async delete(user: User): Promise<void> {
        await this.prisma.user.delete({
            where: { id: user.id },
        });
    }
}
```

### 5. Service Layer

```typescript
// src/service/UserService.ts
import { injectable, inject } from "inversify";
import { v4 as uuid } from "uuid";
import bcrypt from "bcrypt";
import { User, SyncStatus, toUserDto } from "../model/User";
import { UserRepository } from "../repository/UserRepository";
import { CreateUserDto, UpdateUserDto, UserDto } from "../dto/UserDto";
import { TYPES } from "../container/types";
import { AppException } from "../shared/exceptions/AppException";

export interface IUserService {
    getUser(userId: string): Promise<UserDto | null>;
    getUsers(page: number, size: number): Promise<{ data: UserDto[]; total: number }>;
    createUser(dto: CreateUserDto): Promise<UserDto>;
    updateUser(userId: string, dto: UpdateUserDto): Promise<UserDto | null>;
    deleteUser(userId: string): Promise<boolean>;
    authenticate(email: string, password: string): Promise<User | null>;
}

@injectable()
export class UserService implements IUserService {
    constructor(
        @inject(TYPES.UserRepository) private readonly repository: UserRepository
    ) {}

    async getUser(userId: string): Promise<UserDto | null> {
        const user = await this.repository.findById(userId);
        return user ? toUserDto(user) : null;
    }

    async getUsers(page: number = 0, size: number = 10): Promise<{ data: UserDto[]; total: number }> {
        const [users, total] = await this.repository.findAll(page, size);
        return {
            data: users.map(toUserDto),
            total,
        };
    }

    async createUser(dto: CreateUserDto): Promise<UserDto> {
        // Check if email already exists
        const existing = await this.repository.findByEmail(dto.email);
        if (existing) {
            throw AppException.validation("Email already registered", { email: dto.email });
        }

        const user = await this.repository.save({
            name: dto.name,
            email: dto.email,
            passwordHash: await bcrypt.hash(dto.password, 10),
            syncStatus: SyncStatus.SYNCED,
        });

        return toUserDto(user);
    }

    async updateUser(userId: string, dto: UpdateUserDto): Promise<UserDto | null> {
        const user = await this.repository.findById(userId);
        if (!user) {
            return null;
        }

        if (dto.name !== undefined) {
            user.name = dto.name;
        }
        if (dto.email !== undefined) {
            // Check if new email is taken by another user
            const existing = await this.repository.findByEmail(dto.email);
            if (existing && existing.id !== userId) {
                throw AppException.validation("Email already registered", { email: dto.email });
            }
            user.email = dto.email;
        }

        const updated = await this.repository.update(user);
        return toUserDto(updated);
    }

    async deleteUser(userId: string): Promise<boolean> {
        const user = await this.repository.findById(userId);
        if (!user) {
            return false;
        }
        await this.repository.delete(user);
        return true;
    }

    async authenticate(email: string, password: string): Promise<User | null> {
        const user = await this.repository.findByEmail(email);
        if (user && await bcrypt.compare(password, user.passwordHash)) {
            return user;
        }
        return null;
    }
}
```

### 6. Controller Layer (Express)

```typescript
// src/controller/UserController.ts
import { Router, Request, Response, NextFunction } from "express";
import { z } from "zod";
import { IUserService } from "../service/UserService";
import { jwtRequired } from "../middleware/auth";
import { validate } from "../middleware/validate";

const createUserSchema = z.object({
    name: z.string().min(1).max(255),
    email: z.string().email(),
    password: z.string().min(8),
});

const updateUserSchema = z.object({
    name: z.string().min(1).max(255).optional(),
    email: z.string().email().optional(),
});

export function createUserController(userService: IUserService): Router {
    const router = Router();

    router.get(
        "/:userId",
        jwtRequired,
        async (req: Request, res: Response, next: NextFunction) => {
            try {
                const user = await userService.getUser(req.params.userId);
                if (!user) {
                    return res.status(404).json({ error: "User not found" });
                }
                res.json(user);
            } catch (error) {
                next(error);
            }
        }
    );

    router.get(
        "/",
        jwtRequired,
        async (req: Request, res: Response, next: NextFunction) => {
            try {
                const page = parseInt(req.query.page as string) || 0;
                const size = parseInt(req.query.size as string) || 10;

                const result = await userService.getUsers(page, size);

                res.json({
                    data: result.data,
                    page,
                    size,
                    total: result.total,
                });
            } catch (error) {
                next(error);
            }
        }
    );

    router.post(
        "/",
        jwtRequired,
        validate(createUserSchema),
        async (req: Request, res: Response, next: NextFunction) => {
            try {
                const user = await userService.createUser(req.body);
                res.status(201).json(user);
            } catch (error) {
                next(error);
            }
        }
    );

    router.put(
        "/:userId",
        jwtRequired,
        validate(updateUserSchema),
        async (req: Request, res: Response, next: NextFunction) => {
            try {
                const user = await userService.updateUser(req.params.userId, req.body);
                if (!user) {
                    return res.status(404).json({ error: "User not found" });
                }
                res.json(user);
            } catch (error) {
                next(error);
            }
        }
    );

    router.delete(
        "/:userId",
        jwtRequired,
        async (req: Request, res: Response, next: NextFunction) => {
            try {
                const deleted = await userService.deleteUser(req.params.userId);
                if (!deleted) {
                    return res.status(404).json({ error: "User not found" });
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

### 7. InversifyJS Dependency Injection

```typescript
// src/container/types.ts
export const TYPES = {
    // Repositories
    UserRepository: Symbol.for("UserRepository"),
    RefreshTokenRepository: Symbol.for("RefreshTokenRepository"),

    // Services
    UserService: Symbol.for("UserService"),
    AuthService: Symbol.for("AuthService"),
    TokenService: Symbol.for("TokenService"),

    // Infrastructure
    PrismaClient: Symbol.for("PrismaClient"),
    RedisClient: Symbol.for("RedisClient"),
    EventPublisher: Symbol.for("EventPublisher"),
};

// src/container/container.ts
import { Container } from "inversify";
import { PrismaClient } from "@prisma/client";
import { TYPES } from "./types";
import { UserRepository } from "../repository/UserRepository";
import { UserRepositoryImpl } from "../repository/UserRepositoryImpl";
import { IUserService, UserService } from "../service/UserService";
import { IAuthService, AuthService } from "../service/AuthService";

const container = new Container();

// Infrastructure
container.bind<PrismaClient>(TYPES.PrismaClient).toConstantValue(new PrismaClient());

// Repositories
container.bind<UserRepository>(TYPES.UserRepository).to(UserRepositoryImpl).inSingletonScope();

// Services
container.bind<IUserService>(TYPES.UserService).to(UserService).inSingletonScope();
container.bind<IAuthService>(TYPES.AuthService).to(AuthService).inSingletonScope();

export { container };
```

### 8. JWT Authentication Middleware

```typescript
// src/middleware/auth.ts
import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import { AppException, ErrorCode } from "../shared/exceptions/AppException";

const JWT_SECRET = process.env.JWT_SECRET || "your-secret-key";
const JWT_EXPIRES_IN = "24h";

export interface JwtPayload {
    sub: string;
    roles: string[];
    iat: number;
    exp: number;
}

export function createAccessToken(userId: string, roles: string[]): string {
    return jwt.sign(
        { sub: userId, roles },
        JWT_SECRET,
        { expiresIn: JWT_EXPIRES_IN }
    );
}

export function verifyToken(token: string): JwtPayload | null {
    try {
        return jwt.verify(token, JWT_SECRET) as JwtPayload;
    } catch {
        return null;
    }
}

export function jwtRequired(req: Request, res: Response, next: NextFunction): void {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
        throw new AppException(
            ErrorCode.UNAUTHORIZED,
            "Missing or invalid authorization header",
            401
        );
    }

    const token = authHeader.split(" ")[1];
    const payload = verifyToken(token);

    if (!payload) {
        throw new AppException(
            ErrorCode.UNAUTHORIZED,
            "Invalid or expired token",
            401
        );
    }

    (req as any).userId = payload.sub;
    (req as any).userRoles = payload.roles;

    next();
}

export function roleRequired(...requiredRoles: string[]) {
    return (req: Request, res: Response, next: NextFunction): void => {
        const userRoles = (req as any).userRoles || [];

        const hasRole = requiredRoles.some(role => userRoles.includes(role));
        if (!hasRole) {
            throw new AppException(
                ErrorCode.UNAUTHORIZED,
                "Insufficient permissions",
                403
            );
        }

        next();
    };
}
```

### 9. Database Migration with Prisma

```bash
# Create new migration
npx prisma migrate dev --name add_users_table

# Apply migrations to production
npx prisma migrate deploy

# Generate Prisma Client
npx prisma generate

# Reset database (development only)
npx prisma migrate reset
```

### 10. Testing with Vitest

```typescript
// tests/service/UserService.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { UserService } from "../../src/service/UserService";
import { UserRepository } from "../../src/repository/UserRepository";
import { User, SyncStatus } from "../../src/model/User";

describe("UserService", () => {
    let userService: UserService;
    let mockRepository: UserRepository;

    beforeEach(() => {
        mockRepository = {
            findById: vi.fn(),
            findByEmail: vi.fn(),
            findAll: vi.fn(),
            findPendingSync: vi.fn(),
            save: vi.fn(),
            update: vi.fn(),
            delete: vi.fn(),
        };
        userService = new UserService(mockRepository);
    });

    describe("getUser", () => {
        it("should return user when found", async () => {
            const mockUser: User = {
                id: "123",
                name: "John Doe",
                email: "john@example.com",
                passwordHash: "hash",
                syncStatus: SyncStatus.SYNCED,
                createdAt: new Date(),
                updatedAt: new Date(),
            };
            vi.mocked(mockRepository.findById).mockResolvedValue(mockUser);

            const result = await userService.getUser("123");

            expect(result).not.toBeNull();
            expect(result?.id).toBe("123");
            expect(mockRepository.findById).toHaveBeenCalledWith("123");
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
            vi.mocked(mockRepository.save).mockImplementation(async (user) => ({
                ...user,
                id: "new-id",
                createdAt: new Date(),
                updatedAt: new Date(),
            } as User));

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
            vi.mocked(mockRepository.findByEmail).mockResolvedValue({
                id: "existing",
                email: "john@example.com",
            } as User);

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

## API Wiring Verification Guide

### 🚨 The API Wiring Blind Spot

Express Controllers often call Service methods that may not exist:

```typescript
// src/controller/SettingsController.ts
router.get("/account-info", jwtRequired, async (req, res) => {
    const data = await settingsService.getAccountInfo();  // ⚠️ Does this method exist?
    res.json(data);
});

router.post("/change-password", jwtRequired, async (req, res) => {
    await settingsService.changePassword(req.body);  // ⚠️ Is this implemented?
    res.status(204).send();
});
```

**Problem**: If the Service class doesn't have the method, TypeScript catches it at compile time, but if using `any` types, it fails at runtime!

### Detection Patterns

```bash
# Find methods called on Service classes in Controllers
grep -roh "this\.\w*Service\.\w*(" src/controller/*.ts | sort -u

# Find methods defined in Service classes
grep -rh "async \w*(" src/service/*.ts | grep -oE "async \w+\(" | sort -u

# Find unimplemented methods
grep -rn "throw new Error.*NotImplemented\|// TODO" src/service/*.ts

# Compare: Every Service method called in Controller MUST exist and be implemented
```

### Correct Wiring Example

```typescript
// src/controller/SettingsController.ts (calls Service methods)
router.get("/account-info", jwtRequired, async (req, res) => {
    const data = await settingsService.getAccountInfo((req as any).userId);  // ✅ Method exists
    res.json(data);
});

router.post("/change-password", jwtRequired, async (req, res) => {
    await settingsService.changePassword(
        (req as any).userId,
        req.body.currentPassword,
        req.body.newPassword
    );  // ✅ Method exists
    res.status(204).send();
});

// src/service/SettingsService.ts (fully implemented)
@injectable()
export class SettingsService implements ISettingsService {
    constructor(
        @inject(TYPES.UserRepository) private readonly userRepository: UserRepository
    ) {}

    async getAccountInfo(userId: string): Promise<UserDto> {  // ✅ Implemented
        const user = await this.userRepository.findById(userId);
        if (!user) {
            throw AppException.notFound("User not found");
        }
        return toUserDto(user);
    }

    async changePassword(
        userId: string,
        currentPassword: string,
        newPassword: string
    ): Promise<void> {  // ✅ Implemented
        const user = await this.userRepository.findById(userId);
        if (!user) {
            throw AppException.notFound("User not found");
        }
        if (!await bcrypt.compare(currentPassword, user.passwordHash)) {
            throw AppException.validation("Invalid current password", {});
        }
        user.passwordHash = await bcrypt.hash(newPassword, 10);
        await this.userRepository.update(user);
    }
}
```

## Code Review Checklist

### Required Items
- [ ] Follow Clean Architecture layering
- [ ] gRPC service implemented for internal communication
- [ ] Repository pattern properly implemented
- [ ] JWT authentication complete
- [ ] Input validation with Zod
- [ ] 🚨 ALL Controller Service method calls have corresponding Service implementations
- [ ] 🚨 ALL gRPC proto methods have servicer implementations
- [ ] 🚨 ALL Service→Repository method calls exist in Repository classes
- [ ] 🚨 ALL dependencies registered in InversifyJS container

### Performance Checks
- [ ] Use gRPC for internal communication (1.80x faster)
- [ ] Database queries optimized with indexes
- [ ] Connection pooling configured
- [ ] Caching strategy implemented with Redis

### Security Checks
- [ ] JWT token validation
- [ ] Role-based access control
- [ ] Input validation complete
- [ ] Password hashing with bcrypt
- [ ] No hardcoded secrets

### Code Quality
- [ ] TypeScript strict mode enabled
- [ ] ESLint passing
- [ ] 538+ tests passing (90%+ coverage)
- [ ] No `any` types without justification

## Common Issues

### gRPC Connection Issues
1. Check protobuf compilation
2. Verify service registration
3. Ensure proper error handling

### Database Issues
1. Run Prisma migrations
2. Check connection pool settings
3. Review query performance

### Testing Issues
1. Use Vitest fixtures properly
2. Mock external dependencies
3. Test edge cases

### DI Issues
1. Check `@injectable()` decorator
2. Verify `container.bind()` calls
3. Check Symbol tokens match

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| Node.js | 22+ |
| TypeScript | 5.7+ |
| Express.js | 5.x |
| Prisma | 6.x |
| InversifyJS | 7.x |
| gRPC | 1.12+ |
| Vitest | 2.x |
| Zod | 3.x |
| MySQL | 8.0+ |
| Redis | 7.0+ |
