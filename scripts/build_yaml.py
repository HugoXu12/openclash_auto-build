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

def main():
    # --- 配置信息 ---
    GITHUB_USER = "HugoXu12"
    GITHUB_REPO = "openclash-auto-build" 
    GITHUB_REPO_RAW = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/refs/heads/main/rules"

    ICON_MAP = {
        "Google": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/blob/main/Icon/Color/Google.png",
        "YouTube": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/blob/main/Icon/Color/YouTube.png",
        "AI": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/blob/main/Icon/Color/AI.png",
        "Netflix": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/blob/main/Icon/Color/Netflix_b.png",
        "Proxy": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/blob/main/Icon/Color/Proxy.png",
        "Direct": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/blob/main/Icon/Color/Direct.png"
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

    # 5. 注入 rule-providers
    output.append("\nrule-providers:")
    providers = {}
    
    # Custom 规则 (来自 URL)
    for name in custom_names:
        providers[name] = {
            "type": "http", "behavior": "classical", 
            "url": f"{GITHUB_REPO_RAW}/{name}.list", 
            "path": f"./ruleset/{name.lower()}.yaml", "interval": 86400
        }
    
    # 新增：Proxy_custom 和 Direct_custom (来自本地文件)
    # 注意：为了让 OpenClash 识别，建议在 merge.sh 中也将这两个文件拷贝到 rules 文件夹
    providers["Direct_custom"] = {
        "type": "http", "behavior": "classical",
        "url": f"{GITHUB_REPO_RAW}/Direct_custom.list",
        "path": "./ruleset/direct_custom.yaml", "interval": 86400
    }
    providers["Proxy_custom"] = {
        "type": "http", "behavior": "classical",
        "url": f"{GITHUB_REPO_RAW}/Proxy_custom.list",
        "path": "./ruleset/proxy_custom.yaml", "interval": 86400
    }
    
    # 基础汇总规则
    providers["Direct"] = {"type": "http", "behavior": "classical", "url": f"{GITHUB_REPO_RAW}/Direct.list", "path": "./ruleset/direct.yaml", "interval": 86400}
    providers["Proxy"] = {"type": "http", "behavior": "classical", "url": f"{GITHUB_REPO_RAW}/Proxy.list", "path": "./ruleset/proxy.yaml", "interval": 86400}

    for k, v in providers.items():
        p_str = yaml.dump({k: v}, default_flow_style=False, sort_keys=False, allow_unicode=True).strip()
        output.append(f"  {p_str}")
        output.append("")

    # 6. 注入 rules (严格按照优先级排版)
    output.append("\nrules:")
    
    # (1) 高优先级：Custom 规则 (Google, Youtube, etc.)
    for name in custom_names:
        output.append(f"  - RULE-SET,{name},{name}")
    
    # (2) 中高优先级：个人自定义直连
    output.append("  - RULE-SET,Direct_custom,🟢 全球直连")
    
    # (3) 中优先级：个人自定义代理
    output.append("  - RULE-SET,Proxy_custom,🚀 节点选择")
    
    # (4) 基础优先级：汇总规则
    output.append("  - RULE-SET,Direct,🟢 全球直连")
    output.append("  - RULE-SET,Proxy,🚀 节点选择")
    
    # (5) 兜底规则
    output.append("  - GEOIP,CN,🟢 全球直连,no-resolve")
    output.append("  - MATCH,🚀 节点选择")

    # 7. 写入
    os.makedirs('build', exist_ok=True)
    with open('build/config.yaml', 'w', encoding='utf-8') as f:
        f.write("\n".join(output))

    print("=== 优先级优化版 YAML 已生成 ===")

if __name__ == '__main__':
    main()
