

def log_msg(logger, msg: str, msg_type: str):
    """log fail colored red log pass colored green"""
    if msg_type == "fail":
        logger.error(msg)
    elif msg_type == "pass":
        logger.info(msg)
