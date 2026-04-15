import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULE_FILE = os.path.join(BASE_DIR, "rules-src/rules.list")
OUTPUT = os.path.join(BASE_DIR, "build/config.yaml")

custom_rules = []

section = None

with open(RULE_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("["):
            section = line
            continue

        if section == "[Custom_link]":
            name = line.split("|")[0]
            custom_rules.append(name)

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("port: 7890\n")
    f.write("socks-port: 7891\n")
    f.write("allow-lan: true\n")
    f.write("mode: rule\n\n")

    f.write("proxies:\n")
    f.write("""  - {name: US-1, type: ss, server: 1.1.1.1, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: US-2, type: ss, server: 1.1.1.2, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: UK-1, type: ss, server: 2.2.2.1, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: UK-2, type: ss, server: 2.2.2.2, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: HK-1, type: ss, server: 3.3.3.1, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: HK-2, type: ss, server: 3.3.3.2, port: 1000, cipher: aes-128-gcm, password: 123456}

""")

    f.write("proxy-groups:\n")
    f.write("""  - name: 🚀 节点选择
    type: select
    proxies: [US-1, US-2, UK-1, UK-2, HK-1, HK-2]

  - name: 🟢 全球直连
    type: select
    proxies: [DIRECT]

  - name: ♻️ 自动选择
    type: url-test
    proxies: [US-1, US-2, UK-1, UK-2, HK-1, HK-2]
    url: http://www.gstatic.com/generate_204
    interval: 300

""")

    for name in custom_rules:
        f.write(f"""  - name: {name}
    type: select
    proxies: [🚀 节点选择, ♻️ 自动选择, 🟢 全球直连]

""")

    f.write("rules:\n")

    for name in custom_rules:
        f.write(f"  - RULE-SET,{name},{name}\n")

    f.write("  - RULE-SET,Proxy,🚀 节点选择\n")
    f.write("  - RULE-SET,Direct,🟢 全球直连\n")
    f.write("  - MATCH,🚀 节点选择\n")
