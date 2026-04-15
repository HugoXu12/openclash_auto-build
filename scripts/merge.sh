#!/bin/bash
set -e

BASE_DIR=$(cd "$(dirname "$0")/.." && pwd)
RULES_SRC="$BASE_DIR/rules-src"
RULES_DIR="$BASE_DIR/rules"

echo "===> 清空 rules 目录"
rm -rf "$RULES_DIR"
mkdir -p "$RULES_DIR"

# 去注释、去空行、去尾空格
clean_list() {
    sed 's/#.*//g' "$1" | sed '/^\s*$/d' | sed 's/[ \t]*$//' 
}

echo "===> 解析 rules.list"
CUSTOM_LINKS=$(awk '/\[Custom_link\]/,/\[/{if ($0 !~ /\[|^$/) print}' $RULES_SRC/rules.list)
PROXY_LINKS=$(awk '/\[Proxy-src_link\]/,/\[/{if ($0 !~ /\[|^$/) print}' $RULES_SRC/rules.list)
DIRECT_LINKS=$(awk '/\[Direct-src_link\]/,/\[/{if ($0 !~ /\[|^$/) print}' $RULES_SRC/rules.list)

echo "===> 下载 Custom_link 规则"
echo "$CUSTOM_LINKS" | while IFS="|" read name url
do
    echo "处理 $name"
    curl -sL "$url" -o "$RULES_SRC/${name}_RAW.list"
    clean_list "$RULES_SRC/${name}_RAW.list" | sort -u > "$RULES_SRC/${name}_RAW.tmp"
    mv "$RULES_SRC/${name}_RAW.tmp" "$RULES_SRC/${name}_RAW.list"

    cp "$RULES_SRC/${name}_RAW.list" "$RULES_DIR/${name}.list"
done

echo "===> 合并 Proxy RAW"
> "$RULES_SRC/Proxy_RAW.list"
for url in $PROXY_LINKS
do
    curl -sL "$url" >> "$RULES_SRC/Proxy_RAW.list"
    echo "" >> "$RULES_SRC/Proxy_RAW.list"
done

clean_list "$RULES_SRC/Proxy_RAW.list" | sort -u > "$RULES_SRC/Proxy_RAW.tmp"
mv "$RULES_SRC/Proxy_RAW.tmp" "$RULES_SRC/Proxy_RAW.list"

echo "===> 合并 Direct RAW"
> "$RULES_SRC/Direct_RAW.list"
for url in $DIRECT_LINKS
do
    curl -sL "$url" >> "$RULES_SRC/Direct_RAW.list"
    echo "" >> "$RULES_SRC/Direct_RAW.list"
done

clean_list "$RULES_SRC/Direct_RAW.list" | sort -u > "$RULES_SRC/Direct_RAW.tmp"
mv "$RULES_SRC/Direct_RAW.tmp" "$RULES_SRC/Direct_RAW.list"

echo "===> 生成 Proxy_exclude"
cat "$RULES_SRC"/*_RAW.list \
    "$RULES_SRC/Proxy_custom.list" \
    "$RULES_SRC/Direct_custom.list" \
    | sort -u > "$RULES_SRC/Proxy_exclude.list"

echo "===> 生成 Proxy.list"
grep -vxFf "$RULES_SRC/Proxy_exclude.list" "$RULES_SRC/Proxy_RAW.list" > "$RULES_DIR/Proxy.list" || true
grep -xFf "$RULES_SRC/Proxy_exclude.list" "$RULES_SRC/Proxy_RAW.list" > "$RULES_SRC/delete_proxy.list" || true

echo "===> 生成 Direct_exclude"
cat "$RULES_SRC/Proxy_exclude.list" \
    "$RULES_SRC/Direct_custom.list" \
    "$RULES_DIR/Proxy.list" \
    | sort -u > "$RULES_SRC/Direct_exclude.list"

echo "===> 生成 Direct.list"
grep -vxFf "$RULES_SRC/Direct_exclude.list" "$RULES_SRC/Direct_RAW.list" > "$RULES_DIR/Direct.list" || true
grep -xFf "$RULES_SRC/Direct_exclude.list" "$RULES_SRC/Direct_RAW.list" > "$RULES_SRC/delete_direct.list" || true

echo "===> 完成 merge"
