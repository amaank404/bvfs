#include <stdint.h>

// Status
#define BVFS_OK 0
#define BVFS_ERR 1

// Others
#define BVFS_BLOCK_SIZE 1024
#define BVFS_SB_ENTRY_COUNT (984/sizeof(uint64_t))
#define BVFS_DIR_ENTRY_COUNT (992/124)
#define BVFS_VERSION 1

// Block types
#define BVFS_BROOT 5
#define BVFS_BUNKNOWN 0
#define BVFS_BSUPERBLOCK 2
#define BVFS_BNODEMETADATA 3
#define BVFS_BDATA 1
#define BVFS_BDIRECTORY 4
