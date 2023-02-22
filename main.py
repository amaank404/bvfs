import pybvfs

pybvfs.core.createFs("fs.bvfs")
fs = pybvfs.core.BVFS("fs.bvfs")
fs.mkdir("/abc")

fp = fs.open("/abc/Hello.txt", "w")

data = b''
for x in range(200):
    data += "abcd{x}\x01".format(x=x).encode('utf-8')

fp.write(data)
del fp

fp2 = fs.open("/abc/Hello.txt", "r")
dataread = fp2.read()
del fp2

fs.close()

with open("fs.bvfs", "r+b") as fp:
#    pybvfs.fsfix.removeTruncatingBlocks(fp)
    print(pybvfs.fsdump.dumpsystem(fp))

print(f"Is data equal?: {dataread==data}")
