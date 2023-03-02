typedef struct bvfs
{
    FILE* fp;
    int lastfreeblock;
    int rootdir;
    int blocklen;
} bvfs_t;


int createFs(char* fname);
char* geterror();