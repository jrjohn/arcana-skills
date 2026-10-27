# 環境設置（一次性）

> 全部用 placeholder: `<HOST>`=Windows IP、`<ADMIN>`/`<ADMINPW>`=系統管理員帳密、
> `<USER>`/`<USERPW>`=**登入桌面那個使用者**的帳密、`<PY>`=python.exe 路徑、`<TOOLS>`=工作資料夾。

## 1. Windows 端: OpenSSH Server

```powershell
# 系統管理員 PowerShell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd; Set-Service sshd -StartupType Automatic
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH' -Enabled True -Direction Inbound -Protocol TCP -LocalPort 22 -Action Allow
```
- 預設 shell 常是 PowerShell。送中文/複雜指令時用 base64:
  `powershell -NoProfile -EncodedCommand <base64 of UTF-16LE command>`（Mac: `iconv -f UTF-8 -t UTF-16LE | base64`）。
- 快速指令改用 `cmd /c "..."`（比 PowerShell 冷啟動快很多，SSH 不穩時更可靠）。

## 2. python + 套件

```powershell
# 裝 python(或用現成的 <PY>)，然後:
<PY> -m pip install pywinauto pillow pyperclip
# 錄影才需要(非必要): mss opencv-python numpy  或 用 ffmpeg(見 recording.md)
```
- **pywinauto**: 控件操作(win32 backend 最通用)。
- **pillow**: `window.capture_as_image()` 截圖。
- **pyperclip**: 中文輸入(剪貼簿貼上)。

## 3. PsExec（跳進互動桌面）

從 Sysinternals 下載 `PsExec64.exe` 放 `<TOOLS>`。用法:
```
<TOOLS>\PsExec64.exe -accepteula -i 1 -u <USER> -p <USERPW> <PY> <TOOLS>\script.py
```
- `-i 1` = 進 session 1(主控台互動桌面)。`-u <USER>` = 以桌面使用者身分(滑鼠才作用)。
- 加 `-d` = 背景啟動不等待(長任務避免卡住 SSH channel)。
- **前提: `<USER>` 必須已登入 Windows 桌面**(鎖定畫面也算登入)。沒登入 → session 1 沒桌面 → GUI 操作失敗。

## 4. 權限排除（擋路的兩個）

| 擋路的 | 症狀 | 解法 |
|---|---|---|
| **SmartScreen / Smart App Control** | 啟動無簽章程式跳「Windows 已保護您的電腦」藍框、或自動被擋 | Windows 安全性 → 應用程式與瀏覽器控制 → 關 **Check apps and files** + **Smart App Control**。⚠️ 這是降低安全性,**要由使用者本人決定+本人操作**(Claude 的 classifier 會擋「用程式關防護」);且 SAC 關了不能再開(除非重裝) |
| **comtypes gen 無寫入權限** | 以非安裝者身分跑 pywinauto 時 `PermissionError: ...comtypes\gen\*.py` | 系統管理員跑 `icacls "<python>\Lib\site-packages\comtypes\gen" /grant "Users:(OI)(CI)M"` |

## 5. 連線穩定度（SSH）

- **傳檔一律用 `scp`**(走 sftp subsystem,比 `ssh "powershell ..."` 穩很多)。
- 目標是 VM(Parallels/VMware ARM 模擬 x64)時,**冷啟動/重開機後 sshd 會不穩**幾分鐘(`exec request failed` / `banner timeout`) → 用 `run_in_background` 跑 `until ssh echo; do sleep 6; done` 等它穩。
- 連續密集 SSH 會被 rate-limit → 每次呼叫間隔幾秒。
