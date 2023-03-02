#include "blocks.h"

bvfsBlock_t createRootBlock(int rootdir) {
    bvfsBlock_t data;
    data.blocktype = BVFS_BROOT;
    data.d.rb.identifier[0] = 'B';
    data.d.rb.identifier[1] = 'v';
    data.d.rb.identifier[2] = 'F';
    data.d.rb.identifier[3] = 's';

    data.d.rb.locked = 0;
    data.d.rb.version = BVFS_VERSION;
    data.d.rb.rootdir = rootdir;
    return data;
}

bvfsBlock_t createDirectoryBlock(int fp) {
    bvfsBlock_t data;
    data.blocktype = BVFS_BDIRECTORY;
    data.d.dirb.fp = fp;
    for (int i = 0; i < BVFS_DIR_ENTRY_COUNT; i++) {
        data.d.dirb.entries[i].nmpointer = 0;
    }
    return data;
}

bvfsBlock_t createNodeMetadataBlock(int perms, int gid, int uid, int size, int type) {
    bvfsBlock_t data;
    data.blocktype = BVFS_BNODEMETADATA;
    data.d.nm.perms = perms;
    data.d.nm.gid = gid;
    data.d.nm.uid = uid;
    data.d.nm.type = type;
    data.d.nm.size = size;
    return data;
}

bvfsBlock_t createSuperBlock(int psb, int fsb) {
    bvfsBlock_t data;
    data.blocktype = BVFS_BSUPERBLOCK;
    data.d.sb.psb = psb;
    data.d.sb.fsb = fsb;
    return data;
}