#!/bin/bash

set -eo pipefail
set -x  # 开启调试日志（非常重要）

BASE_DIR=$(cd "$(dirname "$0")/.." && pwd)
RULES_SRC="$BASE_DIR/rules-src"
RULES_DIR="$BASE_DIR/rules"

mkdir -p "$RULES_SRC"
mkdir -p "$RULES_DIR"

echo "===> 清空 rules 目录"
rm -rf "$RULES_DIR"
mkdir -p "$RULES_DIR"

# 清洗函数
clean_list() {
    sed 's/#.*//g' "$1" | sed '/^\s*$/d' | sed 's/[ \t]*$//' || true
}

# 解析 rules.list（稳定版）
parse_section() {
    awk -v section="$1" '
    $0 ~ "\\["section"\\]" {flag=1; next}
    /^\[/ {flag=0}
    flag && NF
    ' "$RULES_SRC/rules.list" || true
}

CUSTOM_LINKS=$(parse_section "Custom_link")
PROXY_LINKS=$(parse_section "Proxy-src_link")
DIRECT_LINKS=$(parse_section "Direct-src_link")

echo "===> 下载 Custom_link 规则"

echo "$CUSTOM_LINKS" | while IFS="|" read -r name url
do
    [ -z "$name" ] && continue

    echo "处理 $name"

    RAW_FILE="$RULES_SRC/${name}_RAW.list"

    curl -L --retry 3 --connect-timeout 10 -s "$url" -o "$RAW_FILE" \
        || echo "❌ 下载失败: $url"

    if [ -f "$RAW_FILE" ]; then
        clean_list "$RAW_FILE" | sort -u > "${RAW_FILE}.tmp" || true
        mv "${RAW_FILE}.tmp" "$RAW_FILE" || true
        cp "$RAW_FILE" "$RULES_DIR/${name}.list" || true
    else
        echo "⚠️ 文件不存在: $RAW_FILE"
    fi

done

echo "===> 合并 Proxy RAW"
> "$RULES_SRC/Proxy_RAW.list"

for url in $PROXY_LINKS
do
    curl -L --retry 3 --connect-timeout 10 -s "$url" >> "$RULES_SRC/Proxy_RAW.list" \
        || echo "❌ Proxy 下载失败: $url"
    echo "" >> "$RULES_SRC/Proxy_RAW.list"
done

clean_list "$RULES_SRC/Proxy_RAW.list" | sort -u > "$RULES_SRC/Proxy_RAW.tmp" || true
mv "$RULES_SRC/Proxy_RAW.tmp" "$RULES_SRC/Proxy_RAW.list" || true

echo "===> 合并 Direct RAW"
> "$RULES_SRC/Direct_RAW.list"

for url in $DIRECT_LINKS
do
    curl -L --retry 3 --connect-timeout 10 -s "$url" >> "$RULES_SRC/Direct_RAW.list" \
        || echo "❌ Direct 下载失败: $url"
    echo "" >> "$RULES_SRC/Direct_RAW.list"
done

clean_list "$RULES_SRC/Direct_RAW.list" | sort -u > "$RULES_SRC/Direct_RAW.tmp" || true
mv "$RULES_SRC/Direct_RAW.tmp" "$RULES_SRC/Direct_RAW.list" || true

echo "===> 生成 Proxy_exclude"
cat "$RULES_SRC"/*_RAW.list \
    "$RULES_SRC/Proxy_custom.list" \
    "$RULES_SRC/Direct_custom.list" \
    2>/dev/null | sort -u > "$RULES_SRC/Proxy_exclude.list" || true

echo "===> 生成 Proxy.list"

grep -vxFf "$RULES_SRC/Proxy_exclude.list" "$RULES_SRC/Proxy_RAW.list" \
    > "$RULES_DIR/Proxy.list" || true

grep -xFf "$RULES_SRC/Proxy_exclude.list" "$RULES_SRC/Proxy_RAW.list" \
    > "$RULES_SRC/delete_proxy.list" || true

echo "===> 生成 Direct_exclude"

cat "$RULES_SRC/Proxy_exclude.list" \
    "$RULES_SRC/Direct_custom.list" \
    "$RULES_DIR/Proxy.list" \
    2>/dev/null | sort -u > "$RULES_SRC/Direct_exclude.list" || true

echo "===> 生成 Direct.list"

grep -vxFf "$RULES_SRC/Direct_exclude.list" "$RULES_SRC/Direct_RAW.list" \
    > "$RULES_DIR/Direct.list" || true

grep -xFf "$RULES_SRC/Direct_exclude.list" "$RULES_SRC/Direct_RAW.list" \
    > "$RULES_SRC/delete_direct.list" || true

echo "✅ merge 完成"
