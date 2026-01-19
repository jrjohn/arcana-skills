# React UI 生成參考

## 專案結構

```
📁 src/
├── 📁 components/
│   ├── 📁 ui/           # Button, Input, Card...
│   ├── 📁 layout/       # Header, TabBar, Container
│   └── 📁 screens/      # LoginScreen, HomeScreen...
├── 📁 styles/
│   └── theme.ts
└── 📁 types/
```

---

## Theme 設定

```typescript
// styles/theme.ts
export const theme = {
  colors: {
    primary: '#6366F1',
    primaryHover: '#4F46E5',
    secondary: '#EC4899',
    background: '#FFFFFF',
    surface: '#F8FAFC',
    surfaceHover: '#F1F5F9',
    text: {
      primary: '#1F2937',
      secondary: '#6B7280',
      muted: '#9CA3AF',
      inverse: '#FFFFFF',
    },
    border: '#E5E7EB',
    error: '#EF4444',
    success: '#10B981',
    warning: '#F59E0B',
  },
  spacing: { xs: '4px', sm: '8px', md: '16px', lg: '24px', xl: '32px', xxl: '48px' },
  borderRadius: { sm: '6px', md: '12px', lg: '16px', full: '9999px' },
  fontSize: { xs: '12px', sm: '14px', md: '16px', lg: '18px', xl: '24px', xxl: '32px' },
  fontWeight: { normal: 400, medium: 500, semibold: 600, bold: 700 },
  shadow: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px rgba(0, 0, 0, 0.05)',
    lg: '0 10px 15px rgba(0, 0, 0, 0.1)',
  },
} as const;
```

---

## Button 元件

```tsx
// components/ui/Button.tsx
import styled, { css } from 'styled-components';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  loading?: boolean;
}

const sizeStyles = {
  sm: css`padding: 8px 16px; font-size: 14px; min-height: 36px;`,
  md: css`padding: 12px 24px; font-size: 16px; min-height: 44px;`,
  lg: css`padding: 16px 32px; font-size: 18px; min-height: 52px;`,
};

const variantStyles = {
  primary: css`
    background: ${({ theme }) => theme.colors.primary};
    color: ${({ theme }) => theme.colors.text.inverse};
    &:hover:not(:disabled) { background: ${({ theme }) => theme.colors.primaryHover}; }
  `,
  secondary: css`
    background: ${({ theme }) => theme.colors.surface};
    color: ${({ theme }) => theme.colors.text.primary};
    border: 1px solid ${({ theme }) => theme.colors.border};
    &:hover:not(:disabled) { background: ${({ theme }) => theme.colors.surfaceHover}; }
  `,
  outline: css`
    background: transparent;
    color: ${({ theme }) => theme.colors.primary};
    border: 2px solid ${({ theme }) => theme.colors.primary};
    &:hover:not(:disabled) { background: ${({ theme }) => theme.colors.primary}10; }
  `,
  ghost: css`
    background: transparent;
    color: ${({ theme }) => theme.colors.text.primary};
    &:hover:not(:disabled) { background: ${({ theme }) => theme.colors.surfaceHover}; }
  `,
};

export const Button = styled.button<ButtonProps>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 600;
  border-radius: ${({ theme }) => theme.borderRadius.md};
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
  width: ${({ fullWidth }) => (fullWidth ? '100%' : 'auto')};
  ${({ size = 'md' }) => sizeStyles[size]}
  ${({ variant = 'primary' }) => variantStyles[variant]}
  &:active:not(:disabled) { transform: scale(0.98); }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
`;
```

---

## Input 元件

```tsx
// components/ui/Input.tsx
import styled from 'styled-components';

interface InputProps {
  error?: boolean;
}

export const InputWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

export const Label = styled.label`
  font-size: 14px;
  font-weight: 500;
  color: ${({ theme }) => theme.colors.text.primary};
`;

