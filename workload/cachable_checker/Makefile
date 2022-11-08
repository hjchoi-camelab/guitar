GEM5_PATH=/root/git/anns/jh

CROSSCOMPILE ?= aarch64-none-linux-gnu-
CXX = $(CROSSCOMPILE)g++
LD = $(CROSSCOMPILE)ld
OBJCOPY = $(CROSSCOMPILE)objcopy
OBJDUMP = $(CROSSCOMPILE)objdump

CXXFLAGS = \
	-O2 \
	-Wall \
	-static \
	-I$(GEM5_PATH)/include

LDFLAGS = \
	-L$(GEM5_PATH)/util/m5/build/arm64/out -lm5


OBJS = \
	cachable_checker.o

.PHONY: all clean

all: cachable_checker

cachable_checker: $(OBJS)
	$(CXX) -o cachable_checker $(OBJS) $(CXXFLAGS) $(LDFLAGS)

%.o: %.c
	$(CXX) $^ -c -o $@ $(CXXFLAGS) $(LDFLAGS)

clean:
	rm -f $(OBJS) cachable_checker
