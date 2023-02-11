import pybvfs

pybvfs.core.createFs("fs.bvfs")
fs = pybvfs.core.BVFS("fs.bvfs")
fs.mkdir("/abc")
fs.mkdir("/abc/xyz")
for x in range(15):
    fs.mkdir(f"/dirno{x}")

print(fs.lsdir("/"))
print(fs.lsdir("/abc"))
print(fs.lsdir("/abc/xyz"))

for x in range(10):
    fs.rmdir(f"/dirno{x}")

print(pybvfs.fsdump.dumpsystem(fs._fp))

fs.rmdir("/dirno10")
fs.mkdir("/abcdef")
fs.mkdir("/abcdef/abc231")
for x in range(15):
    fs.mkdir(f"/dirno{x}")
print(fs.lsdir("/"))

fs.close()

with open("fs.bvfs", "r+b") as fp:
    pybvfs.fsfix.removeTruncatingBlocks(fp)
    print(pybvfs.fsdump.dumpsystem(fp))