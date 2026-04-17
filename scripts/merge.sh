#!/bin/bash

# 确保脚本遇到错误时停止执行
set -e

echo "=== 1. 初始化文件夹 ==="
rm -rf tmp rules build
mkdir -p tmp rules build

#如果文件不存在，就自动创建一个空的白文件；如果文件已经存在，就只更新一下它的修改时间，不会破坏里面的内容。
touch rules-src/Proxy_custom.list rules-src/Direct_custom.list rules-src/rules.list

# 定义清理函数（去除 # 注释、空行、末尾空格，并去重）
clean_list() {
    local file=$1
    if [ -f "$file" ]; then
        sed -i 's/#.*//g' "$file"          # 删#号后面的注释
        sed -i 's/[[:space:]]*$//' "$file" # 删末尾空格
        sed -i '/^[[:space:]]*$/d' "$file" # 删空行
        sort -u "$file" -o "$file"         # 排序并去重
    fi
}

# 清理链接中可能携带的乱码或引号
clean_url() {
    echo "$1" | tr -d '"' | tr -d "'" | tr -d '\r'
}

echo "=== 2. 处理 [rules-src/rules.list里面的Custom_link] ==="
awk '/^\[Custom_link\]/{flag=1; next} /^\[/{flag=0} flag && NF' rules-src/rules.list | while IFS='|' read -r name url; do
    name=$(echo "$name" | xargs)
    url=$(clean_url "$url")
    if [ -n "$name" ] && [ -n "$url" ]; then
        echo "正在下载 Custom 规则: $name"
        wget -qO "tmp/${name}_RAW.list" "$url"
        clean_list "tmp/${name}_RAW.list"
        cp "tmp/${name}_RAW.list" "rules/${name}.list"
    fi
done

echo "=== 3. 处理 [rules-src/rules.list里面的Proxy-src_link] ==="
awk '/^\[Proxy-src_link\]/{flag=1; next} /^\[/{flag=0} flag && NF' rules-src/rules.list | while read -r url; do
    url=$(clean_url "$url")
    if [ -n "$url" ] && [[ ! "$url" =~ ^# ]]; then
        wget -qO- "$url" >> "tmp/Proxy_tmp.list"
    fi
done
clean_list "tmp/Proxy_tmp.list"

echo "=== 4. 处理 [rules-src/rules.list里面的Direct-src_link] ==="
awk '/^\[Direct-src_link\]/{flag=1; next} /^\[/{flag=0} flag && NF' rules-src/rules.list | while read -r url; do
    url=$(clean_url "$url")
    if [ -n "$url" ] && [[ ! "$url" =~ ^# ]]; then
        wget -qO- "$url" >> "tmp/Direct_tmp.list"
    fi
done
clean_list "tmp/Direct_tmp.list"

echo "=== 5. 生成 Proxy_exclude.list ==="
# 将所有 Custom_RAW + 个人自定义 Proxy/Direct 汇总，作为 Proxy 的排除项
cat tmp/*_RAW.list rules-src/Proxy_custom.list rules-src/Direct_custom.list 2>/dev/null > tmp/Proxy_exclude.list
clean_list "tmp/Proxy_exclude.list"

echo "=== 6. 对比去重，生成 rules/Proxy.list & tmp/delete_proxy.list ==="
# 从 Proxy_tmp 中剔除包含在 Proxy_exclude 中的内容
grep -v -x -F -f tmp/Proxy_exclude.list tmp/Proxy_tmp.list > rules/Proxy.list || true
grep -x -F -f tmp/Proxy_exclude.list tmp/Proxy_tmp.list > tmp/delete_proxy.list || true
clean_list "rules/Proxy.list"
clean_list "tmp/delete_proxy.list"

echo "=== 7. 生成 Direct_exclude.list ==="
# Direct 的排除项 = 之前所有的排除项 (Proxy_exclude) + 刚刚生成的 Proxy.list
cat tmp/Proxy_exclude.list rules/Proxy.list 2>/dev/null > tmp/Direct_exclude.list
clean_list "tmp/Direct_exclude.list"

echo "=== 8. 对比去重，生成 rules/Direct.list & tmp/delete_direct.list ==="
grep -v -x -F -f tmp/Direct_exclude.list tmp/Direct_tmp.list > rules/Direct.list || true
grep -x -F -f tmp/Direct_exclude.list tmp/Direct_tmp.list > tmp/delete_direct.list || true
clean_list "rules/Direct.list"
clean_list "tmp/delete_direct.list"

echo "=== 9. 收尾：转移 Custom 列表到 rules 目录 ==="
cp rules-src/Proxy_custom.list rules/Proxy_custom.list
cp rules-src/Direct_custom.list rules/Direct_custom.list
clean_list "rules/Proxy_custom.list"
clean_list "rules/Direct_custom.list"

echo "规则合并去重全部完成！"
