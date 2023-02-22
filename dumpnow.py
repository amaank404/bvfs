import pybvfs.fsdump

with open("fs.bvfs", "rb") as file:
    print(pybvfs.fsdump.dumpsystem(file))