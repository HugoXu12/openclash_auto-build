#!/usr/bin/env bash
set -e

SRC_DIR="rules-src"
TMP_DIR="rules-src-provisional"
OUT_DIR="rules"

RULE_FILE="$SRC_DIR/rules.list"

mkdir -p "$TMP_DIR"
mkdir -p "$OUT_DIR"

# 清空目录（保留目录）
rm -f $TMP_DIR/*
rm -f $OUT_DIR/*

# 通用清洗函数
clean() {
    sed 's/#.*//g' "$1" \
    | sed '/^\s*$/d' \
    | sed 's/[ \t]*$//' \
    | sort -u
}

# 下载函数
download() {
    url="$1"
    out="$2"
    curl -L -s "$url" -o "$out"
}

echo "== 解析 rules.list =="

# 解析 Custom_link
awk '/\[Custom_link\]/,/\[/{if($0 !~ /\[.*\]/ && $0!="") print}' "$RULE_FILE" \
| while IFS='|' read -r name url
do
    echo "下载 Custom: $name"
    download "$url" "$TMP_DIR/${name}_RAW.list"
    clean "$TMP_DIR/${name}_RAW.list" > "$TMP_DIR/${name}.clean"

    cp "$TMP_DIR/${name}.clean" "$OUT_DIR/${name}.list"
done

# 解析 Proxy-src_link
awk '/\[Proxy-src_link\]/,/\[/{if($0 !~ /\[.*\]/ && $0!="") print}' "$RULE_FILE" \
| while read -r url
do
    download "$url" "$TMP_DIR/tmp_proxy.list"
    clean "$TMP_DIR/tmp_proxy.list" >> "$TMP_DIR/Proxy_RAW.list"
done

sort -u "$TMP_DIR/Proxy_RAW.list" -o "$TMP_DIR/Proxy_RAW.list"

# 解析 Direct-src_link
awk '/\[Direct-src_link\]/,/\[/{if($0 !~ /\[.*\]/ && $0!="") print}' "$RULE_FILE" \
| while read -r url
do
    download "$url" "$TMP_DIR/tmp_direct.list"
    clean "$TMP_DIR/tmp_direct.list" >> "$TMP_DIR/Direct_RAW.list"
done

sort -u "$TMP_DIR/Direct_RAW.list" -o "$TMP_DIR/Direct_RAW.list"

echo "== 构建 Proxy_exclude =="

cat $TMP_DIR/*_RAW.list \
    $SRC_DIR/Proxy_custom.list \
    $SRC_DIR/Direct_custom.list 2>/dev/null \
| clean /dev/stdin > "$TMP_DIR/Proxy_exclude.list"

echo "== 生成 Proxy.list =="

grep -vxFf "$TMP_DIR/Proxy_exclude.list" "$TMP_DIR/Proxy_RAW.list" > "$OUT_DIR/Proxy.list" || true
grep -xFf "$TMP_DIR/Proxy_exclude.list" "$TMP_DIR/Proxy_RAW.list" > "$TMP_DIR/delete_proxy.list" || true

echo "== 构建 Direct_exclude =="

cat "$TMP_DIR/Proxy_exclude.list" "$OUT_DIR/Proxy.list" \
| sort -u > "$TMP_DIR/Direct_exclude.list"

echo "== 生成 Direct.list =="

grep -vxFf "$TMP_DIR/Direct_exclude.list" "$TMP_DIR/Direct_RAW.list" > "$OUT_DIR/Direct.list" || true
grep -xFf "$TMP_DIR/Direct_exclude.list" "$TMP_DIR/Direct_RAW.list" > "$TMP_DIR/delete_direct.list" || true

echo "== 完成 merge.sh =="
