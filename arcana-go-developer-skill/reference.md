# Go Developer Skill - Technical Reference

## Table of Contents
1. [Configuration (Viper)](#configuration-viper)
2. [Deployment Modes](#deployment-modes)
3. [API Endpoints](#api-endpoints)
4. [gRPC Service Definitions](#grpc-service-definitions)
5. [Environment Variables](#environment-variables)
6. [Docker/K8s Manifests](#dockerk8s-manifests)
7. [Database Configuration](#database-configuration)

---

## Configuration (Viper)

### Configuration Loader

```go
// internal/config/config.go
package config

import (
    "fmt"
    "strings"

    "github.com/spf13/viper"
)

type Config struct {
    Server   ServerConfig   `mapstructure:"server"`
    Database DatabaseConfig `mapstructure:"database"`
    Redis    RedisConfig    `mapstructure:"redis"`
    JWT      JWTConfig      `mapstructure:"jwt"`
    GRPC     GRPCConfig     `mapstructure:"grpc"`
    Log      LogConfig      `mapstructure:"log"`
}

type ServerConfig struct {
    Port         int    `mapstructure:"port"`
    Mode         string `mapstructure:"mode"`         // monolithic, layered, microservice, hybrid, serverless
    ReadTimeout  int    `mapstructure:"readTimeout"`   // seconds
    WriteTimeout int    `mapstructure:"writeTimeout"`  // seconds
}

type DatabaseConfig struct {
    Type         string `mapstructure:"type"`         // mysql, postgres, mongo
    Host         string `mapstructure:"host"`
    Port         int    `mapstructure:"port"`
    Name         string `mapstructure:"name"`
    User         string `mapstructure:"user"`
    Password     string `mapstructure:"password"`
    MaxIdleConns int    `mapstructure:"maxIdleConns"`
    MaxOpenConns int    `mapstructure:"maxOpenConns"`
    MaxLifetime  int    `mapstructure:"maxLifetime"`  // minutes
    SSLMode      string `mapstructure:"sslMode"`
}

type RedisConfig struct {
    Host     string `mapstructure:"host"`
    Port     int    `mapstructure:"port"`
    Password string `mapstructure:"password"`
    DB       int    `mapstructure:"db"`
    PoolSize int    `mapstructure:"poolSize"`
}

type JWTConfig struct {
    Secret    string `mapstructure:"secret"`
    ExpiresIn int    `mapstructure:"expiresIn"` // hours
}

type GRPCConfig struct {
    Port     int    `mapstructure:"port"`
    TLSCert  string `mapstructure:"tlsCert"`
    TLSKey   string `mapstructure:"tlsKey"`
    Enabled  bool   `mapstructure:"enabled"`
}

type LogConfig struct {
    Level  string `mapstructure:"level"`  // debug, info, warn, error
    Format string `mapstructure:"format"` // json, text
    Output string `mapstructure:"output"` // stdout, file
    File   string `mapstructure:"file"`
}

func NewConfig() (*Config, error) {
    viper.SetConfigName("config")
    viper.SetConfigType("yaml")
    viper.AddConfigPath("./config")
    viper.AddConfigPath(".")

    // Environment variable overrides
    viper.SetEnvPrefix("ARCANA")
    viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
    viper.AutomaticEnv()

    // Defaults
    viper.SetDefault("server.port", 8080)
    viper.SetDefault("server.mode", "monolithic")
    viper.SetDefault("server.readTimeout", 30)
    viper.SetDefault("server.writeTimeout", 30)
    viper.SetDefault("database.type", "mysql")
    viper.SetDefault("database.maxIdleConns", 10)
    viper.SetDefault("database.maxOpenConns", 100)
    viper.SetDefault("database.maxLifetime", 60)
    viper.SetDefault("redis.host", "localhost")
    viper.SetDefault("redis.port", 6379)
    viper.SetDefault("redis.db", 0)
    viper.SetDefault("redis.poolSize", 10)
    viper.SetDefault("jwt.expiresIn", 24)
    viper.SetDefault("grpc.port", 50051)
    viper.SetDefault("grpc.enabled", true)
    viper.SetDefault("log.level", "info")
    viper.SetDefault("log.format", "json")
    viper.SetDefault("log.output", "stdout")

    if err := viper.ReadInConfig(); err != nil {
        if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
            return nil, fmt.Errorf("failed to read config: %w", err)
        }
    }

    var cfg Config
    if err := viper.Unmarshal(&cfg); err != nil {
        return nil, fmt.Errorf("failed to unmarshal config: %w", err)
    }

    return &cfg, nil
}
```

### YAML Configuration File

```yaml
# config/config.yaml
server:
  port: 8080
  mode: monolithic       # monolithic | layered | microservice | hybrid | serverless
  readTimeout: 30
  writeTimeout: 30

database:
  type: mysql            # mysql | postgres | mongo
  host: localhost
  port: 3306
  name: arcana
  user: root
  password: ""
  maxIdleConns: 10
  maxOpenConns: 100
  maxLifetime: 60
  sslMode: disable

redis:
  host: localhost
  port: 6379
  password: ""
  db: 0
  poolSize: 10

jwt:
  secret: your-jwt-secret-key
  expiresIn: 24          # hours

grpc:
  port: 50051
  enabled: true
  tlsCert: ""
  tlsKey: ""

log:
  level: info            # debug | info | warn | error
  format: json           # json | text
  output: stdout         # stdout | file
  file: ""
```

### Environment-Specific Overrides

```yaml
# config/config.dev.yaml
server:
  mode: monolithic
log:
  level: debug
  format: text

# config/config.prod.yaml
server:
  mode: microservice
  readTimeout: 10
  writeTimeout: 10
database:
  maxOpenConns: 200
  sslMode: require
redis:
  poolSize: 50
log:
  level: info
  format: json
```

---

## Deployment Modes

### Mode Details

| Mode | Process | Communication | Scale | Memory | Startup |
|------|---------|---------------|-------|--------|---------|
| Monolithic | 1 binary | Direct calls | Vertical | ~50MB | ~100ms |
| Layered | 3 containers | gRPC | Per layer | ~150MB | ~300ms |
| Microservices | N containers | gRPC + MQ | Per service | ~50MB/svc | ~100ms/svc |
| Hybrid | Mixed | gRPC + REST | Mixed | Variable | Variable |
| Serverless | Functions | HTTP triggers | Auto | ~20MB | ~50ms |

### Monolithic Mode

```yaml
# config/config.yaml
server:
  mode: monolithic
  port: 8080
grpc:
  enabled: false
```

### Layered Mode

```yaml
# Controller layer
server:
  mode: layered
  port: 8080
grpc:
  port: 50051

# Service layer
server:
  mode: layered
  port: 0       # no HTTP
grpc:
  port: 50052

# Repository layer
server:
  mode: layered
  port: 0       # no HTTP
grpc:
  port: 50053
```

### Microservices Mode

```yaml
# User service
server:
  mode: microservice
  port: 8081
grpc:
  port: 50061

# Product service
server:
  mode: microservice
  port: 8082
grpc:
  port: 50062

# Auth service
server:
  mode: microservice
  port: 8083
grpc:
  port: 50063
```

---

## API Endpoints

### REST API Reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/v1/auth/login | No | User login |
| POST | /api/v1/auth/register | No | User registration |
| POST | /api/v1/auth/refresh | No | Refresh access token |
| POST | /api/v1/auth/logout | No | Logout (revoke refresh token) |
| POST | /api/v1/auth/logout-all | JWT | Logout all sessions |
| POST | /api/v1/auth/change-password | JWT | Change password |
| GET | /api/v1/auth/me | JWT | Get current user |
| GET | /api/v1/users | JWT | List users (paginated) |
| GET | /api/v1/users/:id | JWT | Get user by ID |
| POST | /api/v1/users | JWT | Create user |
| PUT | /api/v1/users/:id | JWT | Update user |
| DELETE | /api/v1/users/:id | JWT | Delete user |
| GET | /api/v1/products | No | List products (paginated) |
| GET | /api/v1/products/search | No | Search products |
| GET | /api/v1/products/:id | No | Get product by ID |
| POST | /api/v1/products | JWT+Admin | Create product |
| PUT | /api/v1/products/:id | JWT+Admin | Update product |
| PATCH | /api/v1/products/:id/stock | JWT+Admin | Update stock |
| DELETE | /api/v1/products/:id | JWT+Admin | Delete product |
| GET | /health | No | Health check |
| GET | /ready | No | Readiness check |
| GET | /metrics | No | Prometheus metrics |

### Common Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 0 | Page number (0-indexed) |
| size | int | 10 | Page size |
| sort | string | created_at | Sort field |
| order | string | desc | Sort order (asc/desc) |
| q | string | | Search query |

### Standard Response Format

```json
{
    "data": {},
    "page": 0,
    "size": 10,
    "total": 100
}
```

### Standard Error Response

```json
{
    "code": "NOT_FOUND",
    "message": "User not found",
    "details": {},
    "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## gRPC Service Definitions

### User Service Proto

```protobuf
// api/proto/user.proto
syntax = "proto3";

package arcana.user.v1;

option go_package = "arcana-cloud-go/api/proto/user/v1";

service UserService {
    rpc GetUser(GetUserRequest) returns (UserResponse);
    rpc ListUsers(ListUsersRequest) returns (ListUsersResponse);
    rpc CreateUser(CreateUserRequest) returns (UserResponse);
    rpc UpdateUser(UpdateUserRequest) returns (UserResponse);
    rpc DeleteUser(DeleteUserRequest) returns (DeleteUserResponse);
}

message GetUserRequest {
    string id = 1;
}

message ListUsersRequest {
    int32 page = 1;
    int32 size = 2;
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
    string created_at = 4;
    string updated_at = 5;
}

message ListUsersResponse {
    repeated UserResponse users = 1;
    int32 total = 2;
    int32 page = 3;
    int32 size = 4;
    bool has_next = 5;
}

message DeleteUserResponse {
    bool success = 1;
}
```

### Product Service Proto

```protobuf
// api/proto/product.proto
syntax = "proto3";

package arcana.product.v1;

option go_package = "arcana-cloud-go/api/proto/product/v1";

service ProductService {
    rpc GetProduct(GetProductRequest) returns (ProductResponse);
    rpc ListProducts(ListProductsRequest) returns (ListProductsResponse);
    rpc CreateProduct(CreateProductRequest) returns (ProductResponse);
    rpc UpdateProduct(UpdateProductRequest) returns (ProductResponse);
    rpc UpdateStock(UpdateStockRequest) returns (ProductResponse);
    rpc DeleteProduct(DeleteProductRequest) returns (DeleteProductResponse);
}

message GetProductRequest {
    string id = 1;
}

message ListProductsRequest {
    int32 page = 1;
    int32 size = 2;
    string category = 3;
    string status = 4;
}

message CreateProductRequest {
    string name = 1;
    string description = 2;
    double price = 3;
    int32 stock = 4;
    string category = 5;
}

message UpdateProductRequest {
    string id = 1;
    optional string name = 2;
    optional string description = 3;
    optional double price = 4;
    optional int32 stock = 5;
    optional string category = 6;
    optional string status = 7;
}

message UpdateStockRequest {
    string product_id = 1;
    int32 quantity_change = 2;
}

message DeleteProductRequest {
    string id = 1;
}

message ProductResponse {
    string id = 1;
    string name = 2;
    string description = 3;
    double price = 4;
    int32 stock = 5;
    string category = 6;
    string status = 7;
    string created_at = 8;
    string updated_at = 9;
}

message ListProductsResponse {
    repeated ProductResponse products = 1;
    int32 total = 2;
    int32 page = 3;
    int32 size = 4;
    bool has_next = 5;
}

message DeleteProductResponse {
    bool success = 1;
}
```

### Protobuf Compilation

```bash
# Install protoc plugins
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# Compile protobuf files
protoc --go_out=. --go_opt=paths=source_relative \
       --go-grpc_out=. --go-grpc_opt=paths=source_relative \
       api/proto/*.proto

# Or use buf
buf generate
```

---

## Environment Variables

### Required Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| ARCANA_SERVER_PORT | HTTP server port | 8080 | 8080 |
| ARCANA_SERVER_MODE | Deployment mode | monolithic | layered |
| ARCANA_DATABASE_TYPE | Database type | mysql | postgres |
| ARCANA_DATABASE_HOST | Database host | localhost | db.example.com |
| ARCANA_DATABASE_PORT | Database port | 3306 | 5432 |
| ARCANA_DATABASE_NAME | Database name | arcana | myapp |
| ARCANA_DATABASE_USER | Database user | root | admin |
| ARCANA_DATABASE_PASSWORD | Database password | | secret |
| ARCANA_REDIS_HOST | Redis host | localhost | redis.example.com |
| ARCANA_REDIS_PORT | Redis port | 6379 | 6379 |
| ARCANA_REDIS_PASSWORD | Redis password | | secret |
| ARCANA_JWT_SECRET | JWT signing secret | | my-secret-key |
| ARCANA_JWT_EXPIRESIN | JWT expiry (hours) | 24 | 48 |
| ARCANA_GRPC_PORT | gRPC server port | 50051 | 50051 |
| ARCANA_GRPC_ENABLED | Enable gRPC | true | false |
| ARCANA_LOG_LEVEL | Log level | info | debug |

### .env.example

```bash
# Server
ARCANA_SERVER_PORT=8080
ARCANA_SERVER_MODE=monolithic

# Database
ARCANA_DATABASE_TYPE=mysql
ARCANA_DATABASE_HOST=localhost
ARCANA_DATABASE_PORT=3306
ARCANA_DATABASE_NAME=arcana
ARCANA_DATABASE_USER=root
ARCANA_DATABASE_PASSWORD=

# Redis
ARCANA_REDIS_HOST=localhost
ARCANA_REDIS_PORT=6379
ARCANA_REDIS_PASSWORD=

# JWT
ARCANA_JWT_SECRET=change-this-in-production
ARCANA_JWT_EXPIRESIN=24

# gRPC
ARCANA_GRPC_PORT=50051
ARCANA_GRPC_ENABLED=true

# Logging
ARCANA_LOG_LEVEL=info
ARCANA_LOG_FORMAT=json
```

---

## Docker/K8s Manifests

### Dockerfile

```dockerfile
# Build stage
FROM golang:1.23-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /server ./cmd/server/

# Production stage
FROM alpine:3.19

RUN apk --no-cache add ca-certificates tzdata

WORKDIR /app

COPY --from=builder /server .
COPY config/ ./config/

EXPOSE 8080 50051

ENTRYPOINT ["./server"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
      - "50051:50051"
    environment:
      - ARCANA_DATABASE_HOST=mysql
      - ARCANA_REDIS_HOST=redis
      - ARCANA_JWT_SECRET=dev-secret
    depends_on:
      - mysql
      - redis

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: arcana
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:7.0-alpine
    ports:
      - "6379:6379"

volumes:
  mysql_data:
```

### Kubernetes Deployment

```yaml
# deployment/kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arcana-cloud-go
  labels:
    app: arcana-cloud-go
spec:
  replicas: 3
  selector:
    matchLabels:
      app: arcana-cloud-go
  template:
    metadata:
      labels:
        app: arcana-cloud-go
    spec:
      containers:
        - name: arcana-cloud-go
          image: arcana-cloud-go:latest
          ports:
            - containerPort: 8080
              name: http
            - containerPort: 50051
              name: grpc
          env:
            - name: ARCANA_SERVER_MODE
              value: "microservice"
            - name: ARCANA_DATABASE_HOST
              valueFrom:
                secretKeyRef:
                  name: arcana-secrets
                  key: database-host
            - name: ARCANA_JWT_SECRET
              valueFrom:
                secretKeyRef:
                  name: arcana-secrets
                  key: jwt-secret
          resources:
            requests:
              cpu: 100m
              memory: 50Mi
            limits:
              cpu: 500m
              memory: 256Mi
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 3
            periodSeconds: 5
---
# deployment/kubernetes/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: arcana-cloud-go
spec:
  selector:
    app: arcana-cloud-go
  ports:
    - name: http
      port: 80
      targetPort: 8080
    - name: grpc
      port: 50051
      targetPort: 50051
  type: ClusterIP
---
# deployment/kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: arcana-cloud-go
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: arcana-cloud-go
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

## Database Configuration

### GORM Database Initialization

```go
// internal/config/database.go
package config

import (
    "fmt"
    "time"

    "gorm.io/driver/mysql"
    "gorm.io/driver/postgres"
    "gorm.io/gorm"
    "gorm.io/gorm/logger"
)

func InitDatabase(cfg *Config) (*gorm.DB, error) {
    var dialector gorm.Dialector

    switch cfg.Database.Type {
    case "mysql":
        dsn := fmt.Sprintf("%s:%s@tcp(%s:%d)/%s?charset=utf8mb4&parseTime=True&loc=Local",
            cfg.Database.User, cfg.Database.Password,
            cfg.Database.Host, cfg.Database.Port,
            cfg.Database.Name,
        )
        dialector = mysql.Open(dsn)

    case "postgres":
        dsn := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
            cfg.Database.Host, cfg.Database.Port,
            cfg.Database.User, cfg.Database.Password,
            cfg.Database.Name, cfg.Database.SSLMode,
        )
        dialector = postgres.Open(dsn)

    default:
        return nil, fmt.Errorf("unsupported database type: %s", cfg.Database.Type)
    }

    db, err := gorm.Open(dialector, &gorm.Config{
        Logger: logger.Default.LogMode(logger.Info),
    })
    if err != nil {
        return nil, fmt.Errorf("failed to connect database: %w", err)
    }

    sqlDB, err := db.DB()
    if err != nil {
        return nil, fmt.Errorf("failed to get sql.DB: %w", err)
    }

    sqlDB.SetMaxIdleConns(cfg.Database.MaxIdleConns)
    sqlDB.SetMaxOpenConns(cfg.Database.MaxOpenConns)
    sqlDB.SetConnMaxLifetime(time.Duration(cfg.Database.MaxLifetime) * time.Minute)

    return db, nil
}
```

### Connection String Formats

| Database | DSN Format |
|----------|------------|
| MySQL | `user:pass@tcp(host:3306)/dbname?charset=utf8mb4&parseTime=True` |
| PostgreSQL | `host=localhost port=5432 user=admin password=pass dbname=arcana sslmode=disable` |
| MongoDB | `mongodb://user:pass@host:27017/arcana?authSource=admin` |
| Redis | `redis://:password@host:6379/0` |
