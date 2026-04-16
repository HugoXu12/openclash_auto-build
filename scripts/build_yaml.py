import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RULES_SRC = os.path.join(BASE_DIR, "rules-src")
BUILD_DIR = os.path.join(BASE_DIR, "build")

os.makedirs(BUILD_DIR, exist_ok=True)

rules_file = os.path.join(RULES_SRC, "rules.list")

custom_rules = []

if os.path.exists(rules_file):
    with open(rules_file, "r") as f:
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
            name = line.split("|")[0].strip()
            if name:
                custom_rules.append(name)

# =====================
# YAML 构建
# =====================

yaml = []

yaml += [
    "port: 7890",
    "socks-port: 7891",
    "allow-lan: true",
    "mode: rule",
    "log-level: info",
    ""
]

yaml.append("proxies:")
yaml += [
    "  - {name: US-1, type: ss, server: 1.1.1.1, port: 1000, cipher: aes-128-gcm, password: 123456}",
    "  - {name: US-2, type: ss, server: 1.1.1.2, port: 1000, cipher: aes-128-gcm, password: 123456}",
    "  - {name: UK-1, type: ss, server: 2.2.2.1, port: 1000, cipher: aes-128-gcm, password: 123456}",
    "  - {name: UK-2, type: ss, server: 2.2.2.2, port: 1000, cipher: aes-128-gcm, password: 123456}",
    "  - {name: HK-1, type: ss, server: 3.3.3.1, port: 1000, cipher: aes-128-gcm, password: 123456}",
    "  - {name: HK-2, type: ss, server: 3.3.3.2, port: 1000, cipher: aes-128-gcm, password: 123456}",
    ""
]

yaml.append("proxy-groups:")
yaml += [
    "  - name: 🚀 节点选择",
    "    type: select",
    "    proxies: [US-1, US-2, UK-1, UK-2, HK-1, HK-2]",
    ""
]

for rule in custom_rules:
    yaml += [
        f"  - name: {rule}",
        "    type: select",
        "    proxies: [🚀 节点选择, DIRECT]",
        ""
    ]

yaml.append("rules:")

for rule in custom_rules:
    yaml.append(f"  - RULE-SET,{rule},{rule}")

yaml += [
    "  - RULE-SET,Direct_custom,DIRECT",
    "  - RULE-SET,Proxy_custom,🚀 节点选择",
    "  - RULE-SET,Direct,DIRECT",
    "  - RULE-SET,Proxy,🚀 节点选择",
    "  - MATCH,🚀 节点选择"
]

with open(os.path.join(BUILD_DIR, "config.yaml"), "w") as f:
    f.write("\n".join(yaml))

print("✅ YAML 生成完成")
