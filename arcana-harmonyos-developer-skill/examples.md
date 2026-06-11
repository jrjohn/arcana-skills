# HarmonyOS Development Examples

Practical development examples based on Arcana HarmonyOS architecture. All code uses ArkTS strict mode (no any, no unknown, no spread operators, no computed properties).

## Table of Contents

1. [Complete Feature Implementation Examples](#complete-feature-implementation-examples)
2. [Common Problem Solutions](#common-problem-solutions)
3. [Testing Examples](#testing-examples)
4. [Offline-First Examples](#offline-first-examples)

---

## Complete Feature Implementation Examples

### Example 1: User Login Feature

Complete login feature with form validation, error handling, and offline token storage.

#### Domain Layer (PURE)

```typescript
// domain/models/AuthResult.ets
export class AuthResult {
  readonly user: User
  readonly token: string

  constructor(user: User, token: string) {
    this.user = user
    this.token = token
  }
}

// domain/models/User.ets
export class User {
  readonly id: string
  readonly name: string
  readonly email: string
  readonly avatarUrl: string | undefined
  readonly createdAt: number

  constructor(
    id: string,
    name: string,
    email: string,
    avatarUrl: string | undefined,
    createdAt: number
  ) {
    this.id = id
    this.name = name
    this.email = email
    this.avatarUrl = avatarUrl
    this.createdAt = createdAt
  }

  // Factory method for immutable update (no spread operator)
  withName(name: string): User {
    return new User(this.id, name, this.email, this.avatarUrl, this.createdAt)
  }

  withEmail(email: string): User {
    return new User(this.id, this.name, email, this.avatarUrl, this.createdAt)
  }
}

// domain/validators/AuthValidator.ets
export class AuthValidator {
  static validateEmail(email: string): Result<string, AppError> {
    if (email.length === 0) {
      return Result.failure(new AppError(AppError.VALIDATION, 'Email is required'))
    }
    const emailRegex = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/
    if (!emailRegex.test(email)) {
      return Result.failure(new AppError(AppError.VALIDATION, 'Invalid email format'))
    }
    return Result.success(email)
  }

  static validatePassword(password: string): Result<string, AppError> {
    if (password.length === 0) {
      return Result.failure(new AppError(AppError.VALIDATION, 'Password is required'))
    }
    if (password.length < 6) {
      return Result.failure(new AppError(AppError.VALIDATION, 'Password must be at least 6 characters'))
    }
    return Result.success(password)
  }
}

// domain/repository/AuthRepository.ets (INTERFACE ONLY)
export interface AuthRepository {
  login(email: string, password: string): Promise<Result<AuthResult, AppError>>
  logout(): Promise<Result<boolean, AppError>>
  isLoggedIn(): Promise<boolean>
  getCurrentUser(): Promise<Result<User, AppError>>
}
```

#### Data Layer

```typescript
// data/api/dto/LoginRequestDto.ets
export class LoginRequestDto {
  readonly email: string
  readonly password: string

  constructor(email: string, password: string) {
    this.email = email
    this.password = password
  }
}

// data/api/dto/LoginResponseDto.ets
export class LoginResponseDto {
  readonly userId: string
  readonly userName: string
  readonly userEmail: string
  readonly token: string
  readonly expiresAt: number

  constructor(
    userId: string,
    userName: string,
    userEmail: string,
    token: string,
    expiresAt: number
  ) {
    this.userId = userId
    this.userName = userName
    this.userEmail = userEmail
    this.token = token
    this.expiresAt = expiresAt
  }

  toDomain(): AuthResult {
    const user = new User(
      this.userId,
      this.userName,
      this.userEmail,
      undefined,
      Date.now()
    )
    return new AuthResult(user, this.token)
  }
}

// data/repository/AuthRepositoryImpl.ets
@injectable()
export class AuthRepositoryImpl implements AuthRepository {
  private apiService: AuthApiService
  private localSource: AuthLocalSource
  private securityService: SecurityService

  constructor(
    apiService: AuthApiService,
    localSource: AuthLocalSource,
    securityService: SecurityService
  ) {
    this.apiService = apiService
    this.localSource = localSource
    this.securityService = securityService
  }

  async login(email: string, password: string): Promise<Result<AuthResult, AppError>> {
    // Validate inputs first
    const emailResult = AuthValidator.validateEmail(email)
    if (emailResult.isFailure()) {
      return Result.failure(emailResult.getErrorOrNull() as AppError)
    }

    const passwordResult = AuthValidator.validatePassword(password)
    if (passwordResult.isFailure()) {
      return Result.failure(passwordResult.getErrorOrNull() as AppError)
    }

    // Call API
    const response = await this.apiService.login(new LoginRequestDto(email, password))
    if (response.isFailure()) {
      return Result.failure(response.getErrorOrNull() as AppError)
    }

    const authResult = (response.getOrNull() as LoginResponseDto).toDomain()

    // Store token securely via HUKS
    await this.securityService.encrypt(authResult.token)

    // Save user locally
    await this.localSource.saveUser(UserEntity.fromDomain(authResult.user))

    return Result.success(authResult)
  }

  async logout(): Promise<Result<boolean, AppError>> {
    await this.localSource.clearSession()
    return Result.success(true)
  }

  async isLoggedIn(): Promise<boolean> {
    const session = await this.localSource.getSession()
    return session !== undefined && session.expiresAt > Date.now()
  }

  async getCurrentUser(): Promise<Result<User, AppError>> {
    const entity = await this.localSource.getCurrentUser()
    if (entity === undefined) {
      return Result.failure(new AppError(AppError.NOT_FOUND, 'No user found'))
    }
    return Result.success(entity.toDomain())
  }
}
```

#### Presentation Layer

```typescript
// presentation/viewmodel/LoginViewModel.ets

// Input discriminated union
export class LoginInputType {
  static readonly UPDATE_EMAIL = 'UPDATE_EMAIL'
  static readonly UPDATE_PASSWORD = 'UPDATE_PASSWORD'
  static readonly TOGGLE_PASSWORD_VISIBILITY = 'TOGGLE_PASSWORD_VISIBILITY'
  static readonly SUBMIT = 'SUBMIT'
}

export class LoginInput {
  readonly type: string
  readonly payload: string | undefined

  private constructor(type: string, payload: string | undefined) {
    this.type = type
    this.payload = payload
  }

  static updateEmail(email: string): LoginInput {
    return new LoginInput(LoginInputType.UPDATE_EMAIL, email)
  }

  static updatePassword(password: string): LoginInput {
    return new LoginInput(LoginInputType.UPDATE_PASSWORD, password)
  }

  static togglePasswordVisibility(): LoginInput {
    return new LoginInput(LoginInputType.TOGGLE_PASSWORD_VISIBILITY, undefined)
  }

  static submit(): LoginInput {
    return new LoginInput(LoginInputType.SUBMIT, undefined)
  }
}

// Output with factory methods
export class LoginOutput {
  readonly email: string
  readonly password: string
  readonly isPasswordVisible: boolean
  readonly isLoading: boolean
  readonly emailError: string | undefined
  readonly passwordError: string | undefined
  readonly generalError: string | undefined

  private constructor(
    email: string,
    password: string,
    isPasswordVisible: boolean,
    isLoading: boolean,
    emailError: string | undefined,
    passwordError: string | undefined,
    generalError: string | undefined
  ) {
    this.email = email
    this.password = password
    this.isPasswordVisible = isPasswordVisible
    this.isLoading = isLoading
    this.emailError = emailError
    this.passwordError = passwordError
    this.generalError = generalError
  }

  static initial(): LoginOutput {
    return new LoginOutput('', '', false, false, undefined, undefined, undefined)
  }

  get isValid(): boolean {
    return this.email.length > 0 &&
           this.password.length >= 6 &&
           this.emailError === undefined &&
           this.passwordError === undefined
  }

  withEmail(email: string): LoginOutput {
    return new LoginOutput(email, this.password, this.isPasswordVisible, this.isLoading, this.emailError, this.passwordError, this.generalError)
  }

  withPassword(password: string): LoginOutput {
    return new LoginOutput(this.email, password, this.isPasswordVisible, this.isLoading, this.emailError, this.passwordError, this.generalError)
  }

  withPasswordVisible(visible: boolean): LoginOutput {
    return new LoginOutput(this.email, this.password, visible, this.isLoading, this.emailError, this.passwordError, this.generalError)
  }

  withLoading(loading: boolean): LoginOutput {
    return new LoginOutput(this.email, this.password, this.isPasswordVisible, loading, this.emailError, this.passwordError, this.generalError)
  }

  withEmailError(error: string | undefined): LoginOutput {
    return new LoginOutput(this.email, this.password, this.isPasswordVisible, this.isLoading, error, this.passwordError, this.generalError)
  }

  withPasswordError(error: string | undefined): LoginOutput {
    return new LoginOutput(this.email, this.password, this.isPasswordVisible, this.isLoading, this.emailError, error, this.generalError)
  }

  withGeneralError(error: string | undefined): LoginOutput {
    return new LoginOutput(this.email, this.password, this.isPasswordVisible, this.isLoading, this.emailError, this.passwordError, error)
  }
}

// Effect types
export class LoginEffectType {
  static readonly NAVIGATE_HOME = 'NAVIGATE_HOME'
  static readonly NAVIGATE_REGISTER = 'NAVIGATE_REGISTER'
  static readonly SHOW_ERROR = 'SHOW_ERROR'
}

export class LoginEffect {
  readonly type: string
  readonly payload: string | undefined

  private constructor(type: string, payload: string | undefined) {
    this.type = type
    this.payload = payload
  }

  static navigateHome(): LoginEffect {
    return new LoginEffect(LoginEffectType.NAVIGATE_HOME, undefined)
  }

  static navigateRegister(): LoginEffect {
    return new LoginEffect(LoginEffectType.NAVIGATE_REGISTER, undefined)
  }

  static showError(message: string): LoginEffect {
    return new LoginEffect(LoginEffectType.SHOW_ERROR, message)
  }
}

// ViewModel
@injectable()
export class LoginViewModel {
  private authRepository: AuthRepository
  private _output: LoginOutput = LoginOutput.initial()
  private _effectCallback: ((effect: LoginEffect) => void) | undefined = undefined
  private emailTouched: boolean = false
  private passwordTouched: boolean = false

  constructor(authRepository: AuthRepository) {
    this.authRepository = authRepository
  }

  get output(): LoginOutput {
    return this._output
  }

  setEffectCallback(callback: (effect: LoginEffect) => void): void {
    this._effectCallback = callback
  }

  onInput(input: LoginInput): void {
    switch (input.type) {
      case LoginInputType.UPDATE_EMAIL:
        this.updateEmail(input.payload as string)
        break
      case LoginInputType.UPDATE_PASSWORD:
        this.updatePassword(input.payload as string)
        break
      case LoginInputType.TOGGLE_PASSWORD_VISIBILITY:
        this._output = this._output.withPasswordVisible(!this._output.isPasswordVisible)
        break
      case LoginInputType.SUBMIT:
        this.submit()
        break
      default:
        break
    }
  }

  private updateEmail(email: string): void {
    this.emailTouched = true
    this._output = this._output.withEmail(email)

    const validation = AuthValidator.validateEmail(email)
    if (validation.isFailure()) {
      const error = validation.getErrorOrNull() as AppError
      this._output = this._output.withEmailError(error.message)
    } else {
      this._output = this._output.withEmailError(undefined)
    }
  }

  private updatePassword(password: string): void {
    this.passwordTouched = true
    this._output = this._output.withPassword(password)

    const validation = AuthValidator.validatePassword(password)
    if (validation.isFailure()) {
      const error = validation.getErrorOrNull() as AppError
      this._output = this._output.withPasswordError(error.message)
    } else {
      this._output = this._output.withPasswordError(undefined)
    }
  }

  private async submit(): Promise<void> {
    if (!this._output.isValid) {
      this.emailTouched = true
      this.passwordTouched = true
      this.updateEmail(this._output.email)
      this.updatePassword(this._output.password)
      return
    }

    this._output = this._output.withLoading(true).withGeneralError(undefined)

    const result = await this.authRepository.login(
      this._output.email,
      this._output.password
    )

    result.fold(
      (authResult: AuthResult) => {
        this._output = this._output.withLoading(false)
        this.emitEffect(LoginEffect.navigateHome())
      },
      (error: AppError) => {
        this._output = this._output.withLoading(false).withGeneralError(error.message)
        this.emitEffect(LoginEffect.showError(error.message))
      }
    )
  }

  private emitEffect(effect: LoginEffect): void {
    if (this._effectCallback !== undefined) {
      this._effectCallback(effect)
    }
  }
}
```

#### ArkUI Page

```typescript
// pages/LoginPage.ets
import { LoginViewModel, LoginInput, LoginOutput, LoginEffect, LoginEffectType } from '../presentation/viewmodel/LoginViewModel'
import { NavigationHelper } from '../core/navigation/NavigationHelper'
import { NavigationRoutes } from '../core/navigation/NavigationRoutes'
import { promptAction } from '@kit.ArkUI'

@Entry
@Component
struct LoginPage {
  @State private output: LoginOutput = LoginOutput.initial()
  private viewModel: LoginViewModel = AppContainer.resolve<LoginViewModel>(ServiceIdentifiers.LOGIN_VIEW_MODEL)

  aboutToAppear(): void {
    this.viewModel.setEffectCallback((effect: LoginEffect) => {
      this.handleEffect(effect)
    })
  }

  private handleEffect(effect: LoginEffect): void {
    switch (effect.type) {
      case LoginEffectType.NAVIGATE_HOME:
        NavigationHelper.replaceUrl(NavigationRoutes.HOME)
        break
      case LoginEffectType.NAVIGATE_REGISTER:
        NavigationHelper.pushUrl(NavigationRoutes.REGISTER, undefined)
        break
      case LoginEffectType.SHOW_ERROR:
        promptAction.showToast({
          message: effect.payload as string,
          duration: 2000
        })
        break
      default:
        break
    }
  }

  private handleInput(input: LoginInput): void {
    this.viewModel.onInput(input)
    this.output = this.viewModel.output
  }

  build() {
    Column() {
      // Title
      Text($r('app.string.login_title'))
        .fontSize(28)
        .fontWeight(FontWeight.Bold)
        .margin({ top: 80, bottom: 40 })

      // Email input
      TextInput({ placeholder: 'Email', text: this.output.email })
        .type(InputType.Email)
        .onChange((value: string) => {
          this.handleInput(LoginInput.updateEmail(value))
        })
        .width('90%')
        .margin({ bottom: 8 })

      if (this.output.emailError !== undefined) {
        Text(this.output.emailError)
          .fontSize(12)
          .fontColor(Color.Red)
          .width('90%')
          .margin({ bottom: 8 })
      }

      // Password input
      TextInput({ placeholder: 'Password', text: this.output.password })
        .type(this.output.isPasswordVisible ? InputType.Normal : InputType.Password)
        .onChange((value: string) => {
          this.handleInput(LoginInput.updatePassword(value))
        })
        .width('90%')
        .margin({ bottom: 8 })

      if (this.output.passwordError !== undefined) {
        Text(this.output.passwordError)
          .fontSize(12)
          .fontColor(Color.Red)
          .width('90%')
          .margin({ bottom: 8 })
      }

      // Toggle password visibility
      Row() {
        Toggle({ type: ToggleType.Checkbox, isOn: this.output.isPasswordVisible })
          .onChange((isOn: boolean) => {
            this.handleInput(LoginInput.togglePasswordVisibility())
          })
        Text($r('app.string.show_password'))
          .fontSize(14)
          .margin({ left: 8 })
      }
      .width('90%')
      .margin({ bottom: 24 })

      // General error
      if (this.output.generalError !== undefined) {
        Text(this.output.generalError)
          .fontSize(14)
          .fontColor(Color.Red)
          .width('90%')
          .margin({ bottom: 16 })
      }

      // Login button
      Button($r('app.string.sign_in'))
        .width('90%')
        .height(48)
        .enabled(!this.output.isLoading)
        .onClick(() => {
          this.handleInput(LoginInput.submit())
        })

      if (this.output.isLoading) {
        LoadingProgress()
          .width(24)
          .height(24)
          .margin({ top: 16 })
      }

      // Register link
      Text($r('app.string.no_account_register'))
        .fontSize(14)
        .fontColor(Color.Blue)
        .margin({ top: 24 })
        .onClick(() => {
          NavigationHelper.pushUrl(NavigationRoutes.REGISTER, undefined)
        })
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Start)
    .alignItems(HorizontalAlign.Center)
  }
}
```

---

### Example 2: User List with Search and Offline Support

```typescript
// presentation/viewmodel/UserListViewModel.ets

export class UserListInputType {
  static readonly LOAD = 'LOAD'
  static readonly REFRESH = 'REFRESH'
  static readonly SEARCH = 'SEARCH'
  static readonly SELECT_USER = 'SELECT_USER'
  static readonly RETRY = 'RETRY'
}

export class UserListInput {
  readonly type: string
  readonly payload: string | undefined

  private constructor(type: string, payload: string | undefined) {
    this.type = type
    this.payload = payload
  }

  static load(): UserListInput {
    return new UserListInput(UserListInputType.LOAD, undefined)
  }

  static refresh(): UserListInput {
    return new UserListInput(UserListInputType.REFRESH, undefined)
  }

  static search(query: string): UserListInput {
    return new UserListInput(UserListInputType.SEARCH, query)
  }

  static selectUser(id: string): UserListInput {
    return new UserListInput(UserListInputType.SELECT_USER, id)
  }

  static retry(): UserListInput {
    return new UserListInput(UserListInputType.RETRY, undefined)
  }
}

export class UserListOutput {
  readonly users: Array<User>
  readonly searchQuery: string
  readonly isLoading: boolean
  readonly isRefreshing: boolean
  readonly error: string | undefined

  private constructor(
    users: Array<User>,
    searchQuery: string,
    isLoading: boolean,
    isRefreshing: boolean,
    error: string | undefined
  ) {
    this.users = users
    this.searchQuery = searchQuery
    this.isLoading = isLoading
    this.isRefreshing = isRefreshing
    this.error = error
  }

  static initial(): UserListOutput {
    return new UserListOutput(new Array<User>(), '', false, false, undefined)
  }

  get isEmpty(): boolean {
    return this.users.length === 0 && !this.isLoading && this.error === undefined
  }

  withUsers(users: Array<User>): UserListOutput {
    return new UserListOutput(users, this.searchQuery, false, false, undefined)
  }

  withLoading(loading: boolean): UserListOutput {
    return new UserListOutput(this.users, this.searchQuery, loading, this.isRefreshing, loading ? undefined : this.error)
  }

  withRefreshing(refreshing: boolean): UserListOutput {
    return new UserListOutput(this.users, this.searchQuery, this.isLoading, refreshing, this.error)
  }

  withError(error: string): UserListOutput {
    return new UserListOutput(this.users, this.searchQuery, false, false, error)
  }

  withSearchQuery(query: string): UserListOutput {
    return new UserListOutput(this.users, query, this.isLoading, this.isRefreshing, this.error)
  }
}

export class UserListEffectType {
  static readonly NAVIGATE_TO_DETAIL = 'NAVIGATE_TO_DETAIL'
  static readonly SHOW_TOAST = 'SHOW_TOAST'
}

export class UserListEffect {
  readonly type: string
  readonly payload: string | undefined

  private constructor(type: string, payload: string | undefined) {
    this.type = type
    this.payload = payload
  }

  static navigateToDetail(userId: string): UserListEffect {
    return new UserListEffect(UserListEffectType.NAVIGATE_TO_DETAIL, userId)
  }

  static showToast(message: string): UserListEffect {
    return new UserListEffect(UserListEffectType.SHOW_TOAST, message)
  }
}

@injectable()
export class UserListViewModel {
  private userRepository: UserRepository
  private _output: UserListOutput = UserListOutput.initial()
  private _effectCallback: ((effect: UserListEffect) => void) | undefined = undefined

  constructor(userRepository: UserRepository) {
    this.userRepository = userRepository
  }

  get output(): UserListOutput {
    return this._output
  }

  setEffectCallback(callback: (effect: UserListEffect) => void): void {
    this._effectCallback = callback
  }

  onInput(input: UserListInput): void {
    switch (input.type) {
      case UserListInputType.LOAD:
        this.loadUsers()
        break
      case UserListInputType.REFRESH:
        this.refreshUsers()
        break
      case UserListInputType.SEARCH:
        this.searchUsers(input.payload as string)
        break
      case UserListInputType.SELECT_USER:
        this.selectUser(input.payload as string)
        break
      case UserListInputType.RETRY:
        this.loadUsers()
        break
      default:
        break
    }
  }

  private async loadUsers(): Promise<void> {
    this._output = this._output.withLoading(true)

    const result = await this.userRepository.getUsers()
    result.fold(
      (users: Array<User>) => {
        this._output = this._output.withUsers(users)
      },
      (error: AppError) => {
        this._output = this._output.withError(error.message)
      }
    )
  }

  private async refreshUsers(): Promise<void> {
    this._output = this._output.withRefreshing(true)

    const result = await this.userRepository.getUsers()
    result.fold(
      (users: Array<User>) => {
        this._output = this._output.withUsers(users)
        this.emitEffect(UserListEffect.showToast('Refreshed successfully'))
      },
      (error: AppError) => {
        this._output = this._output.withRefreshing(false)
        this.emitEffect(UserListEffect.showToast('Refresh failed'))
      }
    )
  }

  private searchUsers(query: string): void {
    this._output = this._output.withSearchQuery(query)
    // Filter locally (offline-first)
    // For server search, call repository with query param
  }

  private selectUser(userId: string): void {
    this.emitEffect(UserListEffect.navigateToDetail(userId))
  }

  private emitEffect(effect: UserListEffect): void {
    if (this._effectCallback !== undefined) {
      this._effectCallback(effect)
    }
  }
}
```

#### ArkUI User List Page

```typescript
// pages/UserListPage.ets
@Entry
@Component
struct UserListPage {
  @State private output: UserListOutput = UserListOutput.initial()
  private viewModel: UserListViewModel = AppContainer.resolve<UserListViewModel>(ServiceIdentifiers.USER_LIST_VIEW_MODEL)

  aboutToAppear(): void {
    this.viewModel.setEffectCallback((effect: UserListEffect) => {
      this.handleEffect(effect)
    })
    this.viewModel.onInput(UserListInput.load())
    this.output = this.viewModel.output
  }

  private handleEffect(effect: UserListEffect): void {
    switch (effect.type) {
      case UserListEffectType.NAVIGATE_TO_DETAIL:
        const params = new Map<string, string>()
        params.set('userId', effect.payload as string)
        NavigationHelper.pushUrl(NavigationRoutes.USER_DETAIL, params)
        break
      case UserListEffectType.SHOW_TOAST:
        promptAction.showToast({ message: effect.payload as string })
        break
      default:
        break
    }
  }

  build() {
    Column() {
      // Search bar
      Search({ placeholder: 'Search users...', value: this.output.searchQuery })
        .onChange((value: string) => {
          this.viewModel.onInput(UserListInput.search(value))
          this.output = this.viewModel.output
        })
        .width('90%')
        .margin({ top: 16, bottom: 16 })

      if (this.output.isLoading) {
        // Loading state
        Column() {
          LoadingProgress().width(48).height(48)
          Text($r('app.string.loading')).margin({ top: 16 })
        }
        .width('100%')
        .layoutWeight(1)
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
      } else if (this.output.error !== undefined) {
        // Error state
        Column() {
          Text(this.output.error)
            .fontSize(16)
            .fontColor(Color.Red)
            .margin({ bottom: 16 })
          Button($r('app.string.retry'))
            .onClick(() => {
              this.viewModel.onInput(UserListInput.retry())
              this.output = this.viewModel.output
            })
        }
        .width('100%')
        .layoutWeight(1)
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
      } else if (this.output.isEmpty) {
        // Empty state
        Column() {
          Text($r('app.string.no_users_found'))
            .fontSize(18)
            .fontWeight(FontWeight.Medium)
            .margin({ bottom: 8 })
          Text($r('app.string.no_users_description'))
            .fontSize(14)
            .fontColor(Color.Gray)
        }
        .width('100%')
        .layoutWeight(1)
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
      } else {
        // Content state
        Refresh({ refreshing: this.output.isRefreshing }) {
          List() {
            LazyForEach(new UserDataSource(this.output.users), (user: User) => {
              ListItem() {
                this.UserCard(user)
              }
              .onClick(() => {
                this.viewModel.onInput(UserListInput.selectUser(user.id))
                this.output = this.viewModel.output
              })
            }, (user: User) => user.id)
          }
          .divider({ strokeWidth: 1, color: '#F0F0F0' })
        }
        .onRefreshing(() => {
          this.viewModel.onInput(UserListInput.refresh())
          this.output = this.viewModel.output
        })
        .layoutWeight(1)
      }
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  UserCard(user: User) {
    Row() {
      // Avatar placeholder
      Text(user.name.charAt(0))
        .fontSize(20)
        .fontWeight(FontWeight.Bold)
        .fontColor(Color.White)
        .width(48)
        .height(48)
        .borderRadius(24)
        .backgroundColor('#4A90D9')
        .textAlign(TextAlign.Center)

      Column() {
        Text(user.name)
          .fontSize(16)
          .fontWeight(FontWeight.Medium)
        Text(user.email)
          .fontSize(14)
          .fontColor(Color.Gray)
          .margin({ top: 4 })
      }
      .alignItems(HorizontalAlign.Start)
      .margin({ left: 16 })
      .layoutWeight(1)

      Image($r('app.media.ic_chevron_right'))
        .width(24)
        .height(24)
        .fillColor(Color.Gray)
    }
    .width('100%')
    .padding(16)
  }
}

// LazyForEach data source (required by ArkUI)
class UserDataSource implements IDataSource {
  private users: Array<User>

  constructor(users: Array<User>) {
    this.users = users
  }

  totalCount(): number {
    return this.users.length
  }

  getData(index: number): User {
    return this.users[index]
  }

  registerDataChangeListener(listener: DataChangeListener): void { }
  unregisterDataChangeListener(listener: DataChangeListener): void { }
}
```

---

### Example 3: DI Container Registration

```typescript
// core/di/AppContainer.ets
import { Container, ServiceIdentifiers } from './Container'

export class AppContainer {
  private static container: Container = new Container()
  private static initialized: boolean = false

  static initialize(): void {
    if (AppContainer.initialized) {
      return
    }

    const c = AppContainer.container

    // Core services (singletons)
    c.bindSingleton(ServiceIdentifiers.NETWORK_MONITOR, () => {
      return new NetworkMonitor()
    })

    c.bindSingleton(ServiceIdentifiers.SECURITY_SERVICE, () => {
      return new SecurityService()
    })

    c.bindSingleton(ServiceIdentifiers.ANALYTICS_SERVICE, () => {
      return new AnalyticsService()
    })

    c.bindSingleton(ServiceIdentifiers.SYNC_MANAGER, () => {
      const networkMonitor = c.resolve<NetworkMonitor>(ServiceIdentifiers.NETWORK_MONITOR)
      return new SyncManager(networkMonitor)
    })

    // Repositories (singletons)
    c.bindSingleton(ServiceIdentifiers.AUTH_REPOSITORY, () => {
      return new AuthRepositoryImpl(
        new AuthApiService(),
        new AuthLocalSource(),
        c.resolve<SecurityService>(ServiceIdentifiers.SECURITY_SERVICE)
      )
    })

    c.bindSingleton(ServiceIdentifiers.USER_REPOSITORY, () => {
      return new UserRepositoryImpl(
        new UserLocalSource(),
        new UserApiService(),
        c.resolve<NetworkMonitor>(ServiceIdentifiers.NETWORK_MONITOR)
      )
    })

    // ViewModels (transient - new instance per page)
    c.bind(ServiceIdentifiers.LOGIN_VIEW_MODEL, () => {
      return new LoginViewModel(
        c.resolve<AuthRepository>(ServiceIdentifiers.AUTH_REPOSITORY)
      )
    })

    c.bind(ServiceIdentifiers.USER_LIST_VIEW_MODEL, () => {
      return new UserListViewModel(
        c.resolve<UserRepository>(ServiceIdentifiers.USER_REPOSITORY)
      )
    })

    AppContainer.initialized = true
  }

  static resolve<T extends Object>(identifier: string): T {
    if (!AppContainer.initialized) {
      AppContainer.initialize()
    }
    return AppContainer.container.resolve<T>(identifier)
  }
}
```

---

### Example 4: HUKS Encryption/Decryption

```typescript
// core/security/SecurityService.ets (full implementation)
import { huks } from '@kit.UniversalKeystoreKit'

@injectable()
export class SecurityService {
  private static readonly KEY_ALIAS = 'arcana_master_key'

  async ensureKeyExists(): Promise<Result<boolean, AppError>> {
    try {
      const isExist = await huks.isKeyItemExist(SecurityService.KEY_ALIAS, this.getEmptyOptions())
      if (!isExist) {
        return await this.generateKey()
      }
      return Result.success(true)
    } catch (e) {
      return await this.generateKey()
    }
  }

  async encrypt(plaintext: string): Promise<Result<Uint8Array, AppError>> {
    await this.ensureKeyExists()

    const properties: Array<huks.HuksParam> = new Array<huks.HuksParam>()
    properties.push({ tag: huks.HuksTag.HUKS_TAG_ALGORITHM, value: huks.HuksKeyAlg.HUKS_ALG_AES })
    properties.push({ tag: huks.HuksTag.HUKS_TAG_PURPOSE, value: huks.HuksKeyPurpose.HUKS_KEY_PURPOSE_ENCRYPT })
    properties.push({ tag: huks.HuksTag.HUKS_TAG_BLOCK_MODE, value: huks.HuksCipherMode.HUKS_MODE_GCM })
    properties.push({ tag: huks.HuksTag.HUKS_TAG_PADDING, value: huks.HuksKeyPadding.HUKS_PADDING_NONE })

    const options: huks.HuksOptions = {
      properties: properties,
      inData: this.stringToUint8Array(plaintext)
    }

    try {
      const handleResult = await huks.initSession(SecurityService.KEY_ALIAS, options)
      const handle = handleResult.handle
      const finishResult = await huks.finishSession(handle, options)
      if (finishResult.outData !== undefined) {
        return Result.success(finishResult.outData)
      }
      return Result.failure(new AppError(AppError.UNKNOWN, 'Encryption returned no data'))
    } catch (e) {
      return Result.failure(new AppError(AppError.UNKNOWN, 'Encryption failed'))
    }
  }

  async decrypt(ciphertext: Uint8Array): Promise<Result<string, AppError>> {
    const properties: Array<huks.HuksParam> = new Array<huks.HuksParam>()
    properties.push({ tag: huks.HuksTag.HUKS_TAG_ALGORITHM, value: huks.HuksKeyAlg.HUKS_ALG_AES })
    properties.push({ tag: huks.HuksTag.HUKS_TAG_PURPOSE, value: huks.HuksKeyPurpose.HUKS_KEY_PURPOSE_DECRYPT })
    properties.push({ tag: huks.HuksTag.HUKS_TAG_BLOCK_MODE, value: huks.HuksCipherMode.HUKS_MODE_GCM })
    properties.push({ tag: huks.HuksTag.HUKS_TAG_PADDING, value: huks.HuksKeyPadding.HUKS_PADDING_NONE })

    const options: huks.HuksOptions = {
      properties: properties,
      inData: ciphertext
    }

    try {
      const handleResult = await huks.initSession(SecurityService.KEY_ALIAS, options)
      const handle = handleResult.handle
      const finishResult = await huks.finishSession(handle, options)
      if (finishResult.outData !== undefined) {
        return Result.success(this.uint8ArrayToString(finishResult.outData))
      }
      return Result.failure(new AppError(AppError.UNKNOWN, 'Decryption returned no data'))
    } catch (e) {
      return Result.failure(new AppError(AppError.UNKNOWN, 'Decryption failed'))
    }
  }

  private stringToUint8Array(str: string): Uint8Array {
    const encoder = new TextEncoder()
    return encoder.encode(str)
  }

  private uint8ArrayToString(array: Uint8Array): string {
    const decoder = new TextDecoder()
    return decoder.decode(array)
  }

  private getEmptyOptions(): huks.HuksOptions {
    return { properties: new Array<huks.HuksParam>() }
  }

  private async generateKey(): Promise<Result<boolean, AppError>> {
    const properties: Array<huks.HuksParam> = new Array<huks.HuksParam>()
    properties.push({ tag: huks.HuksTag.HUKS_TAG_ALGORITHM, value: huks.HuksKeyAlg.HUKS_ALG_AES })
    properties.push({ tag: huks.HuksTag.HUKS_TAG_KEY_SIZE, value: huks.HuksKeySize.HUKS_AES_KEY_SIZE_256 })
    properties.push({ tag: huks.HuksTag.HUKS_TAG_PURPOSE, value: huks.HuksKeyPurpose.HUKS_KEY_PURPOSE_ENCRYPT | huks.HuksKeyPurpose.HUKS_KEY_PURPOSE_DECRYPT })
    properties.push({ tag: huks.HuksTag.HUKS_TAG_BLOCK_MODE, value: huks.HuksCipherMode.HUKS_MODE_GCM })
    properties.push({ tag: huks.HuksTag.HUKS_TAG_PADDING, value: huks.HuksKeyPadding.HUKS_PADDING_NONE })

    try {
      await huks.generateKeyItem(SecurityService.KEY_ALIAS, { properties: properties })
      return Result.success(true)
    } catch (e) {
      return Result.failure(new AppError(AppError.UNKNOWN, 'Key generation failed'))
    }
  }
}
```

---

## Common Problem Solutions

### Problem 1: ArkTS Strict Mode - Cannot Use Object Literal

```typescript
// WRONG - Object literal not allowed for constants
const config = { baseUrl: 'https://api.example.com', timeout: 30000 }

// CORRECT - Class-based constant
export class ApiConfig {
  static readonly BASE_URL = 'https://api.example.com'
  static readonly TIMEOUT_MS = 30000
  static readonly MAX_RETRIES = 3
}
```

### Problem 2: ArkTS Strict Mode - Cannot Use Spread for State Update

```typescript
// WRONG
this.state = { ...this.state, isLoading: true }

// CORRECT - Factory method
this.state = this.state.withLoading(true)
```

### Problem 3: LazyForEach Requires IDataSource

```typescript
// ArkUI LazyForEach requires IDataSource implementation
class ItemDataSource implements IDataSource {
  private items: Array<ItemModel>

  constructor(items: Array<ItemModel>) {
    this.items = items
  }

  totalCount(): number {
    return this.items.length
  }

  getData(index: number): ItemModel {
    return this.items[index]
  }

  registerDataChangeListener(listener: DataChangeListener): void { }
  unregisterDataChangeListener(listener: DataChangeListener): void { }
}
```

### Problem 4: Reactive State Updates in ArkUI

```typescript
// @State only triggers re-render for primitive changes or reference changes
// For class objects, replace the entire reference

// WRONG - Mutating existing object (no re-render)
this.output.isLoading = true

// CORRECT - Replace with new instance (triggers re-render)
this.output = this.output.withLoading(true)
```

---

## Testing Examples

### ViewModel Test with @ohos/hypium

```typescript
// test/LoginViewModelTest.ets
import { describe, it, expect, beforeEach } from '@ohos/hypium'
import { LoginViewModel, LoginInput, LoginOutput } from '../presentation/viewmodel/LoginViewModel'

class MockAuthRepository implements AuthRepository {
  loginResult: Result<AuthResult, AppError> = Result.success(
    new AuthResult(
      new User('test-id', 'Test User', 'test@test.com', undefined, Date.now()),
      'mock-token'
    )
  )

  async login(email: string, password: string): Promise<Result<AuthResult, AppError>> {
    return this.loginResult
  }

  async logout(): Promise<Result<boolean, AppError>> {
    return Result.success(true)
  }

  async isLoggedIn(): Promise<boolean> {
    return false
  }

  async getCurrentUser(): Promise<Result<User, AppError>> {
    return Result.failure(new AppError(AppError.NOT_FOUND, 'Not logged in'))
  }
}

export default function loginViewModelTest() {
  describe('LoginViewModel', () => {
    let viewModel: LoginViewModel
    let mockRepo: MockAuthRepository

    beforeEach(() => {
      mockRepo = new MockAuthRepository()
      viewModel = new LoginViewModel(mockRepo)
    })

    it('should have initial empty state', () => {
      const output = viewModel.output
      expect(output.email).assertEqual('')
      expect(output.password).assertEqual('')
      expect(output.isLoading).assertFalse()
      expect(output.emailError).assertUndefined()
      expect(output.passwordError).assertUndefined()
    })

    it('should update email on input', () => {
      viewModel.onInput(LoginInput.updateEmail('test@test.com'))
      expect(viewModel.output.email).assertEqual('test@test.com')
      expect(viewModel.output.emailError).assertUndefined()
    })

    it('should show email error for invalid email', () => {
      viewModel.onInput(LoginInput.updateEmail('invalid'))
      expect(viewModel.output.emailError).assertNotUndefined()
    })

    it('should show password error for short password', () => {
      viewModel.onInput(LoginInput.updatePassword('12'))
      expect(viewModel.output.passwordError).assertNotUndefined()
    })

    it('should emit navigate effect on successful login', async () => {
      let emittedEffect: LoginEffect | undefined = undefined
      viewModel.setEffectCallback((effect: LoginEffect) => {
        emittedEffect = effect
      })

      viewModel.onInput(LoginInput.updateEmail('test@test.com'))
      viewModel.onInput(LoginInput.updatePassword('password123'))
      viewModel.onInput(LoginInput.submit())

      // Wait for async operation
      await new Promise<void>((resolve) => setTimeout(resolve, 100))

      expect(emittedEffect).assertNotUndefined()
      expect(emittedEffect!.type).assertEqual(LoginEffectType.NAVIGATE_HOME)
    })

    it('should show error on failed login', async () => {
      mockRepo.loginResult = Result.failure(
        new AppError(AppError.UNAUTHORIZED, 'Invalid credentials')
      )

      viewModel.onInput(LoginInput.updateEmail('test@test.com'))
      viewModel.onInput(LoginInput.updatePassword('wrong_password'))
      viewModel.onInput(LoginInput.submit())

      await new Promise<void>((resolve) => setTimeout(resolve, 100))

      expect(viewModel.output.generalError).assertNotUndefined()
      expect(viewModel.output.isLoading).assertFalse()
    })
  })
}
```

### Repository Test

```typescript
// test/UserRepositoryImplTest.ets
export default function userRepositoryTest() {
  describe('UserRepositoryImpl', () => {
    let repository: UserRepositoryImpl
    let mockLocalSource: MockUserLocalSource
    let mockApiService: MockUserApiService
    let mockNetworkMonitor: MockNetworkMonitor

    beforeEach(() => {
      mockLocalSource = new MockUserLocalSource()
      mockApiService = new MockUserApiService()
      mockNetworkMonitor = new MockNetworkMonitor()
      repository = new UserRepositoryImpl(mockLocalSource, mockApiService, mockNetworkMonitor)
    })

    it('should return users from local source', async () => {
      mockLocalSource.setUsers([
        new UserEntity('1', 'John', 'john@test.com', SyncStatus.SYNCED),
        new UserEntity('2', 'Jane', 'jane@test.com', SyncStatus.SYNCED)
      ])

      const result = await repository.getUsers()
      expect(result.isSuccess()).assertTrue()

      const users = result.getOrNull() as Array<User>
      expect(users.length).assertEqual(2)
      expect(users[0].name).assertEqual('John')
    })

    it('should create user with PENDING_CREATE status', async () => {
      mockNetworkMonitor.setOnline(false)

      const user = new User('3', 'New User', 'new@test.com', undefined, Date.now())
      const result = await repository.createUser(user)

      expect(result.isSuccess()).assertTrue()
      expect(mockLocalSource.lastInsertedStatus).assertEqual(SyncStatus.PENDING_CREATE)
    })

    it('should sync when online after create', async () => {
      mockNetworkMonitor.setOnline(true)

      const user = new User('4', 'Online User', 'online@test.com', undefined, Date.now())
      await repository.createUser(user)

      expect(mockApiService.syncCalled).assertTrue()
    })
  })
}
```

---

## Offline-First Examples

### RelationalStore Local Source

```typescript
// data/local/UserLocalSource.ets
import { relationalStore } from '@kit.ArkData'

export class UserLocalSource {
  private rdbStore: relationalStore.RdbStore | undefined = undefined

  private static readonly TABLE_NAME = 'users'
  private static readonly CREATE_TABLE = `
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      email TEXT NOT NULL,
      avatar_url TEXT,
      sync_status TEXT NOT NULL DEFAULT 'SYNCED',
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    )
  `

  async initialize(context: Context): Promise<void> {
    const config: relationalStore.StoreConfig = {
      name: 'arcana.db',
      securityLevel: relationalStore.SecurityLevel.S1
    }
    this.rdbStore = await relationalStore.getRdbStore(context, config)
    await this.rdbStore.executeSql(UserLocalSource.CREATE_TABLE)
  }

  async getAll(): Promise<Array<UserEntity>> {
    if (this.rdbStore === undefined) {
      return new Array<UserEntity>()
    }

    const predicates = new relationalStore.RdbPredicates(UserLocalSource.TABLE_NAME)
    predicates.notEqualTo('sync_status', SyncStatus.PENDING_DELETE)
    predicates.orderByDesc('created_at')

    const resultSet = await this.rdbStore.query(predicates)
    const entities = new Array<UserEntity>()

    while (resultSet.goToNextRow()) {
      entities.push(UserEntity.fromResultSet(resultSet))
    }
    resultSet.close()

    return entities
  }

  async getById(id: string): Promise<UserEntity | undefined> {
    if (this.rdbStore === undefined) {
      return undefined
    }

    const predicates = new relationalStore.RdbPredicates(UserLocalSource.TABLE_NAME)
    predicates.equalTo('id', id)

    const resultSet = await this.rdbStore.query(predicates)
    let entity: UserEntity | undefined = undefined

    if (resultSet.goToNextRow()) {
      entity = UserEntity.fromResultSet(resultSet)
    }
    resultSet.close()

    return entity
  }

  async insert(entity: UserEntity): Promise<void> {
    if (this.rdbStore === undefined) {
      return
    }

    const values: relationalStore.ValuesBucket = {
      'id': entity.id,
      'name': entity.name,
      'email': entity.email,
      'avatar_url': entity.avatarUrl,
      'sync_status': entity.syncStatus,
      'created_at': entity.createdAt,
      'updated_at': entity.updatedAt
    }

    await this.rdbStore.insert(UserLocalSource.TABLE_NAME, values)
  }

  async update(entity: UserEntity): Promise<void> {
    if (this.rdbStore === undefined) {
      return
    }

    const values: relationalStore.ValuesBucket = {
      'name': entity.name,
      'email': entity.email,
      'avatar_url': entity.avatarUrl,
      'sync_status': entity.syncStatus,
      'updated_at': Date.now()
    }

    const predicates = new relationalStore.RdbPredicates(UserLocalSource.TABLE_NAME)
    predicates.equalTo('id', entity.id)

    await this.rdbStore.update(values, predicates)
  }

  async updateSyncStatus(id: string, status: string): Promise<void> {
    if (this.rdbStore === undefined) {
      return
    }

    const values: relationalStore.ValuesBucket = {
      'sync_status': status,
      'updated_at': Date.now()
    }

    const predicates = new relationalStore.RdbPredicates(UserLocalSource.TABLE_NAME)
    predicates.equalTo('id', id)

    await this.rdbStore.update(values, predicates)
  }

  async getPendingSync(): Promise<Array<UserEntity>> {
    if (this.rdbStore === undefined) {
      return new Array<UserEntity>()
    }

    const predicates = new relationalStore.RdbPredicates(UserLocalSource.TABLE_NAME)
    predicates.in('sync_status', [
      SyncStatus.PENDING_CREATE,
      SyncStatus.PENDING_UPDATE,
      SyncStatus.PENDING_DELETE
    ])

    const resultSet = await this.rdbStore.query(predicates)
    const entities = new Array<UserEntity>()

    while (resultSet.goToNextRow()) {
      entities.push(UserEntity.fromResultSet(resultSet))
    }
    resultSet.close()

    return entities
  }

  async delete(id: string): Promise<void> {
    if (this.rdbStore === undefined) {
      return
    }

    const predicates = new relationalStore.RdbPredicates(UserLocalSource.TABLE_NAME)
    predicates.equalTo('id', id)

    await this.rdbStore.delete(predicates)
  }
}
```
