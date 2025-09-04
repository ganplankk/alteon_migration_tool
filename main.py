import os
from alteon_config_migration import Configuration
from model import port_info as get_port_info

allowed_ports = {}
alteon_conf = ""
model = ""
qsfp = ""

def main():
    global alteon_conf
    global model
    global allowed_ports
    path = input("읽을 파일 경로: ").strip()
    try:
        if path.startswith("#"):
            raise TypeError
    except TypeError:
        print("입력 값 앞에 # 을 제거해주세요.")
        main()
    try:
        with open(path, "r", encoding="utf-8") as f:
            alteon_conf = f.read()
            print(f"파일 읽기 완료: {path}")

    except FileNotFoundError:
        print("파일을 찾을 수 없습니다")
        main()
    except UnicodeDecodeError:
        print("인코딩 불가, utf-8 아닐 수 있습니다.")
        main()
    model = input("파이오링크 L4 Switch 모델 명 입력 ").strip()
    add_module = input("네트워크 모듈 추가 여부(Y/N) ").strip().upper()
    if add_module:
        global qsfp
        qsfp = input("QSFP+ Module? (Y/N) ").strip().upper()

    allowed_ports = get_port_info(model, add_module, qsfp)
    if allowed_ports is None:
        print(f"알 수 없는 모델 : {model}")
        main()

    with open(os.path.join(os.path.dirname(path), "new_conf.txt"), "w", encoding="utf-8") as new_Conf:
        migration = Configuration()
        conf = migration.finalize(alteon_conf, allowed_ports)

        for line in conf:
            if "!!" in line:
                for part in line.split(","):
                    line = part.strip()
                    new_Conf.write(line + "\n")
            else:
                new_Conf.write(line.rstrip("\r\b") + "\n")

main()

