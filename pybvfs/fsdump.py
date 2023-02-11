from . import core
from functools import partial
from io import StringIO

intfb = partial(int.from_bytes, byteorder='big')

btype = {
    0: "Unknown",
    1: "Data",
    2: "SuperBlock",
    3: "NodeMetadata",
    4: "Directory",
    5: "Root"
}

def dumpsystem(system):
    ofp = StringIO()
    tprint = partial(print, file=ofp)
    with open(system, "r+b") as fp:
        bio = core.BlockIO(fp)

        tprint("Short View:")
        for x in range(bio.blocklen):
            blk = bio.readblock(x)
            tprint(f"{x} {hex(bio.bs*x)}: {btype[blk[0]]}")

        tprint("Detailed View:")
        for x in range(bio.blocklen):
            blk = bio.readblock(x)
            tprint(f"{x} {hex(bio.bs*x)}: {btype[blk[0]]}")
            if blk[0] == 0:
                if sum(blk) == 0:
                    tprint("\tEmpty Block")
                else:
                    tprint(f"\tData in Block: {sum(blk)}")
            
            elif blk[0] == 1:
                tprint(f"\tContent Size: {intfb(blk[24:24+2])}")
                tprint(f"\tData isNull?: {sum(blk[24+2:]) == 0}")
            
            elif blk[0] == 2:
                tprint(f"\tPrevious SuperBlock: {intfb(blk[24:24+8])}")
                tprint(f"\tForward SuperBlock: {intfb(blk[24+8:24+16])}")
                tprint("\tSuperblock Pointers:")
                for x in range(984//8):
                    tprint(f"\t\t- {intfb(blk[24+16+x*8: 24+16+x*8+8])}")
            
            elif blk[0] == 3:
                tprint("\tPermissions:")
                perms = intfb(blk[24:24+2])
                anyone = perms & 0b111
                group = (perms >> 3) & 0b111
                owner = (perms >> 6) & 0b111
                tprint(f"\t\tEveryone: {'r' if anyone&0b100 else '-'}{'w' if anyone&0b10 else '-'}{'x' if anyone&0b1 else '-'}")
                tprint(f"\t\tGroup: {'r' if group&0b100 else '-'}{'w' if group&0b10 else '-'}{'x' if group&0b1 else '-'}")
                tprint(f"\t\tOwner: {'r' if owner&0b100 else '-'}{'w' if owner&0b10 else '-'}{'x' if owner&0b1 else '-'}")

                tprint(f"\tNode Size: {intfb(blk[24+10:24+18])} bytes")
                nt = blk[24+18]
                tprint(f"\tNode Type: {'unknown' if nt not in [1, 2] else ('directory' if nt == 2 else 'file')}")

            elif blk[0] == 4:
                tprint(f"\tForward Pointer: {intfb(blk[24:24+8])}")
                tprint("\tEntries:")
                for x in range(992//124):
                    entry = blk[24+8+x*124:24+8+x*124+124]
                    if (intfb(entry[0:8]) == 0):
                        continue
                    tprint(f"\t\tNode Name: {entry[16:16+100].split(bytes([0]), 1)[0]}")
                    tprint(f"\t\t\t- NodeMetadata Pointer: {intfb(entry[0:8])}")
                    tprint(f"\t\t\t- SuperBlock/Dir Pointer: {intfb(entry[8:16])}")
            elif blk[0] == 5:
                tprint(f"\tConstant Identifier: {blk[24:24+4]}")
                tprint(f"\tVersion: {intfb(blk[24+4:24+6])}")
                tprint(f"\tRoot Directory: {intfb(blk[24+6:24+14])}")
                tprint(f"\tLocked: {blk[24+14] != 0}")
    ofp.seek(0)
    return ofp.read()