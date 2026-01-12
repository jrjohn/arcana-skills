# iOS SwiftUI UI 生成參考

## 元件庫

### AppButton

```swift
import SwiftUI

enum AppButtonStyle {
    case primary, secondary, outline, ghost
}

struct AppButton: View {
    let title: String
    let style: AppButtonStyle
    let isLoading: Bool
    let action: () -> Void

    init(_ title: String, style: AppButtonStyle = .primary, isLoading: Bool = false, action: @escaping () -> Void) {
        self.title = title
        self.style = style
        self.isLoading = isLoading
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            HStack {
                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: foregroundColor))
                } else {
                    Text(title).fontWeight(.semibold)
                }
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(backgroundColor)
            .foregroundColor(foregroundColor)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(borderColor, lineWidth: style == .outline ? 2 : 0)
            )
        }
        .disabled(isLoading)
    }

    private var backgroundColor: Color {
        switch style {
        case .primary: return .accentColor
        case .secondary: return Color(.systemGray6)
        case .outline, .ghost: return .clear
        }
    }

    private var foregroundColor: Color {
        switch style {
        case .primary: return .white
        case .secondary, .ghost: return .primary
        case .outline: return .accentColor
        }
    }

    private var borderColor: Color {
        style == .outline ? .accentColor : .clear
    }
}
```

### AppTextField

```swift
import SwiftUI

struct AppTextField: View {
    let label: String
    let placeholder: String
    @Binding var text: String
    var isSecure: Bool = false
    var error: String? = nil

    @State private var showPassword = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label)
                .font(.subheadline)
                .fontWeight(.medium)

            HStack {
                if isSecure && !showPassword {
                    SecureField(placeholder, text: $text)
                } else {
                    TextField(placeholder, text: $text)
                }

                if isSecure {
                    Button(action: { showPassword.toggle() }) {
                        Image(systemName: showPassword ? "eye.slash" : "eye")
                            .foregroundColor(.secondary)
                    }
                }
            }
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(error != nil ? Color.red : Color.clear, lineWidth: 1)
            )

            if let error = error {
                Text(error)
                    .font(.caption)
                    .foregroundColor(.red)
            }
        }
    }
}
```

### AppCard

```swift
import SwiftUI

struct AppCard<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            content
        }
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 8, y: 4)
    }
}

struct ImageCard: View {
    let imageUrl: String
    let title: String
    let description: String
    let price: String?

    var body: some View {
        AppCard {
            AsyncImage(url: URL(string: imageUrl)) { image in
                image.resizable().aspectRatio(contentMode: .fill)
            } placeholder: {
                Color(.systemGray5)
            }
            .frame(height: 192)
            .clipped()

            VStack(alignment: .leading, spacing: 4) {
                Text(title).font(.headline)
                Text(description).font(.subheadline).foregroundColor(.secondary)
                if let price = price {
                    Text(price).font(.headline).foregroundColor(.accentColor).padding(.top, 8)
                }
            }
            .padding()
        }
    }
}
```

---

## 登入頁範例

```swift
import SwiftUI

struct LoginView: View {
    @State private var email = ""
    @State private var password = ""
    @State private var isLoading = false

    var body: some View {
        ScrollView {
            VStack(spacing: 32) {
                // Header
                VStack(spacing: 8) {
                    Text("AppName")
                        .font(.system(size: 28, weight: .bold))
                        .foregroundColor(.accentColor)
                    Text("歡迎回來")
                        .font(.system(size: 28, weight: .bold))
                    Text("登入以繼續使用服務")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .padding(.top, 48)

                // Form
                VStack(spacing: 20) {
                    AppTextField(
                        label: "電子郵件",
                        placeholder: "your@email.com",
                        text: $email
                    )
                    .textContentType(.emailAddress)
                    .keyboardType(.emailAddress)
                    .autocapitalization(.none)

                    AppTextField(
                        label: "密碼",
                        placeholder: "輸入密碼",
                        text: $password,
                        isSecure: true
                    )

                    HStack {
                        Spacer()
                        Button("忘記密碼？") { }
                            .font(.subheadline)
                    }

                    AppButton("登入", isLoading: isLoading) {
                        handleLogin()
                    }

                    // Divider
                    HStack {
                        Rectangle().fill(Color(.systemGray4)).frame(height: 1)
                        Text("或").font(.subheadline).foregroundColor(.secondary)
                        Rectangle().fill(Color(.systemGray4)).frame(height: 1)
                    }

                    // Social Login
                    AppButton("使用 Google 登入", style: .secondary) { }
                    AppButton("使用 Apple 登入", style: .secondary) { }
                }

                Spacer()

                // Footer
                HStack(spacing: 4) {
                    Text("還沒有帳號？").foregroundColor(.secondary)
                    Button("立即註冊") { }.fontWeight(.semibold)
                }
                .font(.subheadline)
            }
            .padding(.horizontal, 24)
        }
    }

    private func handleLogin() {
        isLoading = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            isLoading = false
        }
    }
}

#Preview {
    LoginView()
}
```

---

## 導航元件

### TabBar

```swift
import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView()
                .tabItem {
                    Image(systemName: selectedTab == 0 ? "house.fill" : "house")
                    Text("首頁")
                }
                .tag(0)

            ExploreView()
                .tabItem {
                    Image(systemName: "magnifyingglass")
                    Text("探索")
                }
                .tag(1)

            ProfileView()
                .tabItem {
                    Image(systemName: selectedTab == 2 ? "person.fill" : "person")
                    Text("我的")
                }
                .tag(2)
        }
    }
}
```

### Navigation Bar

```swift
import SwiftUI

struct CustomNavigationBar: View {
    let title: String
    let showBackButton: Bool
    let onBack: () -> Void
    var trailingAction: (() -> Void)? = nil

    var body: some View {
        HStack {
            if showBackButton {
                Button(action: onBack) {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 20, weight: .medium))
                        .frame(width: 44, height: 44)
                }
            } else {
                Spacer().frame(width: 44)
            }

            Spacer()

            Text(title)
                .font(.headline)

            Spacer()

            if let action = trailingAction {
                Button(action: action) {
                    Image(systemName: "ellipsis")
                        .frame(width: 44, height: 44)
                }
            } else {
                Spacer().frame(width: 44)
            }
        }
        .padding(.horizontal)
        .frame(height: 44)
        .background(Color(.systemBackground))
    }
}
```

---

## 列表元件

```swift
import SwiftUI

struct ListItemView: View {
    let icon: String
    let iconColor: Color
    let title: String
    let subtitle: String?
    let showChevron: Bool

    init(icon: String, iconColor: Color = .accentColor, title: String, subtitle: String? = nil, showChevron: Bool = true) {
        self.icon = icon
        self.iconColor = iconColor
        self.title = title
        self.subtitle = subtitle
        self.showChevron = showChevron
    }

    var body: some View {
        HStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 20))
                .foregroundColor(iconColor)
                .frame(width: 40, height: 40)
                .background(iconColor.opacity(0.1))
                .cornerRadius(10)

            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.body)
                if let subtitle = subtitle {
                    Text(subtitle).font(.subheadline).foregroundColor(.secondary)
                }
            }

            Spacer()

            if showChevron {
                Image(systemName: "chevron.right")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
    }
}
```
