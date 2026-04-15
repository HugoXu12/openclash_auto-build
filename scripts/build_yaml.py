import os

RULES_LIST = "rules-src/rules.list"
OUTPUT = "build/config.yaml"

BASE = open("config/base.yaml").read()
NODE = open("config/node.yaml").read()

custom_rules = []

section = None

with open(RULES_LIST) as f:
    for line in f:
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("["):
            section = line.strip("[]")
            continue

        if section == "Custom_link":
            name = line.split("|")[0]
            custom_rules.append(name)

###################################
# 生成 proxy-groups
###################################

def gen_groups():
    groups = []

    base_group = f"""
  - name: 🚀 节点选择
    type: select
    proxies:
"""
    # 提取节点名称
    nodes = []
    for line in NODE.splitlines():
        if "name:" in line:
            n = line.split("name:")[1].split(",")[0].strip()
            nodes.append(n)

    for n in nodes:
        base_group += f"      - {n}\n"

    auto_group = base_group.replace("select", "url-test")
    auto_group = auto_group.replace("🚀 节点选择", "♻️ 自动选择")
    auto_group += "    url: http://www.gstatic.com/generate_204\n    interval: 300\n"

    groups.append(base_group)
    groups.append(auto_group)

    groups.append("""
  - name: 🟢 全球直连
    type: select
    proxies:
      - DIRECT
""")

    for r in custom_rules:
        groups.append(f"""
  - name: {r}
    type: select
    proxies:
      - ♻️ 自动选择
      - 🚀 节点选择
""")

    return "\n".join(groups)

###################################
# rule-providers
###################################

def gen_providers():
    txt = ""

    for r in custom_rules:
        txt += f"""
  {r}:
    type: http
    behavior: classical
    url: https://raw.githubusercontent.com/YOUR_REPO/main/rules/{r}.list
    path: ./ruleset/{r}.yaml
    interval: 86400
"""

    txt += """
  Proxy:
    type: http
    behavior: classical
    url: https://raw.githubusercontent.com/YOUR_REPO/main/rules/Proxy.list
    path: ./ruleset/proxy.yaml
    interval: 86400

  Direct:
    type: http
    behavior: classical
    url: https://raw.githubusercontent.com/YOUR_REPO/main/rules/Direct.list
    path: ./ruleset/direct.yaml
    interval: 86400
"""

    return txt

###################################
# rules
###################################

def gen_rules():
    rules = []

    for r in custom_rules:
        rules.append(f"  - RULE-SET,{r},{r}")

    rules += [
        "  - RULE-SET,Direct,🟢 全球直连",
        "  - RULE-SET,Proxy,🚀 节点选择",
        "  - GEOIP,CN,🟢 全球直连,no-resolve",
        "  - MATCH,🚀 节点选择"
    ]

    return "\n".join(rules)

###################################
# 输出
###################################

os.makedirs("build", exist_ok=True)

with open(OUTPUT, "w") as f:
    f.write(BASE)
    f.write("\n")
    f.write(NODE)
    f.write("\nproxy-groups:\n")
    f.write(gen_groups())
    f.write("\nrule-providers:\n")
    f.write(gen_providers())
    f.write("\nrules:\n")
    f.write(gen_rules())

print("config.yaml 生成完成")
