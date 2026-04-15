#!/bin/bash

set -e

ROOT_DIR=$(pwd)
SRC_DIR="$ROOT_DIR/rules-src"
RULES_DIR="$ROOT_DIR/rules"

rm -rf "$RULES_DIR"
mkdir -p "$RULES_DIR"

echo "== Parsing rules.list =="

CUSTOM_FILE="$SRC_DIR/rules.list"

# ---------------------------
# 1. Custom_link
# ---------------------------
awk '
/^\[Custom_link\]/ {flag=1; next}
/^\[/ {flag=0}
flag && NF {
    split($0,a,"|");
    print a[1]"|"a[2]
}
' "$CUSTOM_FILE" | while IFS="|" read -r name url; do

    echo "Downloading $name"

    curl -s "$url" \
    | sed '/^#/d' \
    | sed '/^$/d' \
    | sed 's/[ \t]*$//' \
    > "$RULES_DIR/$name.list"

done

# ---------------------------
# 2. Proxy-src_link
# ---------------------------
awk '
/^\[Proxy-src_link\]/ {flag=1; next}
/^\[/ {flag=0}
flag && NF {print $0}
' "$CUSTOM_FILE" > /tmp/proxy_src.txt

# merge proxy custom
cat "$SRC_DIR/Proxy_custom.list" >> /tmp/proxy_src.txt

# clean
cat /tmp/proxy_src.txt \
| sed '/^#/d' \
| sed '/^$/d' \
| sed 's/[ \t]*$//' \
| sort -u > "$RULES_DIR/Proxy.list"

# ---------------------------
# 3. Direct-src_link
# ---------------------------
awk '
/^\[Direct-src_link\]/ {flag=1; next}
/^\[/ {flag=0}
flag && NF {print $0}
' "$CUSTOM_FILE" > /tmp/direct_src.txt

cat "$SRC_DIR/Direct_custom.list" >> /tmp/direct_src.txt

cat /tmp/direct_src.txt \
| sed '/^#/d' \
| sed '/^$/d' \
| sed 's/[ \t]*$//' \
| sort -u > "$RULES_DIR/Direct.list"

# ---------------------------
# 4. delete lists（差集）
# ---------------------------

comm -23 <(sort "$RULES_DIR/Proxy.list") <(cat "$SRC_DIR/Proxy_custom.list" "$SRC_DIR/Direct_custom.list" | sort -u) \
> "$RULES_DIR/delete_proxy.list"

comm -23 <(sort "$RULES_DIR/Direct.list") <(cat "$SRC_DIR/Proxy_custom.list" "$SRC_DIR/Direct_custom.list" | sort -u) \
> "$RULES_DIR/delete_direct.list"

echo "Merge done."
