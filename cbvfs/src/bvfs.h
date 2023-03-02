typedef struct BVFS
{
    FILE* fp;
    int lastfreeblock;
    int rootdir;
} BVFS_t;


int createFs(char* fname);
char* geterror();