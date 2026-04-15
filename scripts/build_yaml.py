import os

ROOT = os.path.dirname(os.path.dirname(__file__))

RULES_LIST = os.path.join(ROOT, "rules-src/rules.list")
BUILD_DIR = os.path.join(ROOT, "build")
RULE_DIR = os.path.join(ROOT, "rules")

BASE = os.path.join(ROOT, "config/base.yaml")
NODE = os.path.join(ROOT, "config/node.yaml")

os.makedirs(BUILD_DIR, exist_ok=True)

################################
# 解析 Custom_link
################################
custom = []

with open(RULES_LIST, "r") as f:
    lines = f.readlines()

flag = False
for line in lines:
    line = line.strip()
    if line == "[Custom_link]":
        flag = True
        continue
    if line.startswith("["):
        flag = False
    if flag and "|" in line:
        name = line.split("|")[0].strip()
        custom.append(name)

################################
# 生成 rule-providers
################################
providers = ""

for name in custom:
    providers += f"""
  {name}:
    type: http
    behavior: classical
    url: https://raw.githubusercontent.com/HugoXu12/openclash-rules-auto/main/rules/{name}.list
    path: ./ruleset/{name}.yaml
    interval: 86400
"""

providers += f"""
  Proxy:
    type: http
    behavior: classical
    url: https://raw.githubusercontent.com/HugoXu12/openclash-rules-auto/main/rules/Proxy.list
    path: ./ruleset/proxy.yaml
    interval: 86400

  Direct:
    type: http
    behavior: classical
    url: https://raw.githubusercontent.com/HugoXu12/openclash-rules-auto/main/rules/Direct.list
    path: ./ruleset/direct.yaml
    interval: 86400
"""

################################
# 生成 rules
################################
rules = ""

for name in custom:
    rules += f"  - RULE-SET,{name},{name}\n"

rules += """  - RULE-SET,Direct,🟢 全球直连
  - RULE-SET,Proxy,🚀 节点选择
  - GEOIP,CN,🟢 全球直连,no-resolve
  - MATCH,🚀 节点选择
"""

################################
# 拼接 YAML
################################
with open(BASE) as f:
    base = f.read()

with open(NODE) as f:
    node = f.read()

final = f"""{base}

{node}

rule-providers:
{providers}

rules:
{rules}
"""

with open(os.path.join(BUILD_DIR, "config.yaml"), "w") as f:
    f.write(final)

print("YAML 生成完成")
