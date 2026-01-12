# Angular UI 生成參考

## 專案結構

```
📁 src/app/
├── 📁 components/
│   ├── 📁 ui/           # button/, input/, card/
│   └── 📁 layout/       # header/, tab-bar/
├── 📁 pages/
│   ├── 📁 auth/         # login/, register/
│   ├── 📁 home/
│   └── 📁 profile/
├── 📁 shared/
│   ├── 📁 models/
│   └── 📁 services/
└── 📁 styles/
    ├── _variables.scss
    └── _theme.scss
```

---

## Theme 設定 (SCSS)

```scss
// styles/_variables.scss
:root {
  // Colors
  --color-primary: #6366F1;
  --color-primary-hover: #4F46E5;
  --color-secondary: #EC4899;
  --color-background: #FFFFFF;
  --color-surface: #F8FAFC;
  --color-surface-hover: #F1F5F9;
  --color-text-primary: #1F2937;
  --color-text-secondary: #6B7280;
  --color-text-muted: #9CA3AF;
  --color-text-inverse: #FFFFFF;
  --color-border: #E5E7EB;
  --color-error: #EF4444;
  --color-success: #10B981;

  // Spacing
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;

  // Border Radius
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  // Font Size
  --font-xs: 12px;
  --font-sm: 14px;
  --font-md: 16px;
  --font-lg: 18px;
  --font-xl: 24px;

  // Shadow
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.05);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
}
```

---

## Button 元件

```typescript
// components/ui/button/button.component.ts
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-button',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './button.component.html',
  styleUrls: ['./button.component.scss']
})
export class ButtonComponent {
  @Input() variant: ButtonVariant = 'primary';
  @Input() size: ButtonSize = 'md';
  @Input() fullWidth = false;
  @Input() loading = false;
  @Input() disabled = false;
  @Input() type: 'button' | 'submit' = 'button';
  @Output() clicked = new EventEmitter<void>();

  get buttonClasses(): string {
    return [
      'app-button',
      `app-button--${this.variant}`,
      `app-button--${this.size}`,
      this.fullWidth ? 'app-button--full-width' : '',
      this.loading ? 'app-button--loading' : '',
    ].filter(Boolean).join(' ');
  }

  onClick(): void {
    if (!this.disabled && !this.loading) {
      this.clicked.emit();
    }
  }
}
```

```html
<!-- button.component.html -->
<button [type]="type" [class]="buttonClasses" [disabled]="disabled || loading" (click)="onClick()">
  <span class="app-button__spinner" *ngIf="loading"></span>
  <ng-content *ngIf="!loading"></ng-content>
</button>
```

```scss
// button.component.scss
.app-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 600;
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;

  &:active:not(:disabled) { transform: scale(0.98); }
  &:disabled { opacity: 0.5; cursor: not-allowed; }

  &--sm { padding: 8px 16px; font-size: var(--font-sm); min-height: 36px; }
  &--md { padding: 12px 24px; font-size: var(--font-md); min-height: 44px; }
  &--lg { padding: 16px 32px; font-size: var(--font-lg); min-height: 52px; }

  &--primary {
    background: var(--color-primary);
    color: var(--color-text-inverse);
    &:hover:not(:disabled) { background: var(--color-primary-hover); }
  }

  &--secondary {
    background: var(--color-surface);
    color: var(--color-text-primary);
    border: 1px solid var(--color-border);
    &:hover:not(:disabled) { background: var(--color-surface-hover); }
  }

  &--outline {
    background: transparent;
    color: var(--color-primary);
    border: 2px solid var(--color-primary);
    &:hover:not(:disabled) { background: rgba(99, 102, 241, 0.1); }
  }

  &--ghost {
    background: transparent;
    color: var(--color-text-primary);
    &:hover:not(:disabled) { background: var(--color-surface-hover); }
  }

  &--full-width { width: 100%; }

  &__spinner {
    width: 20px;
    height: 20px;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

---

## Input 元件

```typescript
// components/ui/input/input.component.ts
import { Component, Input, forwardRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, NG_VALUE_ACCESSOR, ControlValueAccessor } from '@angular/forms';

@Component({
  selector: 'app-input',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './input.component.html',
  styleUrls: ['./input.component.scss'],
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => InputComponent),
    multi: true
  }]
})
export class InputComponent implements ControlValueAccessor {
  @Input() label = '';
  @Input() placeholder = '';
  @Input() type: 'text' | 'email' | 'password' = 'text';
  @Input() error = '';
  @Input() required = false;

  value = '';
  showPassword = false;
  disabled = false;

  private onChange: (value: string) => void = () => {};
  private onTouched: () => void = () => {};

  get inputType(): string {
    return this.type === 'password' && this.showPassword ? 'text' : this.type;
  }

  writeValue(value: string): void { this.value = value || ''; }
  registerOnChange(fn: (value: string) => void): void { this.onChange = fn; }
  registerOnTouched(fn: () => void): void { this.onTouched = fn; }
  setDisabledState(isDisabled: boolean): void { this.disabled = isDisabled; }

  onInput(event: Event): void {
    this.value = (event.target as HTMLInputElement).value;
    this.onChange(this.value);
  }

  togglePassword(): void { this.showPassword = !this.showPassword; }
}
```

```html
<!-- input.component.html -->
<div class="app-input" [class.app-input--error]="error">
  <label *ngIf="label" class="app-input__label">
    {{ label }}<span *ngIf="required" class="app-input__required">*</span>
  </label>
  <div class="app-input__wrapper">
    <input
      [type]="inputType"
      [placeholder]="placeholder"
      [value]="value"
      [disabled]="disabled"
      (input)="onInput($event)"
      (blur)="onTouched()"
      class="app-input__field" />
    <button *ngIf="type === 'password'" type="button" class="app-input__toggle" (click)="togglePassword()">
      {{ showPassword ? '隱藏' : '顯示' }}
    </button>
  </div>
  <span *ngIf="error" class="app-input__error">{{ error }}</span>
</div>
```

```scss
// input.component.scss
.app-input {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);

  &__label {
    font-size: var(--font-sm);
    font-weight: 500;
    color: var(--color-text-primary);
  }

  &__required { color: var(--color-error); }

  &__wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  &__field {
    width: 100%;
    padding: 12px 16px;
    font-size: var(--font-md);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: var(--color-background);
    color: var(--color-text-primary);
    transition: all 0.15s ease;
    outline: none;

    &::placeholder { color: var(--color-text-muted); }
    &:focus {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
    &:disabled { background: var(--color-surface); cursor: not-allowed; }
  }

  &__toggle {
    position: absolute;
    right: 12px;
    background: none;
    border: none;
    color: var(--color-text-secondary);
    cursor: pointer;
    font-size: var(--font-sm);
  }

  &__error {
    font-size: var(--font-xs);
    color: var(--color-error);
  }

  &--error .app-input__field {
    border-color: var(--color-error);
  }
}
```

---

## Card 元件

```typescript
// components/ui/card/card.component.ts
import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="app-card" [class.app-card--clickable]="clickable">
      <img *ngIf="imageUrl" [src]="imageUrl" [alt]="title" class="app-card__image">
      <div class="app-card__content">
        <h3 *ngIf="title" class="app-card__title">{{ title }}</h3>
        <p *ngIf="description" class="app-card__description">{{ description }}</p>
        <ng-content></ng-content>
      </div>
    </div>
  `,
  styleUrls: ['./card.component.scss']
})
export class CardComponent {
  @Input() title = '';
  @Input() description = '';
  @Input() imageUrl = '';
  @Input() clickable = false;
}
```
