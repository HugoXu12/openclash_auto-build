#!/bin/bash

# 确保脚本遇到错误时停止执行
set -e

echo "=== 1. 初始化目录 ==="
mkdir -p tmp rules build rules-src config
# 清理旧文件保证环境无污染
rm -rf tmp/* rules/* build/*

# 定义清理格式的函数（去注释、去空行、去末尾空格、去重）
clean_list() {
    sed 's/#.*//g' | sed 's/[[:space:]]*$//' | awk 'NF' | sort -u
}

echo "=== 2. 解析 rules-src/rules.list ==="
RULES_LIST="rules-src/rules.list"

# 提取并下载 [Custom_link]
echo ">>> 处理 Custom_link..."
awk '/^\[Custom_link\]/{flag=1; next} /^\[.*\]/{flag=0} flag && NF' "$RULES_LIST" | while IFS="|" read -r name url; do
    echo "Downloading $name from $url"
    curl -sL "$url" | clean_list > "tmp/${name}_RAW.list"
    cp "tmp/${name}_RAW.list" "rules/${name}.list"
done

# 提取并下载 [Proxy-src_link]
echo ">>> 处理 Proxy-src_link..."
awk '/^\[Proxy-src_link\]/{flag=1; next} /^\[.*\]/{flag=0} flag && NF' "$RULES_LIST" | while read -r url; do
    curl -sL "$url" >> "tmp/Proxy_raw_merge.list"
done
cat "tmp/Proxy_raw_merge.list" | clean_list > "tmp/Proxy_tmp.list"

# 提取并下载 [Direct-src_link]
echo ">>> 处理 Direct-src_link..."
awk '/^\[Direct-src_link\]/{flag=1; next} /^\[.*\]/{flag=0} flag && NF' "$RULES_LIST" | while read -r url; do
    curl -sL "$url" >> "tmp/Direct_raw_merge.list"
done
cat "tmp/Direct_raw_merge.list" | clean_list > "tmp/Direct_tmp.list"


echo "=== 3. 规则对比与去重处理 ==="

# (步骤11) 生成 Proxy_exclude.list (Custom_RAW + Proxy_custom + Direct_custom)
cat tmp/*_RAW.list rules-src/Proxy_custom.list rules-src/Direct_custom.list 2>/dev/null | clean_list > tmp/Proxy_exclude.list

# (步骤11) 生成 Proxy.list 并提取 delete_proxy.list
# 使用 awk 对比：在 exclude 中的放进 delete，不在的放进 Proxy.list
awk 'NR==FNR{exclude[$0]; next} {
    if ($0 in exclude) print $0 > "tmp/delete_proxy.list";
    else print $0 > "rules/Proxy.list"
}' tmp/Proxy_exclude.list tmp/Proxy_tmp.list

# (步骤12) 生成 Direct_exclude.list (Proxy_exclude + rules/Proxy.list)
cat tmp/Proxy_exclude.list rules/Proxy.list 2>/dev/null | clean_list > tmp/Direct_exclude.list

# (步骤13) 生成 Direct.list 并提取 delete_direct.list
awk 'NR==FNR{exclude[$0]; next} {
    if ($0 in exclude) print $0 > "tmp/delete_direct.list";
    else print $0 > "rules/Direct.list"
}' tmp/Direct_exclude.list tmp/Direct_tmp.list

echo "=== 规则合并处理完成 ==="
