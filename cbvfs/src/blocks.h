#include "constants.h"

#include <stdint.h>

#pragma pack(push, 1)
typedef struct BVFSBlockRoot {
    uint8_t identifier[4];
    uint16_t version;
    uint64_t rootdir;
    uint8_t locked;
} BVFSBlockRoot_t;

typedef struct BVFSBlockUnknown {
    uint8_t data[1000];
} BVFSBlockUnknown_t;

typedef struct BVFSBlockSB {
    uint64_t psb;
    uint64_t fsb;
    uint64_t bp[BVFS_SB_ENTRY_COUNT];
} BVFSBlockSB_t;

typedef struct BVFSBlockData {
    uint16_t csize;
    uint8_t data[998];
} BVFSBlockData_t;

typedef struct BVFSDirEntry {
    uint64_t nmpointer;
    uint64_t dpointer;
    uint8_t name[100];
    uint8_t reserved[124-100-8-8];
} BVFSDirEntry_t;

typedef struct BVFSBlockDir {
    uint64_t fp;
    BVFSDirEntry_t entries[BVFS_DIR_ENTRY_COUNT];
} BVFSBlockDir_t;

typedef struct BVFSBlockNM {
    uint16_t perms;
    uint32_t gid;
    uint32_t uid;
    uint64_t size;
    uint8_t type;
} BVFSBlockNM_t;

typedef union BVFSBlockContent {
    BVFSBlockRoot_t rb;
    BVFSBlockData_t db;
    BVFSBlockSB_t sb;
    BVFSBlockDir_t dirb;
    BVFSBlockNM_t nm;
    BVFSBlockUnknown_t rawb;
} BVFSBlockContent_t;

typedef struct BVFSBlock {
    uint8_t blocktype;
    uint8_t reserved[23];
    BVFSBlockContent_t d;
} BVFSBlock_t;
#pragma pack(pop)

BVFSBlock_t createRootBlock(int rootdir);
BVFSBlock_t createDirectoryBlock(int fp);
BVFSBlock_t createNodeMetadataBlock(int perms, int gid, int uid, int size, int type);
BVFSBlock_t createSuperBlock(int psb, int fsb);