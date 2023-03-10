
from functools import partial
from threading import Lock

# Constants
FS_VERSION = 1
BLOCK_SIZE = 1024

# Error classes definition


class BVFSError(Exception):
    """
    Super class for all BVFS Exceptions, this class is never
    raised directly by itself but its subclasses are raised to
    indicate different types of errors.
    """


class MagicError(BVFSError):
    """
    This error usually indicates a wrong file has been provided to open,
    this happens when the first four bytes of the filesystem are not 'BvFs' (ASCII)
    """


class VersionError(BVFSError):
    """
    This error occurs when the filesystem is found to be using a later
    version of BVFS and this library can not read it.
    """


class LockedError(BVFSError):
    """
    This error is raised when the requested filesystem is locked by a
    currently running process or by previous failiure of closing before
    exiting.
    """


class DirectoryNotFound(BVFSError):
    """
    Given directory does not exist and as a result this error is
    thrown
    """


class DirectoryNotEmpty(BVFSError):
    """
    This error is raised when the deletion of a directory has been requested
    but the directory is not empty.
    """


class FileAlreadyExists(BVFSError):
    """
    This error is raised when a file already exists in a situation where
    it is not supposed to exist
    """


class FileNotFound(BVFSError):
    """
    This error is raised when an attempt to open or access a file that
    does not exist is made.
    """

# Utility functions


def _fitb(d: bytes, fitsize: int = BLOCK_SIZE):
    """
    Pads or Trims the bytes to fit exactly in the given block_size
    """
    return bytearray(d.ljust(fitsize, b'\0')[:fitsize])


def _block(d: bytes, btype: int):
    """
    Converts a set of bytes to a BVFS Block. btype indicates the block type.
    You should see the specifications for more details. Afterall the specifications aren't
    that long.
    """
    data = _inttb(btype, 1)+b'\0'*23+d
    return data


_intfb = partial(int.from_bytes, byteorder='big', signed=False)
_inttb = partial(int.to_bytes, byteorder='big', signed=False)

# Internal Blocks Methods


class _Blocks:
    # Creates an empty root block with default values
    @staticmethod
    def createRootBlock(rootdir: int = 1):
        data = b"BvFs"+_inttb(FS_VERSION, 2)+_inttb(rootdir, 8)+b'\0'
        return _fitb(_block(data, 5))

    # Creates an empty directory block with default values.
    @staticmethod
    def createDirectoryBlock(forwardpointer: int = 0):
        data = _inttb(forwardpointer, 8)
        return _fitb(_block(data, 4))

    @staticmethod
    def createDirectoryEntry(nmpointer: int, sbpointer: int, name: str):
        data = _inttb(nmpointer, 8)+_inttb(sbpointer, 8) + \
            _fitb(name.encode('utf-8'), 99)+b'\0'
        return _fitb(data, 124)

    @staticmethod
    def createNodeMetadataBlock(perms: int, groupid: int, userid: int, size: int, ntype: int):
        data = _inttb(perms, 2) + _inttb(groupid, 4) + \
            _inttb(userid, 4) + _inttb(size, 8) + _inttb(ntype, 1)
        return _fitb(_block(data, 3))

    @staticmethod
    def createSuperBlock(prevblock: int, forwardblock: int):
        return _fitb(_block(_inttb(prevblock, 8)+_inttb(forwardblock, 8), 2))

    @staticmethod
    def createDataBlock(contentsize: int, content: bytes):
        return _fitb(_block(_inttb(contentsize, 2)+_fitb(content, fitsize=998), 1))

# For public use


def createFs(filename):
    """
    This function opens the filename, overwriting if exists, and creates
    a new filesystem inside it.
    """
    with open(filename, "wb") as fp:
        bfp = BlockIO(fp)  # You will see its use later
        bfp.writeblock(0, _Blocks.createRootBlock())
        bfp.writeblock(1, _Blocks.createDirectoryBlock())

