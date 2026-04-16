import os
import re

def main():
    # 获取 GitHub 仓库信息以生成 RAW 链接
    repo = os.environ.get("GITHUB_REPOSITORY", "HugoXu12/openclash-auto")
    branch = "main"
    base_raw_url = f"https://raw.githubusercontent.com/{repo}/refs/heads/{branch}/rules"

    # 读取 Custom_link 列表
    custom_links = []
    if os.path.exists("rules-src/rules.list"):
        with open("rules-src/rules.list", "r", encoding="utf-8") as f:
            in_custom = False
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line == "[Custom_link]":
                    in_custom = True
                    continue
                elif line.startswith("["):
                    in_custom = False
                
                if in_custom and "|" in line:
                    name, _ = line.split("|", 1)
                    custom_links.append(name.strip())

    # --- 开始拼接 YAML 内容 ---
    
    yaml_content = """port: 7890
socks-port: 7891
redir-port: 7892
mixed-port: 7893
allow-lan: true
mode: rule
log-level: info
ipv6: false

################################
# DNS（防污染核心）
################################
dns:
  enable: true
  cache-algorithm: arc
  listen: 0.0.0.0:1053
  ipv6: false
  respect-rules: true
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  fake-ip-filter-mode: blacklist
  fake-ip-filter:
    - "rule-set:fakeipfilter_domain"
  default-nameserver:
    - https://223.5.5.5/dns-query
  proxy-server-nameserver:
    - https://dns.alidns.com/dns-query
    - https://doh.pub/dns-query
  nameserver:
    - https://dns.alidns.com/dns-query
    - https://doh.pub/dns-query

proxies:
  - {name: US-1, type: ss, server: 1.1.1.1, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: US-2, type: ss, server: 1.1.1.2, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: UK-1, type: ss, server: 2.2.2.1, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: UK-2, type: ss, server: 2.2.2.2, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: HK-1, type: ss, server: 3.3.3.1, port: 1000, cipher: aes-128-gcm, password: 123456}
  - {name: HK-2, type: ss, server: 3.3.3.2, port: 1000, cipher: aes-128-gcm, password: 123456}

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

  - name: ♻️ 自动选择
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    tolerance: 50
    proxies:
      - US-1 
      - US-2 
      - UK-1 
      - UK-2 
      - HK-1 
      - HK-2

  - name: 🟢 全球直连
    type: select
    proxies:
      - DIRECT
"""

    # 动态插入 Custom_link 对应的代理组
    for name in custom_links:
        yaml_content += f"""
  - name: {name}
    type: select
    proxies:
      - ♻️ 自动选择
      - 🚀 节点选择
"""

    yaml_content += "\nrule-providers:\n"

    # 动态插入 Custom_link 对应的 rule-providers
    for name in custom_links:
        yaml_content += f"""
  {name}:
    type: http
    behavior: classical
    url: {base_raw_url}/{name}.list
    path: ./ruleset/{name}.yaml
    interval: 86400
"""
        
    # 添加固定的 rule-providers (包含你的 Custom.list)
    yaml_content += f"""
  Direct_custom:
    type: http
    behavior: classical
    url: {base_raw_url}/Direct_custom.list
    path: ./ruleset/Direct_custom.yaml
    interval: 86400

  Proxy_custom:
    type: http
    behavior: classical
    url: {base_raw_url}/Proxy_custom.list
    path: ./ruleset/Proxy_custom.yaml
    interval: 86400

  Proxy:
    type: http
    behavior: classical
    url: {base_raw_url}/Proxy.list
    path: ./ruleset/Proxy.yaml
    interval: 86400

  Direct:
    type: http
    behavior: classical
    url: {base_raw_url}/Direct.list
    path: ./ruleset/Direct.yaml
    interval: 86400

rules:
"""

    # 按照优先级组装 rules 分流
    # 优先级 1: Custom_link (Google, Youtube, AI等) -> 指向各自名称的代理组
    for name in custom_links:
        yaml_content += f"  - RULE-SET,{name},{name}\n"
        
    # 优先级 2-5: Direct_custom -> Proxy_custom -> Direct -> Proxy
    yaml_content += """  - RULE-SET,Direct_custom,🟢 全球直连
  - RULE-SET,Proxy_custom,🚀 节点选择
  - RULE-SET,Direct,🟢 全球直连
  - RULE-SET,Proxy,🚀 节点选择
  - GEOIP,CN,🟢 全球直连,no-resolve
  - MATCH,🚀 节点选择
"""

    # 输出到 build/config.yaml
    os.makedirs("build", exist_ok=True)
    with open("build/config.yaml", "w", encoding="utf-8") as f:
        f.write(yaml_content)

    print(f"成功生成 config.yaml，包含 {len(custom_links)} 个自定义动态分流规则。")

if __name__ == "__main__":
    main()
