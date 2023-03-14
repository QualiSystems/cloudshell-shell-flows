def get_str_backup_type(conf) -> str:
    try:
        # in standards v2 backup_type is an Enum
        val = conf.backup_type.value
    except AttributeError:
        val = conf.backup_type
    return val
