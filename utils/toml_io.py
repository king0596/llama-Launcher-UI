"""TOML 序列化工具（轻量实现，避免依赖 tomli-w）。"""


def toml_dump(data, f):
    """将字典以 TOML 格式写入文件对象 f。"""
    for key, value in data.items():
        if isinstance(value, dict):
            f.write(f"[{key}]\n")
            for k, v in value.items():
                if isinstance(v, bool):
                    f.write(f"{k} = {'true' if v else 'false'}\n")
                else:
                    f.write(f"{k} = {repr(v)}\n")
            f.write("\n")
        else:
            if isinstance(value, bool):
                f.write(f"{key} = {'true' if value else 'false'}\n")
            else:
                f.write(f"{key} = {repr(value)}\n")
