import os

RULE_FILE = "rules-src/rules.list"
OUTPUT = "build/config.yaml"

def parse_custom():
    custom = []
    in_block = False

    with open(RULE_FILE, "r") as f:
        for line in f:
            line = line.strip()

            if line == "[Custom_link]":
                in_block = True
                continue
            elif line.startswith("[") and in_block:
                break

            if in_block and line and "|" in line:
                name = line.split("|")[0]
                custom.append(name)

    return custom

custom_rules = parse_custom()

rules = []

# 高优先级 Custom
for name in custom_rules:
    rules.append(f"RULE-SET,{name},{name}")

# 自定义
rules.append("RULE-SET,Direct_custom,DIRECT")
rules.append("RULE-SET,Proxy_custom,🚀 节点选择")

# 通用
rules.append("RULE-SET,Direct,DIRECT")
rules.append("RULE-SET,Proxy,🚀 节点选择")

rules.append("MATCH,DIRECT")

yaml = f"""
port: 7890
socks-port: 7891
allow-lan: true
mode: rule

proxies:
  - {{name: US-1, type: ss, server: 1.1.1.1, port: 1000, cipher: aes-128-gcm, password: 123456}}
  - {{name: US-2, type: ss, server: 1.1.1.2, port: 1000, cipher: aes-128-gcm, password: 123456}}
  - {{name: UK-1, type: ss, server: 2.2.2.1, port: 1000, cipher: aes-128-gcm, password: 123456}}
  - {{name: UK-2, type: ss, server: 2.2.2.2, port: 1000, cipher: aes-128-gcm, password: 123456}}
  - {{name: HK-1, type: ss, server: 3.3.3.1, port: 1000, cipher: aes-128-gcm, password: 123456}}
  - {{name: HK-2, type: ss, server: 3.3.3.2, port: 1000, cipher: aes-128-gcm, password: 123456}}

proxy-groups:
  - name: 🚀 节点选择
    type: select
    proxies:
      - US-1
      - US-2
      - UK-1
      - UK-2
      - HK-1
      - HK-2

rule-providers:
"""

# 动态 rule-providers
for name in custom_rules:
    yaml += f"""
  {name}:
    type: file
    behavior: classical
    path: ./rules/{name}.list
"""

yaml += """
  Proxy:
    type: file
    behavior: classical
    path: ./rules/Proxy.list

  Direct:
    type: file
    behavior: classical
    path: ./rules/Direct.list

rules:
"""

for r in rules:
    yaml += f"  - {r}\n"

os.makedirs("build", exist_ok=True)

with open(OUTPUT, "w") as f:
    f.write(yaml)

print("YAML 生成完成")
