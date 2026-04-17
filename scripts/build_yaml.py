import os
import yaml

def read_custom_links(filepath):
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
    GITHUB_REPO = "openclash-auto" 
    GITHUB_REPO_RAW = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/rules"

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

    # 2. 开始构建内容字符串
    output = []

    # 直接读取 base.yaml 的原始文本，保留所有空行和注释
    with open('config/base.yaml', 'r', encoding='utf-8') as f:
        output.append(f.read())
    
    output.append("\nproxies:")
    for p in proxies:
        # 使用 Block Style 生成节点，这样就不会有 {} 括号了
        p_str = yaml.dump(p, default_flow_style=False, sort_keys=False, allow_unicode=True).strip()
        # 在每一行前面加上两个空格的缩进，并以 - 开头
        indented_p = "\n".join([f"  {line}" if i > 0 else f"- {line}" for i, line in enumerate(p_str.split('\n'))])
        output.append(f"  {indented_p}")
        output.append("") # 节点后空一行
        output.append("\nproxy-groups:")
    
    # 基础组
    groups_template = [
        {"name": "🚀 节点选择", "type": "select", "proxies": proxy_names},
        {"name": "♻️ 自动选择", "type": "url-test", "proxies": proxy_names, "url": "http://www.gstatic.com/generate_204", "interval": 300, "tolerance": 50},
        {"name": "🟢 全球直连", "type": "select", "proxies": ["DIRECT"]}
    ]
    
    for g in groups_template:
        output.append(yaml.dump([g], default_flow_style=False, sort_keys=False, allow_unicode=True).strip())
        output.append("") # 组之间空一行

    # 动态 Custom 组
    for name in custom_names:
        g = {
            "name": name,
            "type": "select",
            "proxies": ["♻️ 自动选择", "🚀 节点选择"]
        }
        match_name = next((k for k in ICON_MAP if k.lower() == name.lower()), None)
        if match_name:
            g["icon"] = ICON_MAP[match_name]
        
        output.append(yaml.dump([g], default_flow_style=False, sort_keys=False, allow_unicode=True).strip())
        output.append("")

    # Rule Providers
    output.append("\nrule-providers:")
    providers = {}
    for name in custom_names:
        providers[name] = {
            "type": "http", "behavior": "classical", 
            "url": f"{GITHUB_REPO_RAW}/{name}.list", 
            "path": f"./ruleset/{name.lower()}.yaml", "interval": 86400
        }
    providers["Proxy"] = {"type": "http", "behavior": "classical", "url": f"{GITHUB_REPO_RAW}/Proxy.list", "path": "./ruleset/proxy.yaml", "interval": 86400}
    providers["Direct"] = {"type": "http", "behavior": "classical", "url": f"{GITHUB_REPO_RAW}/Direct.list", "path": "./ruleset/direct.yaml", "interval": 86400}

    for k, v in providers.items():
        output.append(yaml.dump({k: v}, default_flow_style=False, sort_keys=False, allow_unicode=True).strip())
        output.append("") # Provider 之间空一行

    # Rules
    output.append("\nrules:")
    for name in custom_names:
        output.append(f"  - RULE-SET,{name},{name}")
    
    output.append("  - RULE-SET,Direct,🟢 全球直连")
    output.append("  - RULE-SET,Proxy,🚀 节点选择")
    output.append("  - GEOIP,CN,🟢 全球直连,no-resolve")
    output.append("  - MATCH,🚀 节点选择")

    # 3. 写入文件
    os.makedirs('build', exist_ok=True)
    with open('build/config.yaml', 'w', encoding='utf-8') as f:
        f.write("\n".join(output))

    print("=== 排版优化后的 YAML 已生成 ===")

if __name__ == '__main__':
    main()
