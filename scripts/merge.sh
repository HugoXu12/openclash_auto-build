#!/usr/bin/env bash
set -e

BASE_DIR=$(cd "$(dirname "$0")/.." && pwd)
RULES_SRC="$BASE_DIR/rules-src"
RULES_DIR="$BASE_DIR/rules"
TMP_DIR="$BASE_DIR/tmp"

mkdir -p "$RULES_DIR" "$TMP_DIR"

echo "== 清空旧文件 =="
rm -rf "$RULES_DIR"/*
rm -rf "$TMP_DIR"/*
rm -f "$RULES_SRC/delete_proxy.list"
rm -f "$RULES_SRC/delete_direct.list"

RULE_FILE="$RULES_SRC/rules.list"

section=""
declare -A custom_map
proxy_links=()
direct_links=()

echo "== 解析 rules.list =="

while IFS= read -r line || [[ -n "$line" ]]; do
    line=$(echo "$line" | sed 's/\r//g')

    [[ -z "$line" || "$line" =~ ^# ]] && continue

    if [[ "$line" =~ ^\[.*\]$ ]]; then
        section="$line"
        continue
    fi

    case "$section" in
        "[Custom_link]")
            name=$(echo "$line" | cut -d'|' -f1)
            url=$(echo "$line" | cut -d'|' -f2)
            custom_map["$name"]="$url"
            ;;
        "[Proxy-src_link]")
            proxy_links+=("$line")
            ;;
        "[Direct-src_link]")
            direct_links+=("$line")
            ;;
    esac
done < "$RULE_FILE"

clean_file() {
    sed 's/\r//g' | sed 's/#.*//' | sed '/^\s*$/d' | sed 's/[ \t]*$//'
}

echo "== 生成 Custom RAW =="

custom_raw_files=()

for name in "${!custom_map[@]}"; do
    url=${custom_map[$name]}
    raw_file="$TMP_DIR/${name}_RAW.list"

    echo "下载 $name"
    curl -sL "$url" | clean_file | sort -u > "$raw_file"

    cp "$raw_file" "$RULES_DIR/${name}.list"
    custom_raw_files+=("$raw_file")
done

echo "== 合并 Proxy RAW =="

> "$TMP_DIR/Proxy_RAW.list"
for url in "${proxy_links[@]}"; do
    curl -sL "$url" | clean_file >> "$TMP_DIR/Proxy_RAW.list"
done

sort -u "$TMP_DIR/Proxy_RAW.list" -o "$TMP_DIR/Proxy_RAW.list"

echo "== 合并 Direct RAW =="

> "$TMP_DIR/Direct_RAW.list"
for url in "${direct_links[@]}"; do
    curl -sL "$url" | clean_file >> "$TMP_DIR/Direct_RAW.list"
done

sort -u "$TMP_DIR/Direct_RAW.list" -o "$TMP_DIR/Direct_RAW.list"

echo "== 去重处理 =="

touch "$RULES_SRC/Proxy_custom.list"
touch "$RULES_SRC/Direct_custom.list"

cat "${custom_raw_files[@]}" \
    "$RULES_SRC/Proxy_custom.list" \
    "$RULES_SRC/Direct_custom.list" \
    > "$TMP_DIR/all_known_rules.list"

sort -u "$TMP_DIR/all_known_rules.list" -o "$TMP_DIR/all_known_rules.list"

grep -vxFf "$TMP_DIR/all_known_rules.list" "$TMP_DIR/Proxy_RAW.list" > "$RULES_DIR/Proxy.list" || true
grep -xFf "$TMP_DIR/all_known_rules.list" "$TMP_DIR/Proxy_RAW.list" > "$RULES_SRC/delete_proxy.list" || true

grep -vxFf "$TMP_DIR/all_known_rules.list" "$TMP_DIR/Direct_RAW.list" > "$RULES_DIR/Direct.list" || true
grep -xFf "$TMP_DIR/all_known_rules.list" "$TMP_DIR/Direct_RAW.list" > "$RULES_SRC/delete_direct.list" || true

echo "== 完成规则生成 =="
