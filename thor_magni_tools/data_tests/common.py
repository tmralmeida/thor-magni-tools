

def log_msg(msg: str, msg_type: str):
    """log fail colored red log pass colored green"""
    if msg_type == "fail":
        print("\033[91m {}\033[00m".format(msg))
    elif msg_type == "pass":
        print("\033[92m {}\033[00m".format(msg))
