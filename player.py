from main import alteon_conf, allowed_ports
from alteon_config_migration import *

migration = Configuration()
migration.vlan_create(alteon_conf, allowed_ports)
migration.port_desc(alteon_conf, allowed_ports)
migration.ip_config(alteon_conf)
migration.default_gateway(alteon_conf)
migration.static_routing(alteon_conf)
migration.real_config(alteon_conf)
migration.slb_config(alteon_conf)
migration.health_check(alteon_conf)
final = migration.result