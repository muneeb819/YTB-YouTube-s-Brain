def preflight(rights_status: str, has_user_approval: bool=False):
    if rights_status == "BLOCKED":
        return "BLOCK"
    if rights_status == "UNKNOWN":
        return "REPAIR"
    if not has_user_approval:
        return "REVIEW"
    return "PASS"
