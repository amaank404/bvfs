#include "bvfs.h"
#include "constants.h"
#include "blocks.h"
#include "endian.h"

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

int bvfssystemerrorcode = 0;
char* bvfserror;

inline int writeerror(const char* string) {
    int length = strlen(string);
    bvfserror = malloc(length+1);
    strcpy(bvfserror, string);
}

char* geterror() {
    return bvfserror;
}

BVFSBlock_t cvtblock(BVFSBlock_t data) {
    if (data.blocktype == BVFS_BDATA) {
        data.d.db.csize = store16(data.d.db.csize);
    } else if (data.blocktype == BVFS_BSUPERBLOCK) {
        data.d.sb.fsb = store64(data.d.sb.fsb);
        data.d.sb.psb = store64(data.d.sb.psb);
        for (int i = 0; i < BVFS_SB_ENTRY_COUNT; i++) {
            data.d.sb.bp[i] = store64(data.d.sb.bp[i]);
        }
    } else if (data.blocktype == BVFS_BNODEMETADATA) {
        data.d.nm.perms = store16(data.d.nm.perms);
        data.d.nm.gid = store32(data.d.nm.gid);
        data.d.nm.uid = store32(data.d.nm.uid);
        data.d.nm.size = store64(data.d.nm.size);
    } else if (data.blocktype == BVFS_BDIRECTORY) {
        data.d.dirb.fp = store64(data.d.dirb.fp);
        for (int i = 0; i < BVFS_DIR_ENTRY_COUNT; i++) {
            data.d.dirb.entries[i].nmpointer = store64(data.d.dirb.entries[i].nmpointer);
            data.d.dirb.entries[i].dpointer = store64(data.d.dirb.entries[i].dpointer);
        }
    } else if (data.blocktype == BVFS_BROOT) {
        data.d.rb.version = store16(data.d.rb.version);
        data.d.rb.rootdir = store64(data.d.rb.rootdir);
    }
    return data;
}

void blockwrite(int b, BVFSBlock_t *data, FILE* fp) {
    BVFSBlock_t blk = *data;
    blk = cvtblock(blk);
    fseek(fp, b*BVFS_BLOCK_SIZE, SEEK_SET);
    fwrite(&blk, BVFS_BLOCK_SIZE, 1, fp);
}

BVFSBlock_t blockread(int b, FILE* fp) {
    BVFSBlock_t data;
    fseek(fp, b*BVFS_BLOCK_SIZE, SEEK_SET);
    fread(&data, BVFS_BLOCK_SIZE, 1, fp);
    return data;
}

int createFs(char* fname) {
    FILE* fp = fopen(fname, "wb");
    if (fp == NULL) {
        writeerror("Unable to open the file, OS based error");
        return BVFS_ERR;
    }

    BVFSBlock_t blk = createRootBlock(1);
    blockwrite(0, &blk, fp);
    blk = createDirectoryBlock(0);
    blockwrite(1, &blk, fp);
    
    fclose(fp);
    fp = NULL;
}