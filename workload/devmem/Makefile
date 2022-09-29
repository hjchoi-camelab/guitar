CROSSCOMPILE ?= aarch64-none-linux-gnu-
CC = $(CROSSCOMPILE)gcc
LD = $(CROSSCOMPILE)ld
OBJCOPY = $(CROSSCOMPILE)objcopy
OBJDUMP = $(CROSSCOMPILE)objdump

CXXFLAGS = \
	-O2 \
	-Wall \
	-static

OBJS = \
	devmem.o 

.PHONY: all clean

all: devmem

devmem: $(OBJS)
	$(CC) -o devmem $(OBJS)

%.o: %.c
	$(CC) $(CCFLAGS) $^ -c -o $@

clean:
	rm -f $(OBJS) devmem
