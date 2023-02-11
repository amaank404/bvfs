from . import core

def removeTruncatingBlocks(fp):
    bio = core.BlockIO(fp)
    for x in range(bio.blocklen-1, -1, -1):
        if bio.readblock(x)[0] == 0:
            bio.blocklen -= 1
            fp.truncate(bio.blocklen*bio.bs)
        else:
            break
    fp.seek(0)
    return
