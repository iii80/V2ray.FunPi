# encoding: utf-8
"""
File:       v2ray_config_generator
Author:     twotrees.us@gmail.com
Date:       2020年7月30日  31周星期四 15:52
Desc:
"""
import json
from .proxy_mode import ProxyMode
from .node_item import NodeItem
from .dns_config import DnsConfig
from .advance_config import AdvanceConfig

def gen_config(node: NodeItem, all_nodes: list, mode: int, advance_config: AdvanceConfig) -> str:
    config = gen_basic()
    detail = None
    if mode == ProxyMode.Direct.value:
        detail = gen_direct(node)
    elif mode == ProxyMode.ProxyAuto.value:
        detail = gen_proxy_auto(node, advance_config)
        append_all_nodes_rules(detail, all_nodes)
    elif mode == ProxyMode.ProxyGlobal.value:
        detail = gen_proxy_global(node, advance_config)
        append_all_nodes_rules(detail, all_nodes)

    config.update(detail)
    return json.dumps(config, indent=4)

def gen_basic() -> dict:
    basic_raw_config = '''
{
    "log": {
        "access": "/var/log/v2ray/access.log",
        "error": "/var/log/v2ray/error.log",
        "loglevel": "warning"
    },
    "inbounds": [
        {
            "port": 12345,
            "protocol": "dokodemo-door",
            "settings": {
                "followRedirect": true,
                "network": "tcp,udp"
            },
            "sniffing": {
                "destOverride": [
                    "http",
                    "tls"
                ],
                "enabled": true
            },
            "streamSettings": {
                "sockopt": {
                    "tproxy": "tproxy"
                }
            },
            "tag": "transparent"
        },
        {
            "port": 1080,
            "protocol": "socks",
            "settings": {
                "auth": "noauth"
            },
            "sniffing": {
                "destOverride": [
                    "http",
                    "tls"
                ],
                "enabled": true
            }
        }
    ]
}
'''
    config = json.loads(basic_raw_config)
    return config

def append_all_nodes_rules(config: dict, all_nodes:list):
    raw_config ='''
{
    "domain": [],
    "outboundTag": "direct",
    "type": "field"
}'''
    nodes_rule = json.loads(raw_config)
    domains:list = nodes_rule['domain']

    hosts = set()
    for node in all_nodes:
        hosts.add(node.add)

    for host in hosts:
        domains.append(host)

    rules: list = config['routing']['rules']
    rules.append(nodes_rule)

def gen_direct(node: NodeItem) -> dict:
    direct_raw_config = '''
{
	"outbounds": [
		{
			"protocol": "freedom",
			"settings": {},
			"streamSettings": {
				"sockopt": {
					"mark": 255
				}
			}
		}
	]
}'''
    config = json.loads(direct_raw_config)
    return config

def gen_proxy_outbands(node: NodeItem) -> dict:
    proxy_global_raw_config = '''
{
    "outbounds": [
        {
            "mux": {
                "enabled": true
            },
            "protocol": "vmess",
            "settings": {
                "vnext": [
                    {
                        "address": "<str:add>",
                        "port": "<int:port>",
                        "users": [
                            {
                                "alterId": "<int:aid>",
                                "id": "<str:id>",
                                "level": 0,
                                "security": "aes-128-gcm"
                            }
                        ]
                    }
                ]
            },
            "streamSettings": {
                "network": "<str:net>",
                "security": "<str:tls>",
                "sockopt": {
                    "mark": 255
                },
                "wsSettings": {
                    "headers": {
                        "host": "<str:host>"
                    },
                    "path": "<str:path>"
                },
                "tlsSettings": {
                    "allowInsecure": true,
                    "serverName": "<str:host>"
                }
            },
            "tag": "proxy"
        },
        {
            "protocol": "freedom",
            "settings": {
                "domainStrategy": "UseIP"
            },
            "streamSettings": {
                "sockopt": {
                    "mark": 255
                }
            },
            "tag": "direct"
        },
        {
            "protocol": "blackhole",
            "settings": {
                "response": {
                    "type": "http"
                }
            },
            "tag": "block"
        },
        {
            "protocol": "dns",
            "streamSettings": {
                "sockopt": {
                    "mark": 255
                }
            },
            "tag": "dns-out"
        }
    ]
}'''

    config = json.loads(proxy_global_raw_config)
    server = config['outbounds'][0]['settings']['vnext'][0]
    server['address'] = node.add
    server['port'] = int(node.port)
    user = server['users'][0]
    user['id'] = node.id
    user['alterId'] = int(node.aid)

    stream_settings = config['outbounds'][0]['streamSettings']
    if (len(node.tls)):
        stream_settings['security'] = node.tls
        stream_settings['tlsSettings']['serverName'] = node.host
    else:
        stream_settings['security'] = 'none'
        stream_settings['tlsSettings']['serverName'] = ''

    stream_settings['network'] = node.net
    if node.net == 'ws':
        stream_settings['wsSettings']['headers']['host'] = node.host
        stream_settings['wsSettings']['path'] = node.path

    return config

