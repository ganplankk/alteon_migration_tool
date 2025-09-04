def port_info(model: str, module: str, qsfp: str) -> dict[str, str]:
    model = model.upper().strip()
    module = module.upper().strip()
    qsfp = qsfp.upper().strip()

    def make_ports(count, prefix="ge"):
        return {str(i): f"{prefix}{i}" for i in range(1, count+1)}

    if model == "K3200X":
        if module == "Y":
            return make_ports(18) if qsfp == "Y" else make_ports(24)
        return make_ports(16)

    elif model == "K5600" or model == "K5200" or model == "K5400":
        if module == "Y":
            return make_ports(18) if qsfp == "Y" else make_ports(24)
        return make_ports(16)

    elif model == "K1800":
        return {
            **make_ports(20, "ge"),
            **{str(20+k): f"xg{k}" for k in range(1, 3)}
        }