# A file wrapper to prevent common errors from happening.
# This helps dividing the file into blocks which can be read
# from and written to. This should not be used for any other
# purpose and is definatly not meant to be used by the end user.


class BlockIO:
    """
    Block IO provides a way to read and write to files in terms of blocks.
    Note: This is not meant to be used and is there for internal purposes only.
    This class is liable to have breaking unannounced changes. It is thread safe.
    """

    def __init__(self, file, block_size: int = BLOCK_SIZE, cachesize: int = 100) -> None:
        self.file = file
        self.bs = block_size
        self.file.seek(0, 2)
        fsize = self.file.tell()
        if extra := (fsize % block_size) != 0:
            self.file.truncate(fsize-extra)
        self.blocklen = fsize//block_size
        self.file.seek(0)
        self.previousblocknum = 0
        self.cache = {}
        self.cacheblocks = []
        self.cachesize = cachesize
        self.lock = Lock()

    def readblock(self, blocknum: int) -> bytearray:
        if blocknum in self.cache:
            return self.cache[blocknum]

        self.lock.acquire()

        if self.previousblocknum+1 != blocknum:
            self.file.seek(self.bs*blocknum)
            self.previousblocknum = blocknum
        else:
            self.previousblocknum += 1
        data = bytearray(self.file.read(self.bs))

        self.cache[blocknum] = data
        self.cacheblocks.append(blocknum)
        if len(self.cacheblocks) > self.cachesize:
            del self.cache[self.cacheblocks.pop(0)]

        self.lock.release()
        return data

    def writeblock(self, blocknum: int, data: bytes = b'', write: bool = True) -> None:
        if blocknum == 5 and write:
            if data[0] == 0:
                breakpoint()
        if not isinstance(blocknum, int):
            raise TypeError("Block number must be an integer")
        self.lock.acquire()
        if self.previousblocknum+1 != blocknum:
            self.file.seek(self.bs*blocknum)
            self.previousblocknum = blocknum
        else:
            self.previousblocknum += 1
        if blocknum >= self.blocklen:
            self.file.truncate((blocknum+1)*self.bs)
            self.blocklen = blocknum + 1

        if write:
            pdata = _fitb(data, self.bs)
            if blocknum in self.cache:
                self.cache[blocknum] = bytearray(pdata)
            self.file.write(pdata)
        self.lock.release()

    def __len__(self) -> int:
        return self.blocklen


