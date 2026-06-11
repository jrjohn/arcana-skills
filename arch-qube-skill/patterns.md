# Architecture Qube — Patterns Enforced

The patterns arch-qube checks, with ✅ correct vs ❌ violating code. These are the *target* states — when a rule FAILs, refactor toward the ✅ form. Examples are framework-neutral; the matching `<lang>-developer-skill` has language-exact versions.

---

## Pattern 1 — Layer Direction (rule #1, critical)

Imports flow **inward only**: `presentation → domain → data`. The domain layer never imports presentation or framework code.

```text
✅  presentation/UserView      → domain/GetUserUseCase     → data/UserRepositoryImpl
❌  domain/GetUserUseCase      → presentation/UserView      (upward import — FAIL)
❌  domain/UserUseCase         → org.springframework.*       (framework leak into domain — FAIL)
```

**Fix an upward import** by inverting it: declare an interface in the inner layer, implement it in the outer layer, and wire via DI.

---

## Pattern 2 — Interface / Impl (rules #2 #3 #4)

```text
domain/
  repository/
    UserRepository            # interface (imported everywhere)
    impl/
      UserRepositoryImpl      # ✅ colocated in impl/, named *Impl
```

- ✅ Only the **DI container** imports `UserRepositoryImpl` (#3).
- ❌ A Service importing `UserRepositoryImpl` directly → FAIL #3. Import `UserRepository` instead.
- ❌ Impl named `UserRepoConcrete` → FAIL #4. Rename to `UserRepositoryImpl`.

---

## Pattern 3 — No Business Logic in Boundary (rule #6) + DTO/Entity Separation (#5)

```java
// ❌ business logic + entity leak in the Controller
@GetMapping("/users/{id}")
User get(@PathVariable Long id) {
    User u = repo.findById(id);                 // boundary touching data
    if (u.getAge() > 18 && u.isActive()) { ... }// domain logic in boundary  (#6 FAIL)
    return u;                                    // Entity crosses the API   (#5 FAIL)
}

// ✅ thin Controller, DTO out, logic in Service
@GetMapping("/users/{id}")
UserDto get(@PathVariable Long id) {
    return userService.getEligibleUser(id);      // logic in Service, returns DTO
}
```

---

## Pattern 4 — MVVM Input / Output / Effect (rules #9 #10 #11 #12)

Client ViewModels expose three explicit segments; the View binds **Output** only and emits **Input** only.

```text
ViewModel
  Input   : intents from the View (LoadUser, Refresh, Submit)
  Output  : observable state the View renders (UserState, Loading, Error)
  Effect  : one-shot side effects (Navigate, Toast, Dialog)
```

```text
✅  View --Input--> ViewModel --Output--> View        (unidirectional, #11)
❌  View ----------> Service                            (#12 FAIL — View calls Service)
❌  ViewModel mutates View directly                     (#11 FAIL — back-channel)
```

**Fix #12:** the View never calls a Service/UseCase; it sends an Input; the ViewModel calls the UseCase and emits Output.

---

## Pattern 5 — Backend Layer Chain (rules #16–#21)

```text
Controller → Service → Repository → DAO        # the only legal direction (#16)
```

```java
// ❌ Service reaching the DB directly (#17 FAIL) ; Controller using DAO (#18 FAIL)
class OrderService { @Autowired EntityManager em;  /* raw query */ }
class OrderController { @Autowired OrderDao dao; }

// ✅ each layer talks only to the next
class OrderController { private final OrderService service; }     // → Service
class OrderService    { private final OrderRepository repo;       // → Repository
                        @Transactional void place(...) { ... } }  // tx at Service (#19)
class OrderRepositoryImpl { private final OrderDao dao; }         // → DAO
```

- ❌ `@Transactional` on a Controller or DAO → FAIL #19 (must be at Service).
- ❌ Repository importing/calling a Service → FAIL #21 (upward call).
- ✅ Controller request/response are **DTOs** (#20), mapped to/from Entities in the Service.

---

## Pattern 6 — Defense-in-Depth Security (#7) · Cache (#13) · Offline-First (#15)

- **#7:** validate/authorize at more than one layer (edge filter *and* Service guard), never trust a single gate.
- **#13:** the 4-layer progressive cache cascade (memory → local DB → network) must actually be wired, not stubbed.
- **#15:** local store is the source of truth; reads work offline; writes queue and sync on reconnect.

These three are **AI-checked** — AST cannot tell a real cascade from a placeholder, so Stage 2 reads the code semantically. If one FAILs, the fix is to *implement the behavior*, not rename symbols.

---

## How a fix maps back to a green scan

1. Read the failing rule id from the report → look it up in `reference.md`.
2. Identify the layer it guards (common / client / backend) → find the ✅ form above.
3. Refactor toward the ✅ form (move logic, invert an import, add the missing layer).
4. Re-run `arch-qube scan ... --no-ai` until AST criticals are PASS, then a full AI pass.
5. Critical at 100% + score ≥ threshold → exit `0`.
