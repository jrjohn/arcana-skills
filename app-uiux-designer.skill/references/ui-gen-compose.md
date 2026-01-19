# Android Jetpack Compose UI 生成參考

## Theme 設定

```kotlin
// ui/theme/Color.kt
val Primary = Color(0xFF6366F1)
val PrimaryHover = Color(0xFF4F46E5)
val Secondary = Color(0xFFEC4899)
val Background = Color(0xFFFFFFFF)
val Surface = Color(0xFFF8FAFC)
val SurfaceHover = Color(0xFFF1F5F9)
val TextPrimary = Color(0xFF1F2937)
val TextSecondary = Color(0xFF6B7280)
val TextMuted = Color(0xFF9CA3AF)
val Border = Color(0xFFE5E7EB)
val Error = Color(0xFFEF4444)
val Success = Color(0xFF10B981)

// ui/theme/Theme.kt
@Composable
fun AppTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = lightColorScheme(
            primary = Primary,
            secondary = Secondary,
            background = Background,
            surface = Surface,
            error = Error,
            onPrimary = Color.White,
            onBackground = TextPrimary,
            onSurface = TextPrimary
        ),
        content = content
    )
}
```

---

## 元件庫

### AppButton

```kotlin
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

enum class AppButtonStyle { Primary, Secondary, Outline, Ghost }

@Composable
fun AppButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    style: AppButtonStyle = AppButtonStyle.Primary,
    enabled: Boolean = true,
    loading: Boolean = false
) {
    val colors = when (style) {
        AppButtonStyle.Primary -> ButtonDefaults.buttonColors(
            containerColor = Primary,
            contentColor = Color.White
        )
        AppButtonStyle.Secondary -> ButtonDefaults.buttonColors(
            containerColor = Surface,
            contentColor = TextPrimary
        )
        AppButtonStyle.Outline -> ButtonDefaults.outlinedButtonColors(
            contentColor = Primary
        )
        AppButtonStyle.Ghost -> ButtonDefaults.textButtonColors(
            contentColor = TextPrimary
        )
    }

    when (style) {
        AppButtonStyle.Outline -> OutlinedButton(
            onClick = onClick,
            modifier = modifier.fillMaxWidth().height(52.dp),
            enabled = enabled && !loading,
            colors = colors,
            shape = RoundedCornerShape(12.dp)
        ) {
            ButtonContent(text, loading)
        }
        AppButtonStyle.Ghost -> TextButton(
            onClick = onClick,
            modifier = modifier.fillMaxWidth().height(52.dp),
            enabled = enabled && !loading,
            colors = colors
        ) {
            ButtonContent(text, loading)
        }
        else -> Button(
            onClick = onClick,
            modifier = modifier.fillMaxWidth().height(52.dp),
            enabled = enabled && !loading,
            colors = colors,
            shape = RoundedCornerShape(12.dp)
        ) {
            ButtonContent(text, loading)
        }
    }
}

@Composable
private fun ButtonContent(text: String, loading: Boolean) {
    if (loading) {
        CircularProgressIndicator(
            modifier = Modifier.size(20.dp),
            color = LocalContentColor.current,
            strokeWidth = 2.dp
        )
    } else {
        Text(text, fontWeight = FontWeight.SemiBold)
    }
}
```

### AppTextField

```kotlin
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp

@Composable
fun AppTextField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    modifier: Modifier = Modifier,
    placeholder: String = "",
    isPassword: Boolean = false,
    isError: Boolean = false,
    errorMessage: String? = null,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default
) {
    var passwordVisible by remember { mutableStateOf(false) }

    Column(modifier = modifier) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            color = TextPrimary,
            modifier = Modifier.padding(bottom = 8.dp)
        )

        OutlinedTextField(
            value = value,
            onValueChange = onValueChange,
            modifier = Modifier.fillMaxWidth(),
            placeholder = { Text(placeholder, color = TextMuted) },
            isError = isError,
            visualTransformation = if (isPassword && !passwordVisible)
                PasswordVisualTransformation() else VisualTransformation.None,
            trailingIcon = if (isPassword) {
                {
                    IconButton(onClick = { passwordVisible = !passwordVisible }) {
                        Icon(
                            imageVector = if (passwordVisible) Icons.Outlined.VisibilityOff
                                         else Icons.Outlined.Visibility,
                            contentDescription = null,
                            tint = TextSecondary
                        )
                    }
                }
            } else null,
            keyboardOptions = keyboardOptions,
            shape = RoundedCornerShape(12.dp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = Primary,
                unfocusedBorderColor = Border,
                errorBorderColor = Error
            )
        )

        if (isError && errorMessage != null) {
            Text(
                text = errorMessage,
                style = MaterialTheme.typography.labelSmall,
                color = Error,
                modifier = Modifier.padding(top = 4.dp)
            )
        }
    }
}
```

### AppCard

