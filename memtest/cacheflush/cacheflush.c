#define _mm_clflushopt(addr)\
	asm volatile(".byte 0x66; clflush %0" :\
	"+m" (*(volatile char *)(addr)));

#define _mm_clwb(addr)\
	asm volatile(".byte 0x66; xsaveopt %0" :\
	"+m" (*(volatile char *)(addr)));

static char Buf[32];

int
main(int argc, char *argv[])
{
	_mm_clflushopt(Buf);
    _mm_clwb(Buf);

    return 0;
}