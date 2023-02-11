import pybvfs

pybvfs.core.createFs("fs.bvfs")
fs = pybvfs.core.BVFS("fs.bvfs")
fs.mkdir("/abc")
fs.mkdir("/abc/xyz")
for x in range(20):
    fs.mkdir(f"/dirno{x}")

print(fs.lsdir("/"))
print(fs.lsdir("/abc"))
print(fs.lsdir("/abc/xyz"))

fs.close()

#print(pybvfs.fsdump.dumpsystem("fs.bvfs"))