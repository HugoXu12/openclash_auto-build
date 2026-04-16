#!/bin/bash

set -e

SRC_DIR="rules-src"
TMP_DIR="rules-src-provisional"
OUT_DIR="rules"

RULE_FILE="$SRC_DIR/rules.list"

# ========= 通用清洗函数 =========
clean_file() {
    sed 's/#.*//g' "$1" | sed '/^\s*$/d' | sed 's/[ \t]*$//' | sort -u
}

# ========= Step 7 =========
clean_file "$SRC_DIR/Proxy_custom.list" > "$TMP_DIR/Proxy_custom_RAW.list"

# ========= Step 8 =========
clean_file "$SRC_DIR/Direct_custom.list" > "$TMP_DIR/Direct_custom_RAW.list"

# ========= 解析 rules.list =========
section=""
while read -r line; do
    [[ -z "$line" || "$line" =~ ^# ]] && continue

    if [[ "$line" =~ \[.*\] ]]; then
        section="$line"
        continue
    fi

    case "$section" in
        "[Custom_link]")
            name=$(echo "$line" | cut -d '|' -f1)
            url=$(echo "$line" | cut -d '|' -f2)

            curl -sL "$url" | clean_file /dev/stdin > "$TMP_DIR/${name}_RAW.list"
            ;;

        "[Proxy-src_link]")
            curl -sL "$line" >> "$TMP_DIR/Proxy_RAW.tmp"
            ;;

        "[Direct-src_link]")
            curl -sL "$line" >> "$TMP_DIR/Direct_RAW.tmp"
            ;;
    esac
done < "$RULE_FILE"

# ========= Step 10 =========
clean_file "$TMP_DIR/Proxy_RAW.tmp" > "$TMP_DIR/Proxy_RAW.list"

# ========= Step 11 =========
clean_file "$TMP_DIR/Direct_RAW.tmp" > "$TMP_DIR/Direct_RAW.list"

# ========= Step 12 =========
cat \
  "$TMP_DIR/Proxy_custom_RAW.list" \
  "$TMP_DIR/Direct_custom_RAW.list" \
  "$TMP_DIR/"*_RAW.list \
  | sort -u > "$TMP_DIR/Proxy_exclude.list"

# ========= Step 13 =========
cat \
  "$TMP_DIR/Proxy_RAW.list" \
  "$TMP_DIR/Proxy_exclude.list" \
  | sort -u > "$TMP_DIR/Direct_exclude.list"

# ========= Step 14 =========
grep -vxFf "$TMP_DIR/Proxy_exclude.list" "$TMP_DIR/Proxy_RAW.list" > "$OUT_DIR/Proxy.list"
grep -xFf "$TMP_DIR/Proxy_exclude.list" "$TMP_DIR/Proxy_RAW.list" > "$TMP_DIR/delete_proxy.list"

# ========= Step 15 =========
grep -vxFf "$TMP_DIR/Direct_exclude.list" "$TMP_DIR/Direct_RAW.list" > "$OUT_DIR/Direct.list"
grep -xFf "$TMP_DIR/Direct_exclude.list" "$TMP_DIR/Direct_RAW.list" > "$TMP_DIR/delete_direct.list"

# ========= Step 16 =========
for file in "$TMP_DIR/"*_RAW.list; do
    name=$(basename "$file" _RAW.list)
    case "$name" in
        Proxy*|Direct*) continue ;;
    esac
    cp "$file" "$OUT_DIR/${name}.list"
done

echo "Merge completed"
