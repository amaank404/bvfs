cmake_minimum_required (VERSION 3.10)

set(CMAKE_C_COMPILER "gcc")
set(CMAKE_CXX_COMPILER "g++")

include_directories(
	src
)


project (BVFS)

set (HELLO_SRCS src/blocks.c src/bvfs.c src/endian.c)

add_executable (bvfsmain src/main.c ${HELLO_SRCS})