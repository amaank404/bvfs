#include "constants.h"

#include <stdint.h>

#pragma pack(1)
typedef struct BVFSBlockRoot {
    uint8_t identifier[4];
    uint16_t version;
    uint64_t rootdir;
    uint8_t locked;
} BVFSBlockRoot_t;

#pragma pack(1)
typedef struct BVFSBlockUnknown {
    uint8_t data[1000];
} BVFSBlockUnknown_t;

#pragma pack(1)
typedef struct BVFSBlockSB {
    uint64_t psb;
    uint64_t fsb;
    uint64_t bp[BVFS_SB_ENTRY_COUNT];
} BVFSBlockSB_t;

#pragma pack(1)
typedef struct BVFSBlockData {
    uint16_t csize;
    uint8_t data[998];
} BVFSBlockData_t;

#pragma pack(1)
typedef struct BVFSDirEntry {
    uint64_t nmpointer;
    uint64_t dpointer;
    uint8_t name[100];
    uint8_t reserved[124-100-8-8];
} BVFSDirEntry_t;

#pragma pack(1)
typedef struct BVFSBlockDir {
    uint64_t fp;
    BVFSDirEntry_t entries[BVFS_DIR_ENTRY_COUNT];
} BVFSBlockDir_t;

#pragma pack(1)
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

#pragma pack(1)
typedef struct BVFSBlock {
    uint8_t blocktype;
    uint8_t reserved[23];
    BVFSBlockContent_t d;
} BVFSBlock_t;

BVFSBlock_t createRootBlock(int rootdir);
BVFSBlock_t createDirectoryBlock(int fp);
BVFSBlock_t createNodeMetadataBlock(int perms, int gid, int uid, int size, int type);
BVFSBlock_t createSuperBlock(int psb, int fsb);