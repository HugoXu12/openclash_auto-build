#!/usr/bin/env bash
set -e

SRC_DIR="rules-src"
TMP_DIR="rules-src-provisional"
OUT_DIR="rules"

mkdir -p $TMP_DIR $OUT_DIR

echo "== 清理旧文件 =="
rm -rf $TMP_DIR/*
rm -rf $OUT_DIR/*

#######################################
# 工具函数
#######################################
clean_file() {
  sed 's/#.*//g' "$1" | sed '/^\s*$/d' | sed 's/[ \t]*$//' | sort -u
}

download_and_clean() {
  url="$1"
  curl -sL "$url" | sed 's/#.*//g' | sed '/^\s*$/d' | sed 's/[ \t]*$//'
}

#######################################
# 解析 rules.list
#######################################
CUSTOM_LINKS=$(awk '/\[Custom_link\]/,/^\[/{if($0!~/\[|^$/)print}' $SRC_DIR/rules.list)
PROXY_LINKS=$(awk '/\[Proxy-src_link\]/,/^\[/{if($0!~/\[|^$/)print}' $SRC_DIR/rules.list)
DIRECT_LINKS=$(awk '/\[Direct-src_link\]/,/^\[/{if($0!~/\[|^$/)print}' $SRC_DIR/rules.list)

#######################################
# 1. 处理 Custom_link
#######################################
echo "== 处理 Custom_link =="

CUSTOM_NAMES=()

while IFS="|" read -r name url; do
  [ -z "$name" ] && continue

  CUSTOM_NAMES+=("$name")

  echo "下载 $name"

  download_and_clean "$url" > "$TMP_DIR/${name}_RAW.list"

  cp "$TMP_DIR/${name}_RAW.list" "$OUT_DIR/${name}.list"

done <<< "$CUSTOM_LINKS"

#######################################
# 2. Proxy_RAW
#######################################
echo "== 构建 Proxy_RAW =="

> $TMP_DIR/Proxy_RAW.list

for url in $PROXY_LINKS; do
  download_and_clean "$url" >> $TMP_DIR/Proxy_RAW.list
done

clean_file $TMP_DIR/Proxy_RAW.list > $TMP_DIR/Proxy_RAW_clean.list
mv $TMP_DIR/Proxy_RAW_clean.list $TMP_DIR/Proxy_RAW.list

#######################################
# 3. Direct_RAW
#######################################
echo "== 构建 Direct_RAW =="

> $TMP_DIR/Direct_RAW.list

for url in $DIRECT_LINKS; do
  download_and_clean "$url" >> $TMP_DIR/Direct_RAW.list
done

clean_file $TMP_DIR/Direct_RAW.list > $TMP_DIR/Direct_RAW_clean.list
mv $TMP_DIR/Direct_RAW_clean.list $TMP_DIR/Direct_RAW.list

#######################################
# 4. Proxy_exclude
#######################################
echo "== 构建 Proxy_exclude =="

> $TMP_DIR/Proxy_exclude.list

# Custom
for name in "${CUSTOM_NAMES[@]}"; do
  cat "$TMP_DIR/${name}_RAW.list" >> $TMP_DIR/Proxy_exclude.list
done

# Direct_custom
clean_file $SRC_DIR/Direct_custom.list >> $TMP_DIR/Proxy_exclude.list

clean_file $TMP_DIR/Proxy_exclude.list > $TMP_DIR/tmp && mv $TMP_DIR/tmp $TMP_DIR/Proxy_exclude.list

#######################################
# 5. Proxy.list
#######################################
echo "== 生成 Proxy.list =="

grep -vxFf $TMP_DIR/Proxy_exclude.list $TMP_DIR/Proxy_RAW.list > $OUT_DIR/Proxy.list || true

clean_file $OUT_DIR/Proxy.list > $TMP_DIR/tmp && mv $TMP_DIR/tmp $OUT_DIR/Proxy.list

grep -Fxf $TMP_DIR/Proxy_exclude.list $TMP_DIR/Proxy_RAW.list > $TMP_DIR/delete_proxy.list || true

#######################################
# 6. Direct_exclude
#######################################
echo "== 构建 Direct_exclude =="

> $TMP_DIR/Direct_exclude.list

# Custom
for name in "${CUSTOM_NAMES[@]}"; do
  cat "$TMP_DIR/${name}_RAW.list" >> $TMP_DIR/Direct_exclude.list
done

# Proxy + Proxy_custom
cat $OUT_DIR/Proxy.list >> $TMP_DIR/Direct_exclude.list
clean_file $SRC_DIR/Proxy_custom.list >> $TMP_DIR/Direct_exclude.list

clean_file $TMP_DIR/Direct_exclude.list > $TMP_DIR/tmp && mv $TMP_DIR/tmp $TMP_DIR/Direct_exclude.list

#######################################
# 7. Direct.list
#######################################
echo "== 生成 Direct.list =="

grep -vxFf $TMP_DIR/Direct_exclude.list $TMP_DIR/Direct_RAW.list > $OUT_DIR/Direct.list || true

clean_file $OUT_DIR/Direct.list > $TMP_DIR/tmp && mv $TMP_DIR/tmp $OUT_DIR/Direct.list

grep -Fxf $TMP_DIR/Direct_exclude.list $TMP_DIR/Direct_RAW.list > $TMP_DIR/delete_direct.list || true

echo "== 完成规则构建 =="
