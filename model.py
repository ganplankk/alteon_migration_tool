def port_info(model, module):
    if "K3200X" == model.upper():
        if module:
            qsfp = input("QSFP+ Module? (Y/N) ").strip().upper()
            if qsfp == "Y":
                return {str(i): f"{j}" for i, j in zip(range(1, 19), range(1, 19))}
            return {str(i): f"{j}" for i, j in zip(range(1, 25), range(1, 25))}
        return {str(i): f"{j}" for i, j in zip(range(1, 17), range(1, 17))}
    elif "K5600" == model.upper():
        if module:
            return {str(i): f"{j}" for i, j in zip(range(1, 33), range(1, 33))}

        # return list(range(1, 25))
        return {str(i): f"{j}" for i, j in zip(range(1, 25), range(1, 25))}
    elif "K1800" == model.upper():
        model_port = {
            **{str(i): f"ge{j}" for i, j in zip(range(1, 21), range(1, 21))},
            **{str(20 + k): f"xg{k}" for k in range(1, 3)}
        }
        return model_port