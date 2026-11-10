#include "crc32.h"

unsigned int crc32(const unsigned char data[CRC_N])
{
   unsigned int crc = 0xffffffffu;
   for(int i = 0; i < CRC_N; i++)
   {
      crc ^= data[i];
      for(int b = 0; b < 8; b++)
         crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
   }
   return ~crc;
}
