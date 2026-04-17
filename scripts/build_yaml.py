import os
import yaml

# 保持 YAML 写入时不改变锚点和格式
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

def read_custom_links(filepath):
    custom_names = []
    with open(filepath, 'r', encoding='utf-8') as f:
        is_custom = False
        for line in f:
            line = line.strip()
            if line.startswith('[Custom_link]'):
                is_custom = True
                continue
            if line.startswith('['):
                is_custom = False
                continue
            if is_custom and line and '|' in line:
                name = line.split('|')[0].strip()
                custom_names.append(name)
    return custom_names

def main():
    # 1. 提取动态规则集名称
    custom_names = read_custom_links('rules-src/rules.list')
    
    # 2. 读取基础配置与节点配置
    with open('config/base.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
        
    with open('config/node.yaml', 'r', encoding='utf-8') as f:
        node_data = yaml.safe_load(f) or {}
        proxies = node_data.get('proxies', [])
        proxy_names = [p['name'] for p in proxies]

    config['proxies'] = proxies

    # 3. 构建 proxy-groups
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

    # 动态插入 Custom 分组 (比如 Google, Youtube, AI)
    for name in custom_names:
        group = {
            'name': name,
            'type': 'select',
            'proxies': ['♻️ 自动选择', '🚀 节点选择']
        }
        # 如果需要图标，可以在此处做名称判断并分配 URL
        proxy_groups.append(group)

    config['proxy-groups'] = proxy_groups

    # 4. 构建 rule-providers
    # 请修改为你的真实 GITHUB 用户名和仓库名！
    GITHUB_REPO_RAW = "https://raw.githubusercontent.com/YOUR_GITHUB_NAME/YOUR_REPO_NAME/main/rules"
    
    rule_providers = {}
    
    # 动态添加 Custom providers
    for name in custom_names:
        rule_providers[name] = {
            'type': 'http',
            'behavior': 'classical',
            'url': f"{GITHUB_REPO_RAW}/{name}.list",
            'path': f"./ruleset/{name.lower()}.yaml",
            'interval': 86400
        }

    # 添加基础 providers
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

    # 5. 构建 rules
    rules = []
    # 优先级: Custom > Direct > Proxy > GEOIP/MATCH
    for name in custom_names:
        rules.append(f"RULE-SET,{name},{name}")
        
    rules.extend([
        "RULE-SET,Direct,🟢 全球直连",
        "RULE-SET,Proxy,🚀 节点选择",
        "GEOIP,CN,🟢 全球直连,no-resolve",
        "MATCH,🚀 节点选择"
    ])
    
    config['rules'] = rules

    # 6. 输出 YAML
    os.makedirs('build', exist_ok=True)
    with open('build/config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True, Dumper=NoAliasDumper)
        
    print("=== YAML 配置构建完成 -> build/config.yaml ===")

if __name__ == '__main__':
    main()
