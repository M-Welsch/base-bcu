class BuHddSetter:
    def __init__(self) -> None:
        raise NotImplementedError

    def set_connected_hdd_as_backup_hdd(self):
        raise NotImplementedError


if __name__ == "__main__":
    bhs = BuHddSetter()
    bhs.set_connected_hdd_as_backup_hdd()
