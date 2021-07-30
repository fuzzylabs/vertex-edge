from typing import List


def to_sacred_params_for_vertex(kwargs, in_dict=False) -> List[str]:
    def to_string(_key, _val):
        if not in_dict:
            return f"{_key}={_val}"
        else:
            return f"\"{_key}\": {_val}"
    sacred_params = []
    if not in_dict:
        sacred_params += ["is_vertex=False"]
    for key, val in kwargs.items():
        if key == "_run":
            continue
        elif isinstance(val, dict):
            d = to_sacred_params_for_vertex(val, True)
            d_str = "{" + ", ".join(d) + "}"
            sacred_params += [to_string(key, d_str)]
        elif isinstance(val, str):
            sacred_params += [to_string(key, f"\"{str(val)}\"")]
        else:
            sacred_params += [to_string(key, str(val))]
    return sacred_params


def to_sacred_with_statement(sacred_params) -> str:
    joined_params = " ".join([f"'{x}'" for x in sacred_params])
    return f"with {joined_params}"
