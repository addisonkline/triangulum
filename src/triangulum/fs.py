import os


def init_triangulum_fs() -> None:
    """
    Create the necessary files and directories for Triangulum in the local file system.
    """
    os.makedirs(".triangulum", exist_ok=True)
    os.makedirs(".triangulum/logs", exist_ok=True)
    os.makedirs(".triangulum/cache", exist_ok=True)
