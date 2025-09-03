import re

class Configuration:
    def __init__(self):
        self.config_text = ""
        self.vlan_id = None
        self.vlan_configs = {}
        self.allowed_ports = {}
        self.port_name = {}
        self.ip_address = {}
        self.default_gw = {}
        self.static_routes = []
        self.slb_vip_list = []
        self.vrrp_vip_list = []
        self.vrrp_vid_list = []
        self.health_check_list = {}
        self.real_list = {}
        self.slb_info = {}
        self.slb_final = {}
        self.group_members = {}
        self.slb_conf = {}
        self.slb_final_config = {}
        # self.slb_service_info = {}

    def port_desc(self, config_text: str, allowed_ports: dict):
        self.allowed_ports = allowed_ports
        allowed = set(self.allowed_ports.keys())  # 허용 포트 (문자열 키라고 가정)
        out = []
        cur_port = None
        self.port_name = {}

        for raw in config_text.splitlines():
            line = raw.rstrip("\r")

            if m := re.match(r'^\s*/c/port\s+(\d+)\s*$', line, re.I):
                cur_port = m.group(1)
                continue

            if cur_port is not None:
                # name "....."
                if m := re.match(r'^\s*name\s+"([^"]+)"\s*$', line, re.I):
                    self.port_name[cur_port] = m.group(1)
                    continue

        out.append(f'!! Port Description')
        for p, n in self.port_name.items():
            if allowed and p not in allowed:
                continue
            out.append(f'port {self.allowed_ports[p]} description {quote_delete(n)}')
        out.append(f'!!')
        return out

    def port_boundary(self, allowed_ports: dict):
        self.allowed_ports = allowed_ports
        if self.allowed_ports is None:
            raise ValueError("allowed_ports가 None입니다.")

        out = []
        p_list = []
        out.append(f'!! Port Boundary Configuration')
        out.append(f'port-boundary 10')
        for p in sorted(self.allowed_ports.keys(), key=lambda x: int(x)):
            p_list.append(f'{self.allowed_ports[p]}')
        out.append("port "+", ".join(p_list))
        out.append(f'apply')
        out.append(f'!!')
        return out

    def vlan_create(self, config_text: str, allowed_ports: dict):
        self.allowed_ports = allowed_ports
        if self.allowed_ports is None:
            raise ValueError("allowed_ports가 None입니다.")

        self.vlan_configs = {}
        self.vlan_id = None

        for raw in config_text.splitlines():
            line = raw.rstrip("\r")

            # /c/l2/vlan <VID>
            m_vlan = re.match(r'^\s*/c/l2/vlan\s+(\d+)\s*$', line, re.I)
            if m_vlan:
                self.vlan_id = m_vlan.group(1)
                self.vlan_configs[self.vlan_id] = set()
                continue

            # def 1 2 4 5 6 8
            if self.vlan_id is not None:
                m_port = re.match(r'^\s*def\s+([\d\s,]+)\s*$', line, re.I)
                if m_port:
                    tokens = re.split(r'[,\s]+', m_port.group(1).strip())
                    for p in filter(None, tokens):
                        # 포트 번호 -> 포트명 매핑 (예: '1' -> 'ge1')
                        name = allowed_ports.get(str(p))
                        if name is None:
                            # 매핑 모르면 스킵하거나 에러/로그
                            # print(f"경고: VLAN {self.vlan_id}에 알 수 없는 포트 {p}")
                            continue
                        self.vlan_configs[self.vlan_id].add(name)
                    continue

        # VLAN 블록이 하나도 없었거나, 어떤 VLAN도 포트가 없으면 기본 VLAN 10 생성
        if not self.vlan_configs:
            self.vlan_configs["10"] = set(allowed_ports.values())

        out = []
        out.append(f'!! VLAN Configuration')
        for vid, ports in self.vlan_configs.items():
            # 포트가 비었으면(정의가 없었으면) 전체 포트로 기본 세팅
            if not ports:
                ports = set(allowed_ports.values())

            out.append(f"vlan v{vid} vid {vid}")
            out.append(f"vlan v{vid} port {','.join(sorted(ports))} untagged")
        out.append(f'!!')
        return out
    def ip_config(self, config_text: str):
        p_cmd = re.compile(r'^\s*/c/.*$', re.I)
        p_if = re.compile(r'^\s*/c/l3/if\s+(\d+)\s*$', re.I)
        # p_addr = re.compile(r'^\s*addr\s+(\d{1,3}(?:\.\d{1,3}){3})(?:/(\d{1,2}))?\s*$', re.I)
        p_addr = re.compile(r'^\s*addr\s+(\d{1,3}(?:\.\d{1,3}){3})\s*$', re.I)
        p_mask = re.compile(r'^\s*mask\s+(\d{1,3}(?:\.\d{1,3}){3})\s*$', re.I)
        p_vlan = re.compile(r'^\s*vlan\s+(\d+)\s*$', re.I)

        self.ip_address = {}  # 예: {'1': {'ip': '192.1.3.13', 'mask': '255.255.255.0', 'prefix': 24}}
        cur_if = None       # 현재 "/c/l3/if <num>" 블록 번호 (아니면 None)

        for raw in config_text.splitlines():
            line = raw.rstrip("\r")
            if p_cmd.match(line):
                if m := p_if.match(line): ## 여러 행 중 if addr 패턴만 확인 하도록 if 문 설정 else 에서는 cur_if = None 처리
                    cur_if = m.group(1)  # 문자열키로 통일 (정수로 쓰고 싶으면 int(...)로)
                    self.ip_address.setdefault(cur_if, {"ip": None, "mask": None, "prefix": None, "vid": None})

                else:
                    cur_if = None  # if 블록이 아니면 컨텍스트 해제 (=> VRRP 밑 addr은 무시됨)
                    # print("DEBUG cur_if before mask:", cur_if, "| line:", repr(line))
                continue

            # 인터페이스 블록 안에서만 addr/mask 처리
            if cur_if is not None:
                if m := p_addr.match(line):
                    ip = m.group(1)
                    self.ip_address[cur_if]['ip'] = ip
                    self.ip_address[cur_if]['mask'] = "255.255.255.0" ## default mask 설정
                    self.ip_address[cur_if]['prefix'] = 24            ## default prefix 설정
                    self.ip_address[cur_if]['vid'] = "99"             ## default VLAN ID 설정
                    continue

                if m := p_mask.match(line):
                    import ipaddress
                    self.ip_address[cur_if]['mask'] = m.group(1)
                    self.ip_address[cur_if]['prefix'] = ipaddress.IPv4Network(f"0.0.0.0/{self.ip_address[cur_if]['mask']}").prefixlen
                    continue

                if m := p_vlan.match(line):
                    self.ip_address[cur_if]['vid'] = m.group(1)
                    continue

        out = []
        out.append(f'!! IP address Configuration')
        for if_num, ip_info in self.ip_address.items():
            if ip_info['ip'] and ip_info['mask'] and ip_info['vid']:
                out.append(f"interface v{ip_info['vid']} ip address {ip_info['ip']}/{ip_info['prefix']}")
        out.append(f'!!')
        return out
    def default_gateway(self, config_text: str):
        p_cmd = re.compile(r'^\s*/c/.*$', re.I)
        p_gw = re.compile(r'^\s*/c/l3/gw\s+(\d+)\s*$', re.I)
        p_addr = re.compile(r'^\s*addr\s+(\d{1,3}(?:\.\d{1,3}){3})\s*$', re.I)

        cur_block = None

        for raw in config_text.splitlines():
            line = raw.strip()
            if p_cmd.match(line):
                if m := p_gw.match(line):  # 여러 행 중 if addr 패턴만 확인 하도록 if 문 설정 else 에서는 cur_if = None 처리
                    cur_block = m.group(1)  # 문자열키로 통일 (정수로 쓰고 싶으면 int(...)로)
                else:
                    cur_block = None
            # 블록 시작
            if cur_block is not None:
                if m := p_addr.match(line):
                    addr = m.group(1)
                    self.default_gw[cur_block] = addr
                    continue
        out = []
        out.append(f'!! Default Gateway Configuration')
        for num, addr in self.default_gw.items():
            out.append(f"route default gateway {addr} priority {101 - int(num)}")
        out.append(f'!! ')
        return out
    def static_routing(self, config_text: str):
        p_route_block = re.compile(r'^\s*/c/l3/route/ip4\s*$', re.I)
        p_add = re.compile(r'^\s*add\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+(\d+)\s*$', re.I)

        cur_block = None
        out = []
        for raw in config_text.splitlines():
            line = raw.strip()

            if p_route_block.match(line):
                cur_block = "/c/l3/route/ip4"
                continue
            # add 라인
            if m := p_add.match(line):
                dst, mask, gw, metric = m.groups()
                import ipaddress
                prefix = ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
                out.append(f"route network {dst}/{prefix} gateway {gw}")
                continue
            # 블록 해제 조건 (다른 /c/ 명령 만나면 해제)
            if line.startswith("/c/") and not p_route_block.match(line):
                cur_block = None

        return out
    ## VRRP VIP 및 SLB VIP 파싱
    def vrrp_config(self, config_text: str):

        import random
        import re

        p_vrrp_block = re.compile(r'^\s*/c/l3/vrrp/vr\s+(\d+)\s*$', re.I)
        p_vrid = re.compile(r'^\s*vrid\s+(\d+)\s*$', re.I)
        p_prio = re.compile(r'^\s*prio\s+(\d+)\s*$', re.I)
        p_addr = re.compile(r'^\s*addr\s+(\d{1,3}(?:\.\d{1,3}){3})\s*$', re.I)

        # SLB 관련
        p_slb_block = re.compile(r'^\s*/c/slb/virt\s+(\d+)\s*$', re.I)
        p_slb_addr = re.compile(r'^\s*vip\s+(\d{1,3}(?:\.\d{1,3}){3})\s*$', re.I)
        # service 뒤 프로토콜은 선택적
        p_slb_vport = re.compile(r'^\s*/c/slb/virt\s+(\d+)/service\s+(\d+)(?:\s+([A-Za-z-]+))?\s*$', re.I)
        p_slb_group = re.compile(r'^\s*group\s+(\d+)\s*$', re.I)

        def normalize_proto(s: str | None) -> str:
            if not s:
                return "tcp"
            s = s.lower()
            return "tcp" if s == "basic-slb" else s

        cur_virt = None
        # virt별 서비스 인덱스 관리 및 마지막 서비스 인덱스 기억
        svc_index = {}  # {virt_id: next_int_index}
        last_idx_for_virt = {}  # {virt_id: last_assigned_idx(str)}
        vrrp_info = {}  # {"vr_conf_id": {"vrid":..., "prio":..., "vip":...}}

        for raw in config_text.splitlines():
            line = raw.strip()

            m = p_slb_block.match(line)
            if m:
                cur_virt = m.group(1)
                self.slb_info.setdefault(cur_virt, {
                    "vip": None,
                    "vport": {},
                    "protocol": "tcp",
                    "group": {},
                    "hc": []
                })
                svc_index.setdefault(cur_virt, 1)
                last_idx_for_virt.setdefault(cur_virt, None)
                continue

            # VIP 라인
            if cur_virt is not None:
                m = p_slb_addr.match(line)
                if m:
                    vip = m.group(1)
                    self.slb_info[cur_virt]["vip"] = vip
                    self.slb_vip_list.append(vip)
                    continue

            # 서비스 라인 (/c/slb/virt <VID>/service <PORT> [PROTO])
            m = p_slb_vport.match(line)
            if m:
                virt_id = m.group(1)
                port = m.group(2)
                proto = normalize_proto(m.group(3))

                # 방어적 초기화 (virt 블록을 건너뛴 경우 대비)
                self.slb_info.setdefault(virt_id, {
                    "vip": None,
                    "vport": {},
                    "protocol": "tcp",
                    "group": {}
                })
                svc_index.setdefault(virt_id, 1)
                last_idx_for_virt.setdefault(virt_id, None)

                idx = str(svc_index[virt_id])  # "1", "2", ...
                self.slb_info[virt_id]["vport"][idx] = port
                self.slb_info[virt_id]["protocol"] = proto
                last_idx_for_virt[virt_id] = idx
                svc_index[virt_id] += 1

                # 현재 virt 컨텍스트 갱신
                cur_virt = virt_id
                continue

            # group 라인 → 직전에 본 서비스 인덱스에 매핑
            if cur_virt is not None:
                m = p_slb_group.match(line)
                if m:
                    grp = m.group(1)
                    last_idx = last_idx_for_virt.get(cur_virt)
                    if last_idx:
                        self.slb_info[cur_virt]["group"][last_idx] = grp
                    continue

            # 다른 /c/ 라인이 오면 SLB 컨텍스트 해제 (단, service/virt 라인은 예외)
            if line.startswith("/c/") and not p_slb_vport.match(line) and not p_slb_block.match(line):
                cur_virt = None

            # --- VRRP 블록 파싱
            m = p_vrrp_block.match(line)
            if m:
                cur_vrrp = m.group(1)
                vrrp_info[cur_vrrp] = {"vrid": None, "prio": None, "vip": None}
                continue

            if 'cur_vrrp' in locals() and cur_vrrp is not None:
                m = p_vrid.match(line)
                if m:
                    vrrp_info[cur_vrrp]["vrid"] = m.group(1)
                    self.vrrp_vid_list.append(m.group(1))
                    continue
                m = p_prio.match(line)
                if m:
                    vrrp_info[cur_vrrp]["prio"] = m.group(1)
                    continue
                m = p_addr.match(line)
                if m:
                    vip = m.group(1)
                    vrrp_info[cur_vrrp]["vip"] = vip
                    self.vrrp_vip_list.append(vip)
                    continue

            if line.startswith("/c/") and not p_vrrp_block.match(line):
                if 'cur_vrrp' in locals():
                    cur_vrrp = None

        # 디버그용 JSON 출력 (원하면 유지)
        # print(json.dumps(self.slb_info, indent=4, ensure_ascii=False))

        # SLB VIP에 없는 VRRP VIP만 추출
        vrrp_only_vips = set(self.vrrp_vip_list) - set(self.slb_vip_list)

        out = []
        # 랜덤 선택은 1번만
        choice_vid = random.choice(self.vrrp_vid_list) if self.vrrp_vid_list else None
        chosen = vrrp_info.get(choice_vid) if choice_vid else None
        out.append(f'!! VRRP Configuration')
        if chosen and chosen.get('vrid') and chosen.get('prio'):
            out.append(f"vrrp {chosen['vrid']}")
            out.append(f"priority {chosen['prio']}")

            vip_for_ha = next(iter(vrrp_only_vips), None)  # 없으면 None
            if vip_for_ha:
                out.append(f"interface v{chosen['vrid']} vip {vip_for_ha}")
            else:
                out.append("NO HA VRRP VIP ADDRESS")

            # allowed_ports가 정의되어 있고 '1' 키가 있다면 트래킹 추가
            if getattr(self, 'allowed_ports', None) and '1' in self.allowed_ports:
                out.append(f"track single-port {self.allowed_ports['1']}")
        else:
            out.append("# VRRP VIP 주소가 없습니다.")
        out.append(f'!! ')
        return out
    def parse_group_members(self, config_text: str):
        p_group_blk = re.compile(r'^\s*/c/slb/group\s+(\d+)\s*$', re.I)
        p_add = re.compile(r'^\s*add\s+(\d+)\s*$', re.I)
        cur_gid = None

        for raw in config_text.splitlines():
            line = raw.strip()

            m = p_group_blk.match(line)
            if m:
                cur_gid = m.group(1)
                self.group_members.setdefault(cur_gid, [])
                continue

            # if cur_gid is not None:
            #     m = p_add.match(line)
            #     if m:
            #         rid = m.group(1)
            #         self.group_members[cur_gid].append(rid)
            #         continue
            if cur_gid is not None:
                m = p_add.match(line)
                if m:
                    rid = m.group(1)
                    if rid not in self.group_members[cur_gid]:  # ✅ 중복 방지
                        self.group_members[cur_gid].append(rid)
                    continue
            # 다른 /c/ 블록 만나면 해제
            if line.startswith("/c/") and not p_group_blk.match(line):
                cur_gid = None

        return self.group_members
    def slb_services_with_real_members(self):
        for virt_id, info in self.slb_info.items():
            vports = info.get("vport", {})
            groups = info.get("group", {})
            proto = info.get("protocol", "tcp")
            vip = info.get("vip")

            services = []
            # vport는 {"1":"49999","2":"50000",...} 형태 — 인덱스 기준으로 group 매칭
            for idx, port in sorted(vports.items(), key=lambda kv: int(kv[0])):
                gid = groups.get(idx)  # 이 idx가 가리키는 group 번호 (문자열)
                members = self.group_members.get(gid, []) if hasattr(self, "group_members") else []
                services.append({
                    "port": port,
                    "protocol": proto,
                    "group": gid,
                    "members": members,
                    "hc": []
                })

            self.slb_final[virt_id] = {
                "vip": vip,
                "services": services,

            }

        return self.slb_final

    def real_config(self, config_text: str):
        p_real_block = re.compile(r'^\s*/c/slb/real\s+(\d+)\s*$', re.I)
        p_rip = re.compile(r'^\s*rip\s+(\d{1,3}(?:\.\d{1,3}){3})\s*$', re.I)
        p_backup = re.compile(r'^\s*backup\s+(\d+)\s*$', re.I)
        p_weight = re.compile(r'^\s*weight\s+(\d+)\s*$', re.I)
        p_hc = re.compile(r'^\s*health\s+(\d+)\s*$', re.I)

        cur_real = None
        real_info = {}

        for raw in config_text.splitlines():
            line = raw.strip()

            if m := p_real_block.match(line):
                cur_real = m.group(1)
                real_info[cur_real] = {"id": cur_real, "rip": None, "backup": None, "weight": None, "hc": None}
                continue

            if cur_real is not None:
                if m := p_rip.match(line):
                    real_info[cur_real]["rip"] = m.group(1)
                    continue
                if m := p_backup.match(line):
                    real_info[cur_real]["backup"] = m.group(1)
                    continue
                if m := p_weight.match(line):
                    real_info[cur_real]["weight"] = m.group(1)
                    continue
                if m := p_hc.match(line):
                    real_info[cur_real]["hc"] = m.group(1)
                    continue
            if line.startswith("/c/") and not p_real_block.match(line):
                cur_real = None

        out = []
        for real_id, info in real_info.items():
            if info['id'] and info['rip']:
                out.append(f"!!Real Configuration")
                out.append(f"real {info['id']}")
                out.append(f"rip {info['rip']}")
                out.append(f"backup {info.get('backup') or ''}")
                out.append(f"weight {info.get('weight') or '1'}")
                out.append(f"health-check {info.get('hc') or ''}")
                out.append(f"apply")
                out.append(f"exit")
                out.append(f"!! ")

        return out
    def slb_config(self, config_text: str):
        self.vrrp_config(config_text)
        self.parse_group_members(config_text)

    def health_check(self, config_text: str):
        p_hc_block = re.compile(r'^\s*/c/slb/advhc/health\s+(\d+)\s+([A-Za-z]+)\s*$', re.I)
        p_interval = re.compile(r'^\s*inter\s+(\d+)\s*$', re.I)
        p_timeout = re.compile(r'^\s*timeout\s+(\d+)\s*$', re.I)
        p_retry = re.compile(r'^\s*retry\s+(\d+)\s*$', re.I)

        cur_hc = None
        found_hc = False
        hc_info = {}

        for raw in config_text.splitlines():
            line = raw.strip()

            if m := p_hc_block.match(line):
                found_hc = True
                cur_hc = m.group(1)
                cur_type = m.group(2).lower()
                hc_info[cur_hc] = {
                    "id": cur_hc,
                    "type": cur_type,
                    "interval": None,
                    "timeout": None,
                    "retry": None,
                    "port": None
                }
                continue

            if cur_hc is not None:
                if m := p_interval.match(line):
                    hc_info[cur_hc]["interval"] = m.group(1)
                    continue
                if m := p_timeout.match(line):
                    hc_info[cur_hc]["timeout"] = m.group(1)
                    continue
                if m := p_retry.match(line):
                    hc_info[cur_hc]["retries"] = m.group(1)
                    continue

            if line.startswith("/c/") and not p_hc_block.match(line):
                cur_hc = None
        out = []
        out.append(f'!! Health Check Configuration')
        i = 1

        if not found_hc:
            port_list = self.health_check_ports()
            for i in range(len(port_list)):
                out.append(f"health-check {i+1}")
                out.append("type tcp")
                out.append(f"port {port_list[i]}")
                out.append("interval 10")
                out.append("timeout 3")
                out.append("retry 3")
                out.append("apply")
                out.append("exit")
                i += 1
            out.append(f'!! ')
            return out
        port_list = self.health_check_ports()

        for i in range(len(port_list)):
            out.append(f"health-check {i+1}")
            out.append("type tcp")
            out.append(f"port {port_list[i]}")
            out.append("interval 10")
            out.append("timeout 3")
            out.append("retry 3")
            i += 1

        for hc_id, info in hc_info.items():

            if info['id'] and info['type']:
                out.append(f"health-check {i}")
                out.append(f"type {info['type']}")
                out.append(f"interval {info.get('interval') or 10}")
                out.append(f"timeout {info.get('timeout') or 3}")
                out.append(f"retry {info.get('retry') or 3}")
                i += 1
        out.append(f'!! ')

        return out

    def health_check_ports(self):
        port_list = []
        slb_conf = self.slb_services_with_real_members()
        # for svc_id, services in self.slb_services_with_real_members.items():
        for svc_id, services in slb_conf.items():
            for svc in services['services']:
                port_list.append(svc['port'])
        return port_list

    def health_check_apply(self):
        health_id = self.health_check(self.config_text)

        ids = [str(m.group(1)) for line in health_id if (m := re.match(r'^health-check\s+(\d+)$', line))]
        i = 0
        slb_real_final = self.slb_services_with_real_members()
        for id, services in slb_real_final.items():
            out = []
            out.append(f'!! SLB Configuration')
            for svc in services['services']:
                out.append(f"slb s{i + 1}")
                port = svc['port']
                proto = svc['protocol']
                out.append(f"vip {services['vip']} protocol {proto} vport {port}")
                members = svc.get('members', [])
                out.append(f"health-check {ids[i]}")
                if members:
                    out.append(f"real {','.join(members)}")
                    out.append("apply")
                    out.append("exit")
                else:
                    out.append(f"")
                    out.append("apply")
                    out.append("exit")
                i += 1
            out.append(f'!! ')

            return out

    def finalize(self, alteon_conf: str, allowed_ports: dict):
        sections = []
        sections += self.port_desc(alteon_conf, allowed_ports)
        sections += self.port_boundary(allowed_ports)
        sections += self.vlan_create(alteon_conf, allowed_ports)
        sections += self.ip_config(alteon_conf)
        sections += self.default_gateway(alteon_conf)
        sections += self.static_routing(alteon_conf)

        self.slb_config(alteon_conf)
        sections += self.real_config(alteon_conf)
        sections += self.health_check(alteon_conf)
        sections += self.health_check_apply()


        # 출력: 콤마 포함 줄만 개행 분할
        for line in sections:
            # if line.startswith("real "):
            #     for part in line[len("real "):].split(","):
            #         print("real " + part.strip())
            if "!!" in line:
                for part in line.split(","):
                    print(part.strip())
            else:
                print(line)


def quote_delete(s: str) -> str:
    # if re.search(r'\s|[#";]', s):
    if re.search(r'\s|\"', s):
        # return '"' + s.replace('"', r'\"') + '"'
        return s.replace('"', '')
    return s
