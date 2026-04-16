import os

RULE_FILE = "rules-src/rules.list"
OUT_FILE = "build/config.yaml"

def parse_custom():
    custom = []
    section = None
    with open(RULE_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("["):
                section = line
                continue

            if section == "[Custom_link]":
                name = line.split("|")[0]
                custom.append(name)

    return custom


def load_rules(path, policy):
    rules = []
    if not os.path.exists(path):
        return rules

    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rules.append(f"DOMAIN-SUFFIX,{line},{policy}")
    return rules


def main():
    custom = parse_custom()

    yaml = []

    # ========= proxies =========
    yaml.append("proxies:")
    yaml += [
        "  - {name: US-1, type: ss, server: 1.1.1.1, port: 1000, cipher: aes-128-gcm, password: 123456}",
        "  - {name: US-2, type: ss, server: 1.1.1.2, port: 1000, cipher: aes-128-gcm, password: 123456}",
        "  - {name: UK-1, type: ss, server: 2.2.2.1, port: 1000, cipher: aes-128-gcm, password: 123456}",
        "  - {name: UK-2, type: ss, server: 2.2.2.2, port: 1000, cipher: aes-128-gcm, password: 123456}",
        "  - {name: HK-1, type: ss, server: 3.3.3.1, port: 1000, cipher: aes-128-gcm, password: 123456}",
        "  - {name: HK-2, type: ss, server: 3.3.3.2, port: 1000, cipher: aes-128-gcm, password: 123456}",
    ]

    # ========= rules =========
    yaml.append("\nrules:")

    # Custom优先
    for name in custom:
        rules = load_rules(f"rules/{name}.list", name)
        yaml += rules

    # 自定义
    yaml += load_rules("rules-src-provisional/Direct_custom_RAW.list", "DIRECT")
    yaml += load_rules("rules-src-provisional/Proxy_custom_RAW.list", "Proxy")

    # 通用
    yaml += load_rules("rules/Direct.list", "DIRECT")
    yaml += load_rules("rules/Proxy.list", "Proxy")

    yaml.append("MATCH,Proxy")

    with open(OUT_FILE, "w") as f:
        f.write("\n".join(yaml))

    print("YAML generated")


if __name__ == "__main__":
    main()
