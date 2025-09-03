import os
from model import port_info as get_port_info
from alteon_config_migration import *

path = input("읽을 파일 경로: ").strip()
try:
    with open(path, "r", encoding="utf-8") as f:
        alteon_conf = f.read()
    with open(os.path.join(os.path.dirname(path), "new_conf.txt"), "w", encoding="utf-8") as new_conf:
        pass
except FileNotFoundError:
    print("파일을 찾을 수 없습니다")
except UnicodeDecodeError:
    print("인코딩 불가, utf-8 아닐 수 있습니다.")

model = input("파이오링크 L4 Switch 모델 명 입력 ").strip()
add_module = input("네트워크 모듈 추가 여부(Y/N) ").strip().upper()
allowed_ports = get_port_info(model, add_module)
if allowed_ports is None:
    raise ValueError(f"알 수 없는 모델: {model}")
out_path = os.path.join(os.path.dirname(path), "new_conf.txt")

def write_config(lines):
    file_path = os.path.join(os.path.dirname(path), "new_conf.txt")
    with open(file_path, "a", encoding="utf-8") as w:
        w.write("\n".join(lines) + "\n")


#F:\200_________바탕화면\방효성\000_______________PIOLINK\210_업무\120_사이트\116_KT(분당)\알테온설정\20250821_L4#1(cfg dump).txt
#F:\200_________바탕화면\방효성\000_______________PIOLINK\210_업무\120_사이트\115_KT(과천)\L4SW#1_10.1.253.4.txt