class BVFSFile:
    def __init__(self, parent: "BVFS", superblock: int, pardirnode: int, fname: str, nm: int) -> None:
        self.superblock = superblock
        self.pardirnode = pardirnode
        self.nm = nm
        self.cur = superblock
        self.fname = fname
        self.cursuperblock = 0
        self.curblock = 0
        self.curpos = 0
        self.cursbaddr = superblock
        self.parent = parent
        if self.superblock != 0:
            self.superblockblk = parent._blockio.readblock(superblock)
            if (fb := _intfb(self.superblockblk[24+16:24+16+8])) != 0:
                self.blockblk = parent._blockio.readblock(fb)
                self.curblkaddr = fb
            else:
                self.blockblk = bytearray(1024)
                self.curblkaddr = 0
        else:
            self.superblockblk = bytearray(1024)
            self.blockblk = bytearray(1024)
            self.curblkaddr = 0

    def write(self, data):
        if len(data) == 0:
            return
        if self._islastposition() or (wasempty := self.superblock == 0) or self.curblkaddr == 0:
            self._nextblock(True)
            if wasempty:
                dirnode = self.pardirnode
                while True:
                    blk = self.parent._blockio.readblock(dirnode)
                    fp = _intfb(blk[24:24+8])
                    for x in range(992//124):
                        entry = blk[24+8+x*124:24+8+x*124+124]
                        if _intfb(entry[:8]) == 0:
                            continue
                        else:
                            if entry[16:16+100].split(b'\0', 1)[0].decode('utf-8') == self.fname:
                                entry[8:16] = _inttb(self.superblock, 8)
                                blk[24+8+x*124:24+8+x*124+124] = entry
                                self.parent._blockio.writeblock(dirnode, blk)
                                break
                    if fp != 0:
                        dirnode = fp
                    else:
                        break
        dataidx = 0

        # Write first chunk logic
        datalentocopy = 998-self._curposinblock()
        datachunk = data[0:datalentocopy]
        self.blockblk[
            26+self._curposinblock():
            26+self._curposinblock()+len(datachunk)
        ] = datachunk

        # If this was the last block just change its length to what it is supposed to be.
        if _intfb(self.blockblk[24:26]) != 998:
            self.blockblk[24:26] = _inttb(
                self._curposinblock()+len(datachunk), 2)
            dataidx += len(datachunk)

        # Write the block itself
        self.parent._blockio.writeblock(self.curblkaddr, self.blockblk)

        restchunkswrote = False
        # Write rest of the chunks logic
        while dataidx < len(data):
            self._nextblock(True)
            datachunk = data[dataidx:dataidx+998]
            dataidx += 998
            self.blockblk[26:1024] = datachunk
            self.blockblk[24:26] = _inttb(998, 2)
            self.parent._blockio.writeblock(self.curblkaddr, self.blockblk)
            restchunkswrote = True

        if restchunkswrote:
            self.blockblk[24:26] = _inttb(len(datachunk), 2)
            self.parent._blockio.writeblock(self.curblkaddr, self.blockblk)

    def _curposinblock(self):
        return self.curpos % 998

    def _islastposition(self):
        return self.curpos % 998 == 0 and self.curpos != 0

    def _islastblock(self):
        return self.curblock % 122 == 0 and self.curblock != 0

    def _nextblock(self, create: bool = False) -> bool:
        if not create and self.curblock == 122:
            pass
        if self._islastblock() or self.cursbaddr == 0:
            if not self._nextsuperblock(create):
                return False
            self.curblock = -1
        self.curblock += 1
        blockid = _intfb(
            self.superblockblk[24+16+self.curblock*8:24+16+self.curblock*8+8])
        if blockid == 0:
            if create:
                db = _Blocks.createDataBlock(0, b"")
                dbp = self.parent._allocate()
                self.parent._blockio.writeblock(dbp, db)
                self.superblockblk[24+16+self.curblock *
                                   8:24+16+self.curblock*8+8] = _inttb(dbp, 8)
                self.parent._blockio.writeblock(
                    self.cursbaddr, self.superblockblk)
                self.curblkaddr = dbp
                self.blockblk = db
            else:
                return False
        else:
            self.blockblk = self.parent._blockio.readblock(blockid)
        self.curpos %= 998
        return True

    def _nextsuperblock(self, create: bool = False) -> bool:
        forwardpointer = _intfb(self.superblockblk[24+8:24+16])
        if forwardpointer == 0 or self.curblkaddr == 0:
            if create:
                sbdata = _Blocks.createSuperBlock(self.cursbaddr, 0)
                sb = self.parent._allocate()
                self.parent._blockio.writeblock(sb, sbdata)
                if self.cursbaddr != 0:
                    self.superblockblk[24+8:24+16] = _inttb(sb, 8)
                    self.parent._blockio.writeblock(
                        self.cursbaddr, self.superblockblk)
                else:
                    self.superblock = sb
                self.cursbaddr = sb
                self.cursuperblock += 1
                self.superblockblk = sbdata
                return True
            else:
                return False
        else:
            self.superblockblk = self.parent._blockio.readblock(forwardpointer)
            self.cursbaddr = forwardpointer
            self.cursuperblock += 1
        return True
    
    def read(self, numbytes: int = None):
        if self.cursbaddr == 0 or self.curblkaddr == 0:
            return b''
        if numbytes is not None:
            bleft = numbytes
        else:
            bleft = 0
        data = bytearray()

        while bleft > 0 or numbytes is None:
            if self._islastposition():
                if not self._nextblock():
                    return bytes(data)
            binblk = _intfb(self.blockblk[24:26])
            chunk = self.blockblk[26+self._curposinblock():26+binblk]
            if numbytes is not None:
                data += chunk[:bleft]
            else:
                data += chunk
            bleft -= len(chunk)
            self.curpos += len(chunk)
            if len(chunk) == 0:  # Chunk ended
                return bytes(data)

        return bytes(data)

    def seek(self, pos: int, whence: int = 0):
        if whence == 0:
            pos//BLOCK_SIZE
            cur  # TODO: Complete this
        elif whence == 1:
            self  # TODO: Complete this
        else:
            raise ValueError("Whence is not in 0, 1, 2")


# The Standard BVFS class to perform all the IO operations
class BVFS:
    """
    BVFS class allows you to open a file by its name and interract
    with its underlying filesystem. Cache limit can be set to set
    the amount of blocks it should cache. This is also thread safe.
    """

    def __init__(self, filename: str, cachelimit: int = 1000) -> None:
        self._fp = open(filename, 'r+b')
        self._blockio = BlockIO(self._fp, cachesize=cachelimit)
        # This variable is used to keep the track of the first free block contrary to its name.
        self._lastfreeblock = 0

        block = self._blockio.readblock(0)  # Read the root block

        # Check for magic header
        if block[24:28] != b"BvFs":
            raise MagicError(
                f"Not a BvFs, magic header invalid: {block[24:28]}")
        # Check for file system version
        if (ver := _intfb(block[28:30])) > FS_VERSION:
            raise VersionError(
                f"Current library supports bvfs upto version {FS_VERSION} but the file being read is at version {ver}.")
        # Check for locked flag
        if block[38] != 0:
            raise LockedError(
                "Current file system is locked please run a full recovery on the filesystem to access it")

        # Read the pointer to root directory node
        self._rootdir = _intfb(block[30:38])
        block[38] = 255  # Set the locked flag
        self._blockio.writeblock(0, block)   # Write the lock back

    def _allocate(self) -> int:
        while True:
            if self._lastfreeblock >= len(self._blockio):
                self._blockio.writeblock(self._lastfreeblock, write=False)
                block = b'\0'
            else:
                block = self._blockio.readblock(self._lastfreeblock)

            if block[0] == 0:
                self._lastfreeblock += 1
                return self._lastfreeblock - 1
            self._lastfreeblock += 1

    def _deallocate(self, blocknum: int) -> None:
        self._blockio.writeblock(blocknum, b'')
        self._lastfreeblock = min(self._lastfreeblock, blocknum)

    def _writedirectorynode(self, blockint: int, nm: int, sb: int, name: str):
        block = self._blockio.readblock(blockint)
        bint = blockint
        offset = 0
        entry = _Blocks.createDirectoryEntry(nm, sb, name)
        while True:
            centry = block[24+8+offset:24+8+offset+124]
            if _intfb(centry[0:8]) == 0:
                block[24+8+offset:24+8+offset+124] = entry
                self._blockio.writeblock(bint, block)
                return
            offset += 124
            if offset == 124*8:
                if (fp := _intfb(block[24:24+8])) == 0:
                    # We have reached the end of this entry, need to allocate new block
                    bint2 = self._allocate()
                    block[24:24+8] = bint2.to_bytes(8, 'big')
                    self._blockio.writeblock(bint, block)
                    bint = bint2
                    block = bytearray(_Blocks.createDirectoryBlock())
                    offset = 0
                else:
                    bint = fp
                    block = self._blockio.readblock(fp)
                    offset = 0

    def _createnodemetadata(self, ntype: int, permissions: int = 0, groupid: int = 0, userid: int = 0, fsize: int = 0) -> int:
        block = _Blocks.createNodeMetadataBlock(
            permissions, groupid, userid, fsize, ntype)
        bint = self._allocate()
        self._blockio.writeblock(bint, block)
        return bint

    def _opendirectory(self, dirname: str) -> int:
        dn = dirname.split("/")
        cnode = self._rootdir
        for x in dn[1:]:
            if len(x) == 0:
                continue
            block = self._blockio.readblock(cnode)
            offset = 0
            while True:
                if (nm := _intfb(block[24+8+offset:24+8+offset+8])) != 0:
                    fname = block[24+8+offset+16:24+8+offset +
                                  16+100].split(b'\0', 1)[0].decode('utf-8')
                    if fname == x:
                        nmblock = self._blockio.readblock(nm)
                        if nmblock[24+18] == 2:
                            cnode = _intfb(block[24+8+offset+8:24+8+offset+16])
                            break
                        else:
                            raise DirectoryNotFound("Given path is a file")
                offset += 124
                if offset == 124*8:
                    if (fp := _intfb(block[24:24+8])) != 0:
                        cnode = fp
                        block = self._blockio.readblock(cnode)
                        offset = 0
                        continue
                    else:
                        raise DirectoryNotFound("Given Path does not exist")
        return cnode

    def _purge_empty_directory_blocks(self, dirnum: int):
        preventry = 0
        prevblk = b''
        dirnode = dirnum
        while True:
            blk = self._blockio.readblock(dirnode)
            fp = _intfb(blk[24:24+8])
            totalentries = 0
            for x in range(992//124):
                entry = blk[24+8+x*124:24+8+x*124+124]
                if _intfb(entry[:8]) == 0:
                    continue
                else:
                    totalentries += 1
                    break
            if totalentries == 0 and not dirnode == dirnum:
                prevblk[24:24+8] = blk[24:24+8]
                self._blockio.writeblock(preventry, prevblk)
                self._deallocate(dirnode)
            if fp != 0:
                prevblk = blk
                preventry = dirnode
                dirnode = fp
            else:
                break

    def mkdir(self, dirname: str):
        """
        Create a directory with the given dirname the dirname
        is split by forward slash
        """
        pdir, cdir = dirname.rsplit("/", 1)
        pdirnode = self._opendirectory(pdir)
        nm = self._createnodemetadata(2)
        dirp = self._allocate()
        self._blockio.writeblock(dirp, _Blocks.createDirectoryBlock())
        self._writedirectorynode(pdirnode, nm, dirp, cdir)

    def exists(self, nodename: str) -> bool:
        """
        Checks if a path exists
        """
        pdirnode, fname2 = nodename.rsplit("/", 1)
        dirnode = self._opendirectory(pdirnode)
        while True:
            blk = self._blockio.readblock(dirnode)
            fp = _intfb(blk[24:24+8])
            for x in range(992//124):
                entry = blk[24+8+x*124:24+8+x*124+124]
                if _intfb(entry[:8]) == 0:
                    continue
                elif entry[16:16+100].split(b'\0', 1)[0].decode('utf-8') == fname2:
                    return True
            if fp != 0:
                dirnode = fp
            else:
                break
        return False

    def lsdir(self, dirname: str):
        """
        Lists a directory
        """
        dirnode = self._opendirectory(dirname)
        ls = []
        while True:
            blk = self._blockio.readblock(dirnode)
            fp = _intfb(blk[24:24+8])
            for x in range(992//124):
                entry = blk[24+8+x*124:24+8+x*124+124]
                if _intfb(entry[:8]) == 0:
                    continue
                else:
                    ls.append(entry[16:16+100].split(b'\0', 1)
                              [0].decode('utf-8'))
            if fp != 0:
                dirnode = fp
            else:
                break
        return ls

    def rmdir(self, dirname: str):
        """
        Deletes a directory, Only works on empty directories
        """

        pdirnode = dirnode = self._opendirectory(dirname)
        while True:
            blk = self._blockio.readblock(dirnode)
            fp = _intfb(blk[24:24+8])
            for x in range(992//124):
                entry = blk[24+8+x*124:24+8+x*124+124]
                if _intfb(entry[:8]) == 0:
                    continue
                else:
                    raise DirectoryNotEmpty(
                        "Attempt to remove a directory that is not empty.")
            if fp != 0:
                dirnode = fp
            else:
                break

        # Code to actually remove the directory
        dirnode = pdirnode
        while True:
            blk = self._blockio.readblock(dirnode)
            fp = _intfb(blk[24:24+8])
            self._deallocate(dirnode)
            if fp != 0:
                dirnode = fp
            else:
                break

        # Code to remove directory entry from parent
        parentdir = self._opendirectory(dirname.rsplit("/", 1)[0])
        fname = dirname.rsplit("/", 1)[1]
        dirnode = parentdir
        rmpentry = True
        while rmpentry:
            blk = self._blockio.readblock(dirnode)
            fp = _intfb(blk[24:24+8])
            for x in range(992//124):
                entry = blk[24+8+x*124:24+8+x*124+124]
                if _intfb(entry[:8]) == 0:
                    continue
                else:
                    if entry[16:16+100].split(b'\0', 1)[0].decode('utf-8') == fname:
                        nmpointer = _intfb(entry[:8])
                        self._deallocate(nmpointer)
                        blk[24+8+x*124:24+8+x*124+124] = bytearray(124)
                        self._blockio.writeblock(dirnode, blk)
                        rmpentry = False
                        break
            if fp != 0:
                dirnode = fp
            else:
                break

        # Purge Empty directory nodes in the parent directory
        self._purge_empty_directory_blocks(parentdir)

    def open(self, filename: str, mode: str):
        """
        Classic python like open function for opening a pythonic file api based object.
        """
        if self.exists(filename):
            if 'x' in mode:
                raise FileAlreadyExists(
                    "Can not create the file in exclusive mode as the file already exists")
            elif 'w' in mode:
                self.rmfile(filename)
        else:
            if 'r' in mode or '+' in mode or 'a' in mode:
                raise FileNotFound()

        if 'w' in mode or 'x' in mode:
            pdir, fname = filename.rsplit("/", 1)
            nm = self._createnodemetadata(1)
            sb = 0
            pdirnode = self._opendirectory(pdir)
            self._writedirectorynode(pdirnode, nm, sb, fname)
            return BVFSFile(self, 0, pdirnode, fname, nm)
        elif 'r' in mode or 'a' in mode:
            pdir, fname = filename.rsplit("/", 1)
            pdirnode = self._opendirectory(pdir)
            while True:
                blk = self._blockio.readblock(pdirnode)
                for x in range(992//124):
                    entry = blk[24+8+x*124:24+8+x*124+124]
                    if (nmnum := _intfb(entry[:8])) != 0:
                        if entry[16:16+100].split(b'\0', 1)[0].decode('utf-8') == fname:
                            nmblk = self._blockio.readblock(nmnum)
                            if nmblk[24+18] != 1:
                                raise FileNotFound(
                                    "Provided path exists but is not a file")
                            else:
                                return BVFSFile(self, _intfb(entry[8:16]), pdirnode, fname, nmnum)
                if (fp := _intfb(blk[24:24+8])) != 0:
                    pdirnode = fp
                else:
                    raise FileNotFound("File does not exist")

    def rmfile(self, filename: str):
        """
        Removes a file, if the file is not found an error is raised
        """
        # TODO: Write this function

    def close(self):
        block = self._blockio.readblock(0)
        block[38] = 0  # unset the locked flag
        self._blockio.writeblock(0, block)   # Write the lock back
        del self._blockio
        self._fp.close()
        del self._fp
