import os

RULE_FILE = "rules-src/rules.list"
OUTPUT = "build/config.yaml"

def parse_custom():
    custom = []
    with open(RULE_FILE, "r") as f:
        lines = f.readlines()

    in_section = False
    for line in lines:
        line = line.strip()

        if line == "[Custom_link]":
            in_section = True
            continue
        if line.startswith("[") and in_section:
            break

        if in_section and line and "|" in line:
            name = line.split("|")[0]
            custom.append(name)

    return custom


def main():
    custom = parse_custom()

    os.makedirs("build", exist_ok=True)

    with open(OUTPUT, "w") as f:

        # proxies
        f.write("proxies:\n")
        f.write("""  - {name: US-1, type: ss, server: 1.1.1.1, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: US-2, type: ss, server: 1.1.1.2, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: UK-1, type: ss, server: 2.2.2.1, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: UK-2, type: ss, server: 2.2.2.2, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: HK-1, type: ss, server: 3.3.3.1, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: HK-2, type: ss, server: 3.3.3.2, port: 1000, cipher: aes-128-gcm, password: 123456}

""")

        f.write("port: 7890\n\n")

        # rules
        f.write("rules:\n")

        # Custom 优先级最高
        for name in custom:
            f.write(f"  - RULE-SET,{name},{name}\n")

        f.write("  - RULE-SET,Direct_custom,DIRECT\n")
        f.write("  - RULE-SET,Proxy_custom,Proxy\n")
        f.write("  - RULE-SET,Direct,DIRECT\n")
        f.write("  - RULE-SET,Proxy,Proxy\n")
        f.write("  - MATCH,Proxy\n")


if __name__ == "__main__":
    main()
