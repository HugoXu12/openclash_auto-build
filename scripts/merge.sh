#!/bin/bash
set -e

ROOT=$(cd "$(dirname "$0")/.." && pwd)

RULE_SRC="$ROOT/rules-src"
RULE_DIR="$ROOT/rules"

echo "== 清空 rules 目录 =="
rm -rf "$RULE_DIR"
mkdir -p "$RULE_DIR"

TMP_DIR=$(mktemp -d)

################################
# 通用清洗函数
################################
clean_file() {
  sed 's/#.*//g' "$1" | sed '/^\s*$/d' | sed 's/[ \t]*$//'
}

################################
# 解析 rules.list
################################
CUSTOM_SECTION=$(awk '/\[Custom_link\]/{flag=1;next}/\[/{flag=0}flag' $RULE_SRC/rules.list)
PROXY_SECTION=$(awk '/\[Proxy-src_link\]/{flag=1;next}/\[/{flag=0}flag' $RULE_SRC/rules.list)
DIRECT_SECTION=$(awk '/\[Direct-src_link\]/{flag=1;next}/\[/{flag=0}flag' $RULE_SRC/rules.list)

################################
# 1. 处理 Custom_link
################################
echo "== 处理 Custom_link =="

echo "$CUSTOM_SECTION" | while IFS="|" read -r name url
do
  [ -z "$name" ] && continue
  file="$RULE_DIR/${name}.list"

  curl -sL "$url" > "$TMP_DIR/tmp.list"
  clean_file "$TMP_DIR/tmp.list" > "$file"
done

################################
# 2. 汇总 Proxy
################################
echo "== 处理 Proxy =="

> "$TMP_DIR/proxy_all.list"

for url in $PROXY_SECTION
do
  curl -sL "$url" >> "$TMP_DIR/proxy_all.list"
done

# 加入自定义
cat "$RULE_SRC/Proxy_custom.list" >> "$TMP_DIR/proxy_all.list"

clean_file "$TMP_DIR/proxy_all.list" | sort -u > "$TMP_DIR/proxy_clean.list"

################################
# 3. 汇总 Direct
################################
echo "== 处理 Direct =="

> "$TMP_DIR/direct_all.list"

for url in $DIRECT_SECTION
do
  curl -sL "$url" >> "$TMP_DIR/direct_all.list"
done

cat "$RULE_SRC/Direct_custom.list" >> "$TMP_DIR/direct_all.list"

clean_file "$TMP_DIR/direct_all.list" | sort -u > "$TMP_DIR/direct_clean.list"

################################
# 4. 去重逻辑（核心）
################################

# Proxy 去掉 Direct + Custom
cat "$RULE_DIR"/*.list "$TMP_DIR/direct_clean.list" > "$TMP_DIR/exclude_proxy.list"

grep -vxFf "$TMP_DIR/exclude_proxy.list" "$TMP_DIR/proxy_clean.list" > "$RULE_DIR/Proxy.list"
grep -xFf "$TMP_DIR/exclude_proxy.list" "$TMP_DIR/proxy_clean.list" > "$RULE_DIR/delete_proxy.list"

# Direct 去掉 Proxy + Custom
cat "$RULE_DIR"/*.list "$TMP_DIR/proxy_clean.list" > "$TMP_DIR/exclude_direct.list"

grep -vxFf "$TMP_DIR/exclude_direct.list" "$TMP_DIR/direct_clean.list" > "$RULE_DIR/Direct.list"
grep -xFf "$TMP_DIR/exclude_direct.list" "$TMP_DIR/direct_clean.list" > "$RULE_DIR/delete_direct.list"

echo "== 完成 =="
