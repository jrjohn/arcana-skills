# Service Layer Pattern

## Overview

The Service Layer pattern provides business logic orchestration between Controllers and Repositories in Python/Flask.

## Service Class Template

```python
from typing import Optional, List
from dataclasses import dataclass
from app.repository import UserRepository
from app.model import User
from app.exception import AppException, ErrorCode

class UserService:
    def __init__(self, user_repository: UserRepository):
        self._repository = user_repository

    def find_by_id(self, user_id: str) -> Optional[User]:
        return self._repository.find_by_id(user_id)

    def find_all(self, page: int = 1, size: int = 20) -> List[User]:
        return self._repository.find_all(page=page, size=size)

    def create(self, request: CreateUserRequest) -> User:
        # Validation
        if self._repository.exists_by_email(request.email):
            raise AppException(ErrorCode.CONFLICT, "Email already exists")

        user = User(
            id=str(uuid4()),
            email=request.email,
            name=request.name,
            created_at=datetime.utcnow()
        )
        return self._repository.save(user)

    def update(self, user_id: str, request: UpdateUserRequest) -> User:
        user = self._repository.find_by_id(user_id)
        if not user:
            raise AppException(ErrorCode.NOT_FOUND, "User not found")

        if request.name:
            user.name = request.name
        user.updated_at = datetime.utcnow()

        return self._repository.save(user)

    def delete(self, user_id: str) -> None:
        if not self._repository.exists_by_id(user_id):
            raise AppException(ErrorCode.NOT_FOUND, "User not found")
        self._repository.delete(user_id)
```

## Key Principles

1. **Dependency Injection** - Repository injected via constructor
2. **Validation** - Business rules validated in service
3. **Exception Handling** - Throw domain-specific exceptions
4. **Logging** - Log important operations

## Testing

```python
def test_create_user_when_email_exists_raises_conflict():
    mock_repo = Mock(spec=UserRepository)
    mock_repo.exists_by_email.return_value = True
    service = UserService(mock_repo)

    with pytest.raises(AppException) as exc:
        service.create(CreateUserRequest(email="test@test.com"))

    assert exc.value.error_code == ErrorCode.CONFLICT
```
