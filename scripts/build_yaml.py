import os
import re
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RULES_SRC = os.path.join(ROOT, "rules-src", "rules.list")
RULES_DIR = os.path.join(ROOT, "rules")
OUT_DIR = os.path.join(ROOT, "build")
OUT_FILE = os.path.join(OUT_DIR, "config.yaml")

os.makedirs(OUT_DIR, exist_ok=True)


def parse_custom():
    items = {}
    with open(RULES_SRC, "r", encoding="utf-8") as f:
        content = f.read()

    block = re.search(r"\[Custom_link\](.*?)\[", content, re.S)
    if not block:
        block = re.search(r"\[Custom_link\](.*)", content, re.S)

    lines = block.group(1).strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            name, url = line.split("|", 1)
            items[name.strip()] = url.strip()

    return items


custom = parse_custom()
names = list(custom.keys())

# -------------------------
# base config
# -------------------------
config = {
    "port": 7890,
    "socks-port": 7891,
    "redir-port": 7892,
    "mixed-port": 7893,
    "allow-lan": True,
    "mode": "rule",
    "log-level": "info",
    "ipv6": False,
}

# -------------------------
# proxy-groups
# -------------------------
proxy_groups = [
    {
        "name": "🚀 节点选择",
        "type": "select",
        "proxies": ["US-1", "US-2", "UK-1", "UK-2", "HK-1", "HK-2"]
    },
    {
        "name": "♻️ 自动选择",
        "type": "url-test",
        "url": "http://www.gstatic.com/generate_204",
        "interval": 300,
        "tolerance": 50,
        "proxies": ["US-1", "US-2", "UK-1", "UK-2", "HK-1", "HK-2"]
    },
    {
        "name": "🟢 全球直连",
        "type": "select",
        "proxies": ["DIRECT"]
    }
]

# dynamic groups
for name in names:
    proxy_groups.append({
        "name": name,
        "type": "select",
        "icon": f"https://github.com/Vbaethon/HOMOMIX/blob/main/Icon/Color/{name}.png",
        "proxies": ["♻️ 自动选择", "🚀 节点选择"]
    })

config["proxy-groups"] = proxy_groups

# -------------------------
# rule-providers
# -------------------------
rule_providers = {}

for name, url in custom.items():
    rule_providers[name] = {
        "type": "http",
        "behavior": "classical",
        "url": url,
        "path": f"./ruleset/{name.lower()}.yaml",
        "interval": 86400
    }

# static rules
rule_providers.update({
    "ChinaMedia": {
        "type": "http",
        "behavior": "classical",
        "url": "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaMedia.list",
        "path": "./ruleset/chinaMedia.yaml",
        "interval": 86400
    },
    "ProxyGFWlist": {
        "type": "http",
        "behavior": "classical",
        "url": "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ProxyGFWlist.list",
        "path": "./ruleset/proxygfw.yaml",
        "interval": 86400
    }
})

config["rule-providers"] = rule_providers

# -------------------------
# rules section
# -------------------------
rules = []

for name in names:
    rules.append(f"- RULE-SET,{name},{name}")

rules += [
    "- RULE-SET,ChinaMedia,🟢 全球直连",
    "- RULE-SET,ProxyGFWlist,🚀 节点选择",
    "- GEOIP,CN,🟢 全球直连,no-resolve",
    "- MATCH,🚀 节点选择"
]

config["rules"] = rules

# -------------------------
# write yaml
# -------------------------
with open(OUT_FILE, "w", encoding="utf-8") as f:
    yaml.dump(config, f, allow_unicode=True, sort_keys=False)

print("Generated:", OUT_FILE)
