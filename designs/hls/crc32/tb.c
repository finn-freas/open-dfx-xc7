#include <stdio.h>
#include "crc32.h"

int main(void)
{
   unsigned char d[CRC_N];
   for(int i = 0; i < CRC_N; i++)
      d[i] = (unsigned char)(i * 7 + 3);
   unsigned int r = 0xffffffffu;
   for(int i = 0; i < CRC_N; i++)
   {
      r ^= d[i];
      for(int b = 0; b < 8; b++)
         r = (r & 1u) ? (r >> 1) ^ 0xedb88320u : r >> 1;
   }
   r = ~r;
   unsigned int got = crc32(d);
   int errors = got != r;
   printf("crc32: %08x expected %08x, %d errors\n", got, r, errors);
   return errors;
}
