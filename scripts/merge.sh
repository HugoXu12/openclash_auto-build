#!/bin/bash
set -e

echo "=== 1. 初始化文件夹 ==="
rm -rf rules-src-provisional rules build
mkdir -p rules-src-provisional rules build
touch rules-src/Proxy_custom.list rules-src/Direct_custom.list

# 定义清理函数（去注释、去空行、去末尾空格、去重）
clean_list() {
    local file=$1
    if [ -f "$file" ]; then
        sed -i 's/#.*//g' "$file"          # 删注释
        sed -i '/^[[:space:]]*$/d' "$file" # 删空行
        sed -i 's/[[:space:]]*$//' "$file" # 删末尾空格
        sort -u "$file" -o "$file"         # 排序并去重
    fi
}

# 清理可能携带的乱码或引号（针对 url 的处理函数）
clean_url() {
    echo "$1" | tr -d '"' | tr -d "'" | tr -d '\r'
}

echo "=== 2-3. 处理 Custom_link ==="
awk '/^\[Custom_link\]/{flag=1; next} /^\[/{flag=0} flag && NF' rules-src/rules.list | while IFS='|' read -r name url; do
    name=$(echo "$name" | xargs)
    url=$(clean_url "$url")
    if [ -n "$name" ] && [ -n "$url" ]; then
        echo "下载 Custom_link: $name"
        wget -qO "rules-src-provisional/${name}_RAW.list" "$url"
        clean_list "rules-src-provisional/${name}_RAW.list"
        cp "rules-src-provisional/${name}_RAW.list" "rules/${name}.list"
    fi
done

echo "=== 4. 处理 Proxy-src_link ==="
awk '/^\[Proxy-src_link\]/{flag=1; next} /^\[/{flag=0} flag && NF' rules-src/rules.list | while read -r url; do
    url=$(clean_url "$url")
    if [ -n "$url" ] && [[ ! "$url" =~ ^# ]]; then
        wget -qO- "$url" >> "rules-src-provisional/Proxy_RAW.list"
    fi
done
clean_list "rules-src-provisional/Proxy_RAW.list"

echo "=== 5. 处理 Direct-src_link ==="
awk '/^\[Direct-src_link\]/{flag=1; next} /^\[/{flag=0} flag && NF' rules-src/rules.list | while read -r url; do
    url=$(clean_url "$url")
    if [ -n "$url" ] && [[ ! "$url" =~ ^# ]]; then
        wget -qO- "$url" >> "rules-src-provisional/Direct_RAW.list"
    fi
done
clean_list "rules-src-provisional/Direct_RAW.list"

echo "=== 6. 生成 Proxy_exclude.list ==="
# 汇总 Custom_RAW + Custom 个人收集
cat rules-src-provisional/*_RAW.list rules-src/Proxy_custom.list rules-src/Direct_custom.list 2>/dev/null > rules-src-provisional/Proxy_exclude.list
clean_list "rules-src-provisional/Proxy_exclude.list"

echo "=== 7. 生成 rules/Proxy.list & delete_proxy ==="
# 对比去重，使用 || true 防止 grep 在没有匹配时退出
grep -v -x -F -f rules-src-provisional/Proxy_exclude.list rules-src-provisional/Proxy_RAW.list > rules/Proxy.list || true
grep -x -F -f rules-src-provisional/Proxy_exclude.list rules-src-provisional/Proxy_RAW.list > rules-src-provisional/delete_proxy.list || true

echo "=== 8. 生成 Direct_exclude.list ==="
# 汇总 Proxy_exclude + Direct_custom + 生成的 Proxy.list
cat rules-src-provisional/Proxy_exclude.list rules-src/Direct_custom.list rules/Proxy.list 2>/dev/null > rules-src-provisional/Direct_exclude.list
clean_list "rules-src-provisional/Direct_exclude.list"

echo "=== 9. 生成 rules/Direct.list & delete_direct ==="
grep -v -x -F -f rules-src-provisional/Direct_exclude.list rules-src-provisional/Direct_RAW.list > rules/Direct.list || true
grep -x -F -f rules-src-provisional/Direct_exclude.list rules-src-provisional/Direct_RAW.list > rules-src-provisional/delete_direct.list || true

echo "=== 10. 转移并清理所有最终 Rules ==="
cp rules-src/Proxy_custom.list rules/Proxy_custom.list
cp rules-src/Direct_custom.list rules/Direct_custom.list

for f in rules/*.list; do
    clean_list "$f"
done

echo "规则合并去重完成！"
