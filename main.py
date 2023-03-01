import pybvfs
import time

pybvfs.core.createFs("fs.bvfs")
fs = pybvfs.core.BVFS("fs.bvfs")
fs.mkdir("/abc")

fp = fs.open("/abc/Hello.txt", "w")

with open('testdata/bigbunny.mkv', 'rb') as file:
    data = file.read()

# data = b''
# for x in range(200000):
#     data += "abcd{x}\x01".format(x=x).encode('utf-8')

datamb = (len(data)/1024)/1024

tw_1 = time.perf_counter()
fp.write(data)
tw_2 = time.perf_counter()
tw_time = tw_2 - tw_1
del fp

fp2 = fs.open("/abc/Hello.txt", "r")
tr_1 = time.perf_counter()
dataread = fp2.read()
tr_2 = time.perf_counter()
tr_time = tr_2 - tr_1
del fp2

datareadmb = (len(dataread)/1024)/1024

fs.close()

with open("fs.bvfs", "r+b") as fp:
#    pybvfs.fsfix.removeTruncatingBlocks(fp)
#    print(pybvfs.fsdump.dumpsystem(fp))
    pass

print(datamb)

print(f"Is data equal?: {dataread==data}")
print(f"Write speed: {round(datamb/tw_time, 4)} MB/s")
print(f"Read speed: {round(datareadmb/tr_time, 4)} MB/s")