export const Input = styled.input<InputProps>`
  width: 100%;
  padding: 12px 16px;
  font-size: 16px;
  border: 1px solid ${({ theme, error }) => error ? theme.colors.error : theme.colors.border};
  border-radius: ${({ theme }) => theme.borderRadius.md};
  background: ${({ theme }) => theme.colors.background};
  color: ${({ theme }) => theme.colors.text.primary};
  transition: all 0.15s ease;
  outline: none;

  &::placeholder { color: ${({ theme }) => theme.colors.text.muted}; }
  &:focus {
    border-color: ${({ theme }) => theme.colors.primary};
    box-shadow: 0 0 0 3px ${({ theme }) => theme.colors.primary}1A;
  }
  &:disabled { background: ${({ theme }) => theme.colors.surface}; cursor: not-allowed; }
`;

export const ErrorText = styled.span`
  font-size: 12px;
  color: ${({ theme }) => theme.colors.error};
`;
```

---

## Card 元件

```tsx
// components/ui/Card.tsx
import styled from 'styled-components';

export const Card = styled.div`
  background: ${({ theme }) => theme.colors.background};
  border-radius: ${({ theme }) => theme.borderRadius.lg};
  padding: 24px;
  box-shadow: ${({ theme }) => theme.shadow.sm};
  border: 1px solid ${({ theme }) => theme.colors.border}20;
`;

export const CardImage = styled.img`
  width: 100%;
  height: 192px;
  object-fit: cover;
  border-radius: ${({ theme }) => theme.borderRadius.md};
`;

export const CardTitle = styled.h3`
  font-size: 18px;
  font-weight: 600;
  color: ${({ theme }) => theme.colors.text.primary};
  margin: 0;
`;

export const CardDescription = styled.p`
  font-size: 14px;
  color: ${({ theme }) => theme.colors.text.secondary};
  margin: 8px 0 0;
`;
```

---

## 登入頁範例

```tsx
// screens/LoginScreen.tsx
import React, { useState } from 'react';
import styled from 'styled-components';
import { Button } from '../ui/Button';
import { Input, InputWrapper, Label } from '../ui/Input';

export const LoginScreen: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Login logic
    setTimeout(() => setLoading(false), 2000);
  };

  return (
    <Container>
      <Header>
        <Logo>AppName</Logo>
        <Title>歡迎回來</Title>
        <Subtitle>登入以繼續使用服務</Subtitle>
      </Header>

      <Form onSubmit={handleLogin}>
        <InputWrapper>
          <Label>電子郵件</Label>
          <Input
            type="email"
            placeholder="your@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </InputWrapper>

        <InputWrapper>
          <Label>密碼</Label>
          <Input
            type="password"
            placeholder="輸入密碼"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </InputWrapper>

        <ForgotPassword href="#">忘記密碼？</ForgotPassword>

        <Button type="submit" fullWidth disabled={loading}>
          {loading ? '登入中...' : '登入'}
        </Button>

        <Divider><span>或</span></Divider>

        <Button variant="outline" fullWidth>使用 Google 登入</Button>
        <Button variant="outline" fullWidth>使用 Apple 登入</Button>
      </Form>

      <Footer>
        還沒有帳號？<SignUpLink href="#">立即註冊</SignUpLink>
      </Footer>
    </Container>
  );
};

const Container = styled.div`
  min-height: 100vh;
  padding: 48px 24px;
  display: flex;
  flex-direction: column;
  background: ${({ theme }) => theme.colors.background};
`;

const Header = styled.header`
  text-align: center;
  margin-bottom: 40px;
`;

const Logo = styled.div`
  font-size: 28px;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.primary};
  margin-bottom: 24px;
`;

const Title = styled.h1`
  font-size: 28px;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.text.primary};
  margin-bottom: 8px;
`;

const Subtitle = styled.p`
  font-size: 16px;
  color: ${({ theme }) => theme.colors.text.secondary};
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const ForgotPassword = styled.a`
  align-self: flex-end;
  font-size: 14px;
  color: ${({ theme }) => theme.colors.primary};
  text-decoration: none;
`;

const Divider = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  color: ${({ theme }) => theme.colors.text.muted};
  &::before, &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: ${({ theme }) => theme.colors.border};
  }
`;

const Footer = styled.footer`
  margin-top: auto;
  text-align: center;
  font-size: 14px;
  color: ${({ theme }) => theme.colors.text.secondary};
`;

const SignUpLink = styled.a`
  color: ${({ theme }) => theme.colors.primary};
  font-weight: 600;
  text-decoration: none;
  margin-left: 4px;
`;
```