def gen_proxy_global(node: NodeItem, advance_config: AdvanceConfig) -> dict:
    proxy_global_raw_config = '''
{	
    "dns": {
        "servers": [
            "<str:remote_dns>",
            {
                "address": "<str:local_dns>",
                "domains": [
                    "ntp.org",
                    "geosite:speedtest",
                    "<str:add>"
                ],
                "port": 53
            }
        ]
    },
    "routing": {
		"domainStrategy": "IPOnDemand",
		"rules": [{
				"inboundTag": [
					"transparent"
				],
				"network": "udp",
				"outboundTag": "dns-out",
				"port": 53,
				"type": "field"
			},
			{
				"inboundTag": [
					"transparent"
				],
				"network": "udp",
				"outboundTag": "direct",
				"port": 123,
				"type": "field"
			},
			{
				"domain": [
					"geosite:category-ads-all"
				],
				"outboundTag": "block",
				"type": "field"
			},
			{
				"outboundTag": "direct",
				"protocol": [
					"bittorrent"
				],
				"type": "field"
			},
			{
				"ip": [
					"geoip:private"
				],
				"outboundTag": "direct",
				"type": "field"
			}
		]
	}
}'''
    config = json.loads(proxy_global_raw_config)
    update_dns_config(config, advance_config)
    config['dns']['servers'][1]['domains'][2] = node.add

    config.update(gen_proxy_outbands(node))
    return config

def gen_proxy_auto(node: NodeItem, advance_config: AdvanceConfig) -> dict:
    proxy_auto_raw_config = '''
{
	"dns": {
		"servers": [
			"<str:remote_dns>",
			{
				"address": "<str:local_dns>",
				"domains": [
					"geosite:cn",
					"ntp.org",
					"geosite:speedtest",
					"<str:add>"
				],
				"port": 53
			}
		]
	},
	"routing": {
		"domainStrategy": "IPOnDemand",
		"rules": [{
				"inboundTag": [
					"transparent"
				],
				"network": "udp",
				"outboundTag": "dns-out",
				"port": 53,
				"type": "field"
			},
			{
				"inboundTag": [
					"transparent"
				],
				"network": "udp",
				"outboundTag": "direct",
				"port": 123,
				"type": "field"
			},
			{
				"domain": [
					"geosite:category-ads-all"
				],
				"outboundTag": "block",
				"type": "field"
			},
			{
				"outboundTag": "direct",
				"protocol": [
					"bittorrent"
				],
				"type": "field"
			},
			{
				"ip": [
					"geoip:private",
					"geoip:cn"
				],
				"outboundTag": "direct",
				"type": "field"
			},
			{
				"domain": [
					"geosite:cn"
				],
				"outboundTag": "direct",
				"type": "field"
			}
		]
	}
}
'''
    config = json.loads(proxy_auto_raw_config)
    update_dns_config(config, advance_config)
    config['dns']['servers'][1]['domains'][3] = node.add

    config.update(gen_proxy_outbands(node))
    return config

def update_local_dns_config(config:dict, local_dns:str):
    config['dns']['servers'][1]['address'] = local_dns

    local_rule_raw = '''
{
    "ip": [
        "223.5.5.5"
    ],
    "outboundTag": "direct",
    "type": "field"
}'''
    local_dns_rule = json.loads(local_rule_raw)
    local_dns_rule['ip'][0] = local_dns

    rules : list = config['routing']['rules']
    rules.append(local_dns_rule)

def update_remote_dns_config(config:dict, remote_dns:str):
    config['dns']['servers'][0] = remote_dns
    remote_rule_raw = '''
{
    "ip": [
        "8.8.8.8"
    ],
    "outboundTag": "proxy",
    "type": "field"
}
'''
    remote_dns_rule = json.loads(remote_rule_raw)
    remote_dns_rule['ip'][0] = remote_dns

    rules : list = config['routing']['rules']
    rules.append(remote_dns_rule)

def update_dns_config(config:dict, advance_config:AdvanceConfig):
    if len(advance_config.dns.local_dns):
        update_local_dns_config(config, advance_config.dns.local_dns)
    else:
        update_local_dns_config(config, DnsConfig.default_local_dns)

    if len(advance_config.dns.remote_dns):
        update_remote_dns_config(config, advance_config.dns.remote_dns)
    else:
        update_remote_dns_config(config, DnsConfig.default_remote_dns)
