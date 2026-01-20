#!/bin/bash
# doc-indexer-skill 安裝腳本 (macOS/Linux)
# 用法: bash setup.sh

set -e

echo "=========================================="
echo "  doc-indexer-skill 安裝程式"
echo "  平台: macOS / Linux"
echo "=========================================="
echo ""

# 設定變數
SKILL_DIR="$HOME/.claude/skills/doc-indexer-skill"
INSTALL_DIR="$HOME/.local/share/doc-indexer"
JAR_NAME="doc-indexer-1.0.0-all.jar"
JAR_URL="https://github.com/jrjohn/doc-indexer/releases/latest/download/${JAR_NAME}"
JAVA_MIN_VERSION="17"

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函數: 檢查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 函數: 取得 Java 版本
get_java_version() {
    if command_exists java; then
        java -version 2>&1 | head -n 1 | awk -F '"' '{print $2}' | cut -d'.' -f1
    else
        echo "0"
    fi
}

# 函數: 安裝 Java (macOS)
install_java_macos() {
    echo -e "${YELLOW}正在安裝 Java ${JAVA_MIN_VERSION}...${NC}"

    if command_exists brew; then
        brew install openjdk@${JAVA_MIN_VERSION}
        # 設定 JAVA_HOME
        JAVA_HOME="$(brew --prefix openjdk@${JAVA_MIN_VERSION})"
        echo "export JAVA_HOME=\"${JAVA_HOME}\"" >> "$HOME/.zshrc"
        echo "export PATH=\"\$JAVA_HOME/bin:\$PATH\"" >> "$HOME/.zshrc"
        source "$HOME/.zshrc"
    else
        echo -e "${RED}請先安裝 Homebrew: https://brew.sh${NC}"
        echo "或手動安裝 Java ${JAVA_MIN_VERSION}: https://adoptium.net/"
        exit 1
    fi
}

# 函數: 安裝 Java (Linux)
install_java_linux() {
    echo -e "${YELLOW}正在安裝 Java ${JAVA_MIN_VERSION}...${NC}"

    if command_exists apt-get; then
        sudo apt-get update
        sudo apt-get install -y openjdk-${JAVA_MIN_VERSION}-jdk
    elif command_exists yum; then
        sudo yum install -y java-${JAVA_MIN_VERSION}-openjdk-devel
    elif command_exists dnf; then
        sudo dnf install -y java-${JAVA_MIN_VERSION}-openjdk-devel
    else
        echo -e "${RED}無法自動安裝 Java，請手動安裝 Java ${JAVA_MIN_VERSION}${NC}"
        echo "下載: https://adoptium.net/"
        exit 1
    fi
}

# 步驟 1: 檢查/安裝 Java
echo "步驟 1/4: 檢查 Java 環境..."
JAVA_VERSION=$(get_java_version)

if [ "$JAVA_VERSION" -lt "$JAVA_MIN_VERSION" ]; then
    echo -e "${YELLOW}Java 版本不足 (目前: ${JAVA_VERSION}, 需要: ${JAVA_MIN_VERSION})${NC}"

    read -p "是否自動安裝 Java ${JAVA_MIN_VERSION}? (y/n): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            install_java_macos
        else
            install_java_linux
        fi
    else
        echo -e "${RED}請手動安裝 Java ${JAVA_MIN_VERSION} 後重新執行此腳本${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Java ${JAVA_VERSION} 已安裝${NC}"
fi

# 步驟 2: 建立安裝目錄
echo ""
echo "步驟 2/4: 建立安裝目錄..."
mkdir -p "$INSTALL_DIR"
echo -e "${GREEN}✓ 安裝目錄: ${INSTALL_DIR}${NC}"

# 步驟 3: 下載 JAR
echo ""
echo "步驟 3/4: 下載 doc-indexer..."

JAR_PATH="${INSTALL_DIR}/${JAR_NAME}"

if [ -f "$JAR_PATH" ]; then
    echo -e "${YELLOW}JAR 檔案已存在，是否重新下載? (y/n): ${NC}"
    read -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "跳過下載"
    else
        rm -f "$JAR_PATH"
    fi
fi

if [ ! -f "$JAR_PATH" ]; then
    if command_exists curl; then
        echo "從 GitHub 下載..."
        if curl -L -o "$JAR_PATH" "$JAR_URL" 2>/dev/null; then
            echo -e "${GREEN}✓ 下載完成${NC}"
        else
            echo -e "${YELLOW}GitHub 下載失敗，嘗試從原始碼建置...${NC}"
            SOURCE_DIR="${SKILL_DIR}/source"
            if [ -d "$SOURCE_DIR" ] && [ -f "$SOURCE_DIR/gradlew" ]; then
                echo "從原始碼建置中..."
                cd "$SOURCE_DIR"
                chmod +x gradlew
                if ./gradlew shadowJar --no-daemon; then
                    SOURCE_JAR="$SOURCE_DIR/build/libs/${JAR_NAME}"
                    if [ -f "$SOURCE_JAR" ]; then
                        cp "$SOURCE_JAR" "$JAR_PATH"
                        echo -e "${GREEN}✓ 從原始碼建置完成${NC}"
                    fi
                else
                    echo -e "${RED}建置失敗${NC}"
                fi
                cd - > /dev/null
            else
                echo -e "${RED}無法找到原始碼，請手動下載 JAR${NC}"
                exit 1
            fi
        fi
    fi
fi

# 步驟 4: 產生設定檔
echo ""
echo "步驟 4/4: 產生設定檔..."

# 偵測 JAVA_HOME
if [ -z "$JAVA_HOME" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        JAVA_HOME=$(/usr/libexec/java_home -v ${JAVA_MIN_VERSION} 2>/dev/null || echo "")
    else
        JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
    fi
fi

CONFIG_FILE="${SKILL_DIR}/config.env"
cat > "$CONFIG_FILE" << EOF
# doc-indexer-skill 設定檔
# 自動產生於: $(date)
# 平台: $(uname -s)

JAVA_HOME="${JAVA_HOME}"
DOC_INDEXER_JAR="${JAR_PATH}"
DOC_INDEXER_INDEX="\$HOME/.local/share/doc-indexer/index-data"
EOF

echo -e "${GREEN}✓ 設定檔已產生: ${CONFIG_FILE}${NC}"

# 完成
echo ""
echo "=========================================="
echo -e "${GREEN}  安裝完成!${NC}"
echo "=========================================="
echo ""
echo "設定資訊:"
echo "  JAVA_HOME: ${JAVA_HOME}"
echo "  JAR 位置:  ${JAR_PATH}"
echo "  設定檔:    ${CONFIG_FILE}"
echo ""
echo "使用方式:"
echo "  /doc-indexer search \"關鍵字\""
echo "  /doc-indexer index \"/path/to/docs\""
echo ""
