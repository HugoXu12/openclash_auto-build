import os
import yaml

def read_custom_links(filepath):
    """提取 [Custom_link] 节的规则名称"""
    custom_names = []
    if not os.path.exists(filepath):
        return custom_names
    with open(filepath, 'r', encoding='utf-8') as f:
        is_custom = False
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            if line.startswith('[Custom_link]'):
                is_custom = True
                continue
            if line.startswith('['):
                is_custom = False
                continue
            if is_custom and '|' in line:
                name = line.split('|')[0].strip()
                custom_names.append(name)
    return custom_names

def read_and_format_rules(filepath, policy):
    """读取本地 .list 文件，并将其转换为带有具体策略组的直写规则"""
    rule_lines = []
    if not os.path.exists(filepath):
        return rule_lines
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 过滤空行和注释行
            if not line or line.startswith('#'): 
                continue
            
            parts = line.split(',')
            # 处理特殊情况：如果原始规则带有 no-resolve，策略组必须插在它前面
            # 例如 IP-CIDR,1.1.1.1/32,no-resolve -> IP-CIDR,1.1.1.1/32,Policy,no-resolve
            if len(parts) >= 2 and parts[-1].strip().lower() == 'no-resolve':
                rule_lines.append(f"  - {','.join(parts[:-1])},{policy},no-resolve")
            else:
                rule_lines.append(f"  - {line},{policy}")
                
    return rule_lines

def main():
    # --- 配置信息 ---
    ICON_MAP = {
        "Google": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/main/Icon/Color/Google.png",
        "YouTube": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/main/Icon/Color/YouTube.png",
        "AI": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/main/Icon/Color/AI.png",
        "Netflix": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/main/Icon/Color/Netflix_b.png",
        "Proxy": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/main/Icon/Color/Proxy.png",
        "Direct": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/main/Icon/Color/Direct.png"
    }

    # 1. 加载数据
    custom_names = read_custom_links('rules-src/rules.list')
    
    with open('config/node.yaml', 'r', encoding='utf-8') as f:
        node_data = yaml.safe_load(f) or {}
        proxies = node_data.get('proxies', [])
        proxy_names = [p['name'] for p in proxies]

    output = []

    # 2. 注入 base.yaml
    with open('config/base.yaml', 'r', encoding='utf-8') as f:
        output.append(f.read())
    
    # 3. 注入 proxies
    output.append("\nproxies:")
    for p in proxies:
        p_block = yaml.dump(p, default_flow_style=False, sort_keys=False, allow_unicode=True).strip()
        lines = p_block.split('\n')
        output.append(f"  - {lines[0]}")
        for line in lines[1:]:
            output.append(f"    {line}")
        output.append("")

    # 4. 注入 proxy-groups
    output.append("\nproxy-groups:")
    base_groups = [
        {"name": "🚀 节点选择", "type": "select", "proxies": proxy_names},
        {"name": "♻️ 自动选择", "type": "url-test", "proxies": proxy_names, "url": "http://www.gstatic.com/generate_204", "interval": 300, "tolerance": 50},
        {"name": "🟢 全球直连", "type": "select", "proxies": ["DIRECT"]}
    ]
    
    all_groups = base_groups
    for name in custom_names:
        g = {"name": name, "type": "select", "proxies": ["♻️ 自动选择", "🚀 节点选择"]}
        match_name = next((k for k in ICON_MAP if k.lower() == name.lower()), None)
        if match_name: g["icon"] = ICON_MAP[match_name]
        all_groups.append(g)

    for g in all_groups:
        g_block = yaml.dump(g, default_flow_style=False, sort_keys=False, allow_unicode=True).strip()
        lines = g_block.split('\n')
        output.append(f"  - {lines[0]}")
        for line in lines[1:]:
            output.append(f"    {line}")
        output.append("")

    # === 注意：rule-providers 块已完全删除 ===

    # 5. 注入 rules (展开所有本地 .list 文件)
    output.append("\nrules:")
    
    # (1) 高优先级：Custom 规则 (从 rules 文件夹读取)
    for name in custom_names:
        filepath = f"rules/{name}.list"
        output.extend(read_and_format_rules(filepath, name))
    
    # (2) 中高优先级：个人自定义直连 (从 rules-src 文件夹读取)
    output.extend(read_and_format_rules("rules-src/Direct_custom.list", "🟢 全球直连"))
    
    # (3) 中优先级：个人自定义代理 (从 rules-src 文件夹读取)
    output.extend(read_and_format_rules("rules-src/Proxy_custom.list", "🚀 节点选择"))
    
    # (4) 基础优先级：汇总规则 (从 rules 文件夹读取)
    output.extend(read_and_format_rules("rules/Direct.list", "🟢 全球直连"))
    output.extend(read_and_format_rules("rules/Proxy.list", "🚀 节点选择"))
    
    # (5) 兜底规则
    output.append("  - GEOIP,CN,🟢 全球直连,no-resolve")
    output.append("  - MATCH,🚀 节点选择")

    # 6. 写入文件
    os.makedirs('build', exist_ok=True)
    with open('build/config.yaml', 'w', encoding='utf-8') as f:
        f.write("\n".join(output))

    print("=== 全展开版 Inline Rules YAML 已生成 ===")

if __name__ == '__main__':
    main()

