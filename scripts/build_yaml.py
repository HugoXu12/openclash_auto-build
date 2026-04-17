import os
import yaml

# 保持 YAML 写入时不产生锚点（&id001），使配置易读
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

def read_custom_links(filepath):
    """从 rules.list 中提取 [Custom_link] 节的规则名称"""
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
    # --- 1. 配置区域 ---
    # 【重要】请修改为你真实的 GitHub 仓库 Raw 地址
    GITHUB_USER = "HugoXu12"
    GITHUB_REPO = "openclash-auto-build" # 替换为你的仓库名
    GITHUB_REPO_RAW = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/rules"

    # 图标映射表
    ICON_MAP = {
        "Google": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/blob/main/Icon/Color/Google.png",
        "YouTube": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/blob/main/Icon/Color/YouTube.png",
        "AI": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/blob/main/Icon/Color/AI.png",
        "Netflix": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/blob/main/Icon/Color/Netflix_b.png",
        "Proxy": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/blob/main/Icon/Color/Proxy.png",
        "Direct": "https://raw.githubusercontent.com/Vbaethon/HOMOMIX/blob/main/Icon/Color/Direct.png"
    }

    # --- 2. 加载基础数据 ---
    custom_names = read_custom_links('rules-src/rules.list')
    
    with open('config/base.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
        
    with open('config/node.yaml', 'r', encoding='utf-8') as f:
        node_data = yaml.safe_load(f) or {}
        proxies = node_data.get('proxies', [])
        proxy_names = [p['name'] for p in proxies]

    # 注入节点信息
    config['proxies'] = proxies

    # --- 3. 构建策略组 (proxy-groups) ---
    proxy_groups = [
        {
            'name': '🚀 节点选择',
            'type': 'select',
            'proxies': proxy_names
        },
        {
            'name': '♻️ 自动选择',
            'type': 'url-test',
            'url': 'http://www.gstatic.com/generate_204',
            'interval': 300,
            'tolerance': 50,
            'proxies': proxy_names
        },
        {
            'name': '🟢 全球直连',
            'type': 'select',
            'proxies': ['DIRECT']
        }
    ]

    # 动态添加 Custom 规则的分组（带图标匹配）
    for name in custom_names:
        group = {
            'name': name,
            'type': 'select',
            'proxies': ['♻️ 自动选择', '🚀 节点选择']
        }
        # 匹配图标
        match_name = next((k for k in ICON_MAP if k.lower() == name.lower()), None)
        if match_name:
            group['icon'] = ICON_MAP[match_name]
        
        proxy_groups.append(group)

    config['proxy-groups'] = proxy_groups

    # --- 4. 构建 Rule Providers ---
    rule_providers = {}
    
    # Custom 规则的 Provider
    for name in custom_names:
        rule_providers[name] = {
            'type': 'http',
            'behavior': 'classical',
            'url': f"{GITHUB_REPO_RAW}/{name}.list",
            'path': f"./ruleset/{name.lower()}.yaml",
            'interval': 86400
        }

    # 基础 Proxy 和 Direct 的 Provider
    rule_providers['Proxy'] = {
        'type': 'http',
        'behavior': 'classical',
        'url': f"{GITHUB_REPO_RAW}/Proxy.list",
        'path': "./ruleset/proxy.yaml",
        'interval': 86400
    }
    rule_providers['Direct'] = {
        'type': 'http',
        'behavior': 'classical',
        'url': f"{GITHUB_REPO_RAW}/Direct.list",
        'path': "./ruleset/direct.yaml",
        'interval': 86400
    }
    
    config['rule-providers'] = rule_providers

    # --- 5. 构建 最终规则 (rules) ---
    # 优先级逻辑：Custom > Direct > Proxy > GEOIP/MATCH
    rules_list = []
    for name in custom_names:
        rules_list.append(f"RULE-SET,{name},{name}")
        
    rules_list.extend([
        "RULE-SET,Direct,🟢 全球直连",
        "RULE-SET,Proxy,🚀 节点选择",
        "GEOIP,CN,🟢 全球直连,no-resolve",
        "MATCH,🚀 节点选择"
    ])
    
    config['rules'] = rules_list

    # --- 6. 写入文件 ---
    os.makedirs('build', exist_ok=True)
    with open('build/config.yaml', 'w', encoding='utf-8') as f:
        # 使用 NoAliasDumper 保证 YAML 格式纯净
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True, Dumper=NoAliasDumper)
        
    print(f"成功构建配置：build/config.yaml (包含 {len(custom_names)} 个自定义规则集)")

if __name__ == '__main__':
    main()
