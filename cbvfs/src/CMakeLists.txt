cmake_minimum_required (VERSION 3.10)

project (BVFS)

set (HELLO_SRCS blocks.c bvfs.c endian.c)

add_executable (bvfsmain main.c ${HELLO_SRCS})