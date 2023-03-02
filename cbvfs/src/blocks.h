#include "constants.h"

#include <stdint.h>

#pragma pack(push, 1)
typedef struct bvfsBlockRoot {
    uint8_t identifier[4];
    uint16_t version;
    uint64_t rootdir;
    uint8_t locked;
} bvfsBlockRoot_t;

typedef struct bvfsBlockUnknown {
    uint8_t data[1000];
} bvfsBlockUnknown_t;

typedef struct bvfsBlockSB {
    uint64_t psb;
    uint64_t fsb;
    uint64_t bp[BVFS_SB_ENTRY_COUNT];
} bvfsBlockSB_t;

typedef struct bvfsBlockData {
    uint16_t csize;
    uint8_t data[998];
} bvfsBlockData_t;

typedef struct bvfsDirEntry {
    uint64_t nmpointer;
    uint64_t dpointer;
    uint8_t name[100];
    uint8_t reserved[124-100-8-8];
} bvfsDirEntry_t;

typedef struct bvfsBlockDir {
    uint64_t fp;
    bvfsDirEntry_t entries[BVFS_DIR_ENTRY_COUNT];
} BVFSBlockDir_t;

typedef struct bvfsBlockNM {
    uint16_t perms;
    uint32_t gid;
    uint32_t uid;
    uint64_t size;
    uint8_t type;
} bvfsBlockNM_t;

typedef union bvfsBlockContent {
    bvfsBlockRoot_t rb;
    bvfsBlockData_t db;
    bvfsBlockSB_t sb;
    BVFSBlockDir_t dirb;
    bvfsBlockNM_t nm;
    bvfsBlockUnknown_t rawb;
} bvfsBlockContent_t;

typedef struct bvfsBlock {
    uint8_t blocktype;
    uint8_t reserved[23];
    bvfsBlockContent_t d;
} bvfsBlock_t;
#pragma pack(pop)

bvfsBlock_t createRootBlock(int rootdir);
bvfsBlock_t createDirectoryBlock(int fp);
bvfsBlock_t createNodeMetadataBlock(int perms, int gid, int uid, int size, int type);
bvfsBlock_t createSuperBlock(int psb, int fsb);