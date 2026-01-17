#!/bin/bash

# =============================================================================
# generate-screen-list.sh
# 產生 device-preview.html 的畫面清單 HTML
# =============================================================================

set -e

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "======================================"
echo "  畫面清單產生器"
echo "======================================"

# 確認當前目錄
if [ ! -f "device-preview.html" ]; then
    echo -e "${RED}錯誤：請在 04-ui-flow 目錄下執行此腳本${NC}"
    exit 1
fi

# 產生畫面清單 HTML
generate_screen_list() {
    local output=""
    local current_module=""
    local first_screen=""

    # 定義模組顏色
    declare -A MODULE_COLORS
    MODULE_COLORS[AUTH]="badge-auth"
    MODULE_COLORS[DASH]="badge-dash"
    MODULE_COLORS[VOCAB]="badge-vocab"
    MODULE_COLORS[TRAIN]="badge-train"
    MODULE_COLORS[PROGRESS]="badge-progress"
    MODULE_COLORS[PARENT]="badge-parent"
    MODULE_COLORS[SETTING]="badge-setting"
    MODULE_COLORS[REPORT]="badge-report"
    MODULE_COLORS[ONBOARD]="badge-onboard"

    # 定義模組中文名稱
    declare -A MODULE_NAMES
    MODULE_NAMES[AUTH]="認證"
    MODULE_NAMES[DASH]="首頁"
    MODULE_NAMES[VOCAB]="字庫"
    MODULE_NAMES[TRAIN]="練習"
    MODULE_NAMES[PROGRESS]="進度"
    MODULE_NAMES[PARENT]="家長"
    MODULE_NAMES[SETTING]="設定"
    MODULE_NAMES[REPORT]="報表"
    MODULE_NAMES[ONBOARD]="導覽"

    # 遍歷所有模組目錄
    for dir in auth dash vocab train progress parent setting report onboard; do
        if [ -d "$dir" ]; then
            local files=$(find "$dir" -maxdepth 1 -name "SCR-*.html" 2>/dev/null | sort)
            if [ -n "$files" ]; then
                local module_upper=$(echo "$dir" | tr '[:lower:]' '[:upper:]')
                local count=$(echo "$files" | wc -l | tr -d ' ')
                local badge_class="${MODULE_COLORS[$module_upper]:-badge-default}"

                output+="          <!-- $module_upper Module -->\n"
                output+="          <div class=\"mb-5\">\n"
                output+="            <p class=\"text-xs font-semibold text-gray-500 mb-2 flex items-center gap-2\">\n"
                output+="              <span class=\"w-2 h-2 rounded-full $badge_class\"></span>\n"
                output+="              $module_upper ($count)\n"
                output+="            </p>\n"
                output+="            <div class=\"space-y-1\">\n"

                local is_first=true
                for file in $files; do
                    local filename=$(basename "$file")
                    local screen_id=$(echo "$filename" | sed 's/\.html$//')
                    local iphone_path="iphone/$filename"

                    # 從檔案中提取標題
                    local title=$(grep -m1 '<title>' "$file" 2>/dev/null | sed 's/.*<title>\(.*\)<\/title>.*/\1/' | sed 's/ | 單字小達人//' | sed 's/^SCR-[A-Z]*-[0-9]* - //')
                    if [ -z "$title" ]; then
                        title="$screen_id"
                    fi

                    local active_class=""
                    if [ "$is_first" = true ] && [ -z "$first_screen" ]; then
                        active_class=" active"
                        first_screen="$dir/$filename"
                        is_first=false
                    fi

                    output+="              <div class=\"screen-item$active_class px-3 py-2.5 rounded-lg cursor-pointer\" onclick=\"loadScreen('$dir/$filename', this)\" data-iphone=\"$iphone_path\">\n"
                    output+="                <span class=\"text-sm text-gray-700\">$screen_id $title</span>\n"
                    output+="              </div>\n"
                done

                output+="            </div>\n"
                output+="          </div>\n\n"
            fi
        fi
    done

    echo "$first_screen"
    echo "---SCREEN_LIST---"
    echo -e "$output"
}

# 產生清單
echo ""
echo "掃描畫面檔案..."
result=$(generate_screen_list)
first_screen=$(echo "$result" | head -1)
screen_list=$(echo "$result" | sed '1d' | sed '1d')

# 備份 device-preview.html
cp device-preview.html device-preview.html.bak

echo "第一個畫面: $first_screen"

# 更新 iframe 預設 src
if [ -n "$first_screen" ]; then
    sed -i '' "s|src=\"auth/SCR-AUTH-001-login.html\"|src=\"$first_screen\"|g" device-preview.html
    sed -i '' "s|currentScreen = 'auth/SCR-AUTH-001-login.html'|currentScreen = '$first_screen'|g" device-preview.html
    echo -e "${GREEN}✅ iframe src 已更新為: $first_screen${NC}"
fi

# 將畫面清單寫入臨時檔案
echo -e "$screen_list" > /tmp/screen_list_temp.html

echo ""
echo -e "${GREEN}✅ 畫面清單已產生到 /tmp/screen_list_temp.html${NC}"
echo ""
echo "請手動將清單內容替換到 device-preview.html 的畫面清單區域"
echo "（搜尋 '<!-- Example AUTH Module -->' 並替換該區塊）"
echo ""

# 顯示統計
echo "統計："
find . -name "SCR-*.html" -not -path "./iphone/*" | wc -l | xargs echo "  總畫面數:"

echo ""
echo "完成！"
