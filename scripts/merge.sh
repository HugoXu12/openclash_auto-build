#!/bin/bash

set -e

RULES_DIR="rules"
SRC_DIR="rules-src"

rm -rf $RULES_DIR
mkdir -p $RULES_DIR

TMP_ALL=$(mktemp)

echo "===> 解析 rules.list"

section=""

while IFS= read -r line || [ -n "$line" ]; do
    line=$(echo "$line" | sed 's/\r//g')

    [[ -z "$line" || "$line" =~ ^# ]] && continue

    if [[ "$line" =~ \[(.*)\] ]]; then
        section="${BASH_REMATCH[1]}"
        continue
    fi

    case $section in

    Custom_link)
        name=$(echo "$line" | cut -d '|' -f1)
        url=$(echo "$line" | cut -d '|' -f2)

        echo "===> 下载 Custom: $name"

        curl -s "$url" \
        | sed 's/#.*//' \
        | sed '/^\s*$/d' \
        | sed 's/[ \t]*$//' \
        > "$RULES_DIR/$name.list"

        cat "$RULES_DIR/$name.list" >> "$TMP_ALL"
        ;;

    Proxy-src_link)
        echo "$line" >> proxy_links.tmp
        ;;

    Direct-src_link)
        echo "$line" >> direct_links.tmp
        ;;

    esac

done < "$SRC_DIR/rules.list"

##################################
# Proxy 汇总
##################################

> proxy_all.tmp

while read -r url; do
    echo "===> 下载 Proxy: $url"

    curl -s "$url" \
    | sed 's/#.*//' \
    | sed '/^\s*$/d' \
    | sed 's/[ \t]*$//' \
    >> proxy_all.tmp

done < proxy_links.tmp

cat "$SRC_DIR/Proxy_custom.list" >> proxy_all.tmp
cat "$SRC_DIR/Direct_custom.list" >> proxy_all.tmp

##################################
# Direct 汇总
##################################

> direct_all.tmp

while read -r url; do
    echo "===> 下载 Direct: $url"

    curl -s "$url" \
    | sed 's/#.*//' \
    | sed '/^\s*$/d' \
    | sed 's/[ \t]*$//' \
    >> direct_all.tmp

done < direct_links.tmp

cat "$SRC_DIR/Direct_custom.list" >> direct_all.tmp
cat "$SRC_DIR/Proxy_custom.list" >> direct_all.tmp

##################################
# 去重逻辑
##################################

sort -u "$TMP_ALL" > custom_all.tmp

grep -vxFf custom_all.tmp proxy_all.tmp | sort -u > "$RULES_DIR/Proxy.list"
grep -Fxf custom_all.tmp proxy_all.tmp > "$RULES_DIR/delete_proxy.list"

grep -vxFf custom_all.tmp direct_all.tmp | sort -u > "$RULES_DIR/Direct.list"
grep -Fxf custom_all.tmp direct_all.tmp > "$RULES_DIR/delete_direct.list"

echo "===> 完成"
