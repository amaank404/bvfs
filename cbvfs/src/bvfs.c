#include "bvfs.h"
#include "constants.h"
#include "blocks.h"
#include "endian.h"

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

int bvfssystemerrorcode = 0;
char* bvfserror = NULL;

static inline void writeerror(const char* string) {
    size_t length = strlen(string);
    if (bvfserror != NULL) {
        free(bvfserror);
    }
    bvfserror = malloc(length+1);
    strcpy_s(bvfserror, length+1, string);
}

char* geterror() {
    return bvfserror;
}

static bvfsBlock_t cvtblock(bvfsBlock_t data) {
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

static void blockwrite(int b, bvfsBlock_t *data, FILE* fp) {
    bvfsBlock_t blk = *data;
    blk = cvtblock(blk);
    fseek(fp, b*BVFS_BLOCK_SIZE, SEEK_SET);
    fwrite(&blk, BVFS_BLOCK_SIZE, 1, fp);
}

static bvfsBlock_t blockread(int b, FILE* fp) {
    bvfsBlock_t data;
    fseek(fp, b*BVFS_BLOCK_SIZE, SEEK_SET);
    fread(&data, BVFS_BLOCK_SIZE, 1, fp);
    data = cvtblock(data);
    return data;
}

int createFs(char* fname) {
    FILE* fp;
    fopen_s(&fp, fname, "wb");
    if (fp == NULL) {
        writeerror("Unable to open the file, OS based error");
        return BVFS_ERR;
    }

    bvfsBlock_t blk = createRootBlock(1);
    blockwrite(0, &blk, fp);
    blk = createDirectoryBlock(0);
    blockwrite(1, &blk, fp);
    
    fclose(fp);
    return BVFS_OK;
}

int bvfsOpen(bvfs_t* bvfs, char* fname) {
    FILE* fp;
    fopen_s(fp, fname, "rb+");
    if (fp == NULL) {
        writeerror("Unable to open file");
        return BVFS_ERR;
    }

    bvfsBlock_t blk = blockread(0, fp);
    if (blk.blocktype != BVFS_BROOT) {
        writeerror("Unknown block type, NOT A ROOT BLOCK");
        return BVFS_ERR;
    } else if (blk.d.rb.identifier[0] != 'B' ||
               blk.d.rb.identifier[1] != 'v' ||
               blk.d.rb.identifier[2] != 'F' ||
               blk.d.rb.identifier[3] != 's') {
        writeerror("Unknown root identifier, NOT 'BvFs'");
        return BVFS_ERR;
    } else if (blk.d.rb.version > BVFS_VERSION) {
        writeerror("The filesystem version is greater than " BVFS_VERSION_STR "which is not supported by this library.");
        return BVFS_ERR;
    } else if (blk.d.rb.locked != 0) {
        writeerror("The filesystem is locked");
        return BVFS_ERR;
    }

    bvfs->fp = fp;
    bvfs->lastfreeblock = 0;
    bvfs->rootdir = blk.d.rb.rootdir;
    
    fseek(fp, 0, SEEK_END);
    bvfs->blocklen = ftell(fp)/BVFS_BLOCK_SIZE;
    fseek(fp, 0, SEEK_SET);

    blk.d.rb.locked = 0xff;
    blockwrite(0, &blk, fp);
}

void bvfsClose(bvfs_t* bvfs) {
    int lockedOffset = offsetof(bvfsBlock_t, d.rb.locked);
    uint8_t data = 0;
    fseek(bvfs->fp, lockedOffset, SEEK_SET);
    fwrite(data, 1, 1, bvfs->fp);
    fclose(bvfs->fp);
    bvfs->fp = NULL;
}

int bvfsAllocate(bvfs_t* bvfs) {
    int lastblk;

    while (1) {
        if (bvfs->lastfreeblock >= bvfs->blocklen) {
            lastblk = bvfs->lastfreeblock;
            bvfs->lastfreeblock += 1;
            return lastblk;
        } else {
            fseek(bvfs->fp, BVFS_BLOCK_SIZE*bvfs->lastfreeblock, SEEK_SET);
            uint8_t buf;
            fread_s(buf, 1, 1, 1, bvfs->fp);
            if (buf == 0) {
                lastblk = bvfs->lastfreeblock;
                bvfs->lastfreeblock += 1;
                return lastblk;
            } else {
                bvfs->lastfreeblock += 1;
            }
        }
    }
}

void deallocate(bvfs_t* bvfs, int b) {
    fseek(bvfs->fp, BVFS_BLOCK_SIZE*b, SEEK_SET);
    uint8_t data = BVFS_BUNKNOWN;
    fwrite(data, 1, 1, bvfs->fp);
}