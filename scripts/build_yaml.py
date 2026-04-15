import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RULES_SRC = os.path.join(BASE_DIR, "rules-src")
BUILD_DIR = os.path.join(BASE_DIR, "build")

os.makedirs(BUILD_DIR, exist_ok=True)

rules_list_file = os.path.join(RULES_SRC, "rules.list")

custom_rules = []

with open(rules_list_file, "r") as f:
    lines = f.readlines()

in_custom = False
for line in lines:
    line = line.strip()
    if line.startswith("[Custom_link]"):
        in_custom = True
        continue
    if line.startswith("[") and not line.startswith("[Custom_link]"):
        in_custom = False

    if in_custom and "|" in line:
        name = line.split("|")[0]
        custom_rules.append(name)

# =====================
# 构建 YAML
# =====================

yaml = []

yaml.append("port: 7890")
yaml.append("socks-port: 7891")
yaml.append("allow-lan: true")
yaml.append("mode: rule")
yaml.append("log-level: info")
yaml.append("")

# proxies
yaml.append("proxies:")
yaml.append("  - {name: US-1, type: ss, server: 1.1.1.1, port: 1000, cipher: aes-128-gcm, password: 123456}")
yaml.append("  - {name: US-2, type: ss, server: 1.1.1.2, port: 1000, cipher: aes-128-gcm, password: 123456}")
yaml.append("  - {name: UK-1, type: ss, server: 2.2.2.1, port: 1000, cipher: aes-128-gcm, password: 123456}")
yaml.append("  - {name: UK-2, type: ss, server: 2.2.2.2, port: 1000, cipher: aes-128-gcm, password: 123456}")
yaml.append("  - {name: HK-1, type: ss, server: 3.3.3.1, port: 1000, cipher: aes-128-gcm, password: 123456}")
yaml.append("  - {name: HK-2, type: ss, server: 3.3.3.2, port: 1000, cipher: aes-128-gcm, password: 123456}")
yaml.append("")

# proxy-groups
yaml.append("proxy-groups:")
yaml.append("  - name: 🚀 节点选择")
yaml.append("    type: select")
yaml.append("    proxies: [US-1, US-2, UK-1, UK-2, HK-1, HK-2]")
yaml.append("")

# 每个 Custom 生成策略组
for rule in custom_rules:
    yaml.append(f"  - name: {rule}")
    yaml.append("    type: select")
    yaml.append("    proxies: [🚀 节点选择, DIRECT]")
    yaml.append("")

# rules
yaml.append("rules:")

# Custom 高优先级
for rule in custom_rules:
    yaml.append(f"  - RULE-SET,{rule},{rule}")

# 你的优先级
yaml.append("  - RULE-SET,Direct_custom,DIRECT")
yaml.append("  - RULE-SET,Proxy_custom,🚀 节点选择")
yaml.append("  - RULE-SET,Direct,DIRECT")
yaml.append("  - RULE-SET,Proxy,🚀 节点选择")
yaml.append("  - MATCH,🚀 节点选择")

# 写入文件
with open(os.path.join(BUILD_DIR, "config.yaml"), "w") as f:
    f.write("\n".join(yaml))

print("✅ YAML 生成完成")
