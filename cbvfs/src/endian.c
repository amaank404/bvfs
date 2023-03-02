#include "endian.h"

uint64_t store64(uint64_t a) {
    if (BYTEORDER_ENDIAN == BYTEORDER_LITTLE_ENDIAN) {
        return (uint64_t)(
            ((a&0x00000000000000ff)<<56)|
            ((a&0x000000000000ff00)<<40)|
            ((a&0x0000000000ff0000)<<24)|
            ((a&0x00000000ff000000)<<8)|
            ((a&0x000000ff00000000)>>8)|
            ((a&0x0000ff0000000000)>>24)|
            ((a&0x00ff000000000000)>>40)|
            ((a&0xff00000000000000)>>56)
        );
    } else {
        return a;
    }
}

uint32_t store32(uint32_t a) {
    if (BYTEORDER_ENDIAN == BYTEORDER_LITTLE_ENDIAN) {
        return (uint32_t)(
            ((a&0x000000ff)<<24)|
            ((a&0x0000ff00)<<8)|
            ((a&0x00ff0000)>>8)|
            ((a&0xff000000)>>24)
        );
    } else {
        return a;
    }
}

uint16_t store16(uint16_t a) {
    if (BYTEORDER_ENDIAN == BYTEORDER_LITTLE_ENDIAN) {
        return (uint16_t)(
            ((a&0x00ff)<<8)|
            ((a&0xff00)>>8)
        );
    } else {
        return a;
    }
}