```kotlin
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage

@Composable
fun AppCard(
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit
) {
    Card(
        modifier = modifier,
        onClick = onClick ?: {},
        enabled = onClick != null,
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(content = content)
    }
}

@Composable
fun ImageCard(
    imageUrl: String,
    title: String,
    description: String,
    price: String? = null,
    onClick: () -> Unit = {}
) {
    AppCard(onClick = onClick) {
        AsyncImage(
            model = imageUrl,
            contentDescription = null,
            modifier = Modifier.fillMaxWidth().height(192.dp),
            contentScale = ContentScale.Crop
        )
        Column(modifier = Modifier.padding(16.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text(description, style = MaterialTheme.typography.bodyMedium, color = TextSecondary)
            if (price != null) {
                Text(price, style = MaterialTheme.typography.titleMedium, color = Primary,
                     modifier = Modifier.padding(top = 8.dp))
            }
        }
    }
}
```

---

## 登入頁範例

```kotlin
@Composable
fun LoginScreen(
    onLoginClick: (String, String) -> Unit,
    onForgotPasswordClick: () -> Unit,
    onSignUpClick: () -> Unit,
    onGoogleLoginClick: () -> Unit,
    onAppleLoginClick: () -> Unit
) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Spacer(modifier = Modifier.height(48.dp))

        // Header
        Text("AppName", fontSize = 28.sp, fontWeight = FontWeight.Bold, color = Primary)
        Spacer(modifier = Modifier.height(24.dp))
        Text("歡迎回來", fontSize = 28.sp, fontWeight = FontWeight.Bold)
        Spacer(modifier = Modifier.height(8.dp))
        Text("登入以繼續使用服務", color = TextSecondary)

        Spacer(modifier = Modifier.height(32.dp))

        // Form
        AppTextField(
            value = email,
            onValueChange = { email = it },
            label = "電子郵件",
            placeholder = "your@email.com",
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email)
        )

        Spacer(modifier = Modifier.height(16.dp))

        AppTextField(
            value = password,
            onValueChange = { password = it },
            label = "密碼",
            placeholder = "輸入密碼",
            isPassword = true
        )

        Spacer(modifier = Modifier.height(8.dp))

        TextButton(
            onClick = onForgotPasswordClick,
            modifier = Modifier.align(Alignment.End)
        ) {
            Text("忘記密碼？", color = Primary)
        }

        Spacer(modifier = Modifier.height(16.dp))

        AppButton(
            text = "登入",
            onClick = { onLoginClick(email, password) },
            loading = isLoading
        )

        Spacer(modifier = Modifier.height(24.dp))

        // Divider
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            HorizontalDivider(modifier = Modifier.weight(1f))
            Text("或", modifier = Modifier.padding(horizontal = 16.dp), color = TextMuted)
            HorizontalDivider(modifier = Modifier.weight(1f))
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Social Login
        AppButton(text = "使用 Google 登入", onClick = onGoogleLoginClick, style = AppButtonStyle.Outline)
        Spacer(modifier = Modifier.height(12.dp))
        AppButton(text = "使用 Apple 登入", onClick = onAppleLoginClick, style = AppButtonStyle.Outline)

        Spacer(modifier = Modifier.weight(1f))

        // Footer
        Row {
            Text("還沒有帳號？", color = TextSecondary)
            TextButton(onClick = onSignUpClick) {
                Text("立即註冊", fontWeight = FontWeight.SemiBold)
            }
        }
    }
}
```

---

## 導航元件

### BottomNavBar

```kotlin
@Composable
fun MainScreen() {
    var selectedTab by remember { mutableIntStateOf(0) }

    Scaffold(
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    icon = { Icon(Icons.Outlined.Home, contentDescription = null) },
                    label = { Text("首頁") },
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 }
                )
                NavigationBarItem(
                    icon = { Icon(Icons.Outlined.Search, contentDescription = null) },
                    label = { Text("探索") },
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 }
                )
                NavigationBarItem(
                    icon = { Icon(Icons.Outlined.Person, contentDescription = null) },
                    label = { Text("我的") },
                    selected = selectedTab == 2,
                    onClick = { selectedTab = 2 }
                )
            }
        }
    ) { paddingValues ->
        Box(modifier = Modifier.padding(paddingValues)) {
            when (selectedTab) {
                0 -> HomeScreen()
                1 -> ExploreScreen()
                2 -> ProfileScreen()
            }
        }
    }
}
```

### TopAppBar

```kotlin
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CustomTopBar(
    title: String,
    onBackClick: (() -> Unit)? = null,
    actions: @Composable RowScope.() -> Unit = {}
) {
    TopAppBar(
        title = { Text(title) },
        navigationIcon = {
            if (onBackClick != null) {
                IconButton(onClick = onBackClick) {
                    Icon(Icons.AutoMirrored.Outlined.ArrowBack, contentDescription = "返回")
                }
            }
        },
        actions = actions
    )
}
```
