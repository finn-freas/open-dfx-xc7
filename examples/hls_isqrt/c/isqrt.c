#include "isqrt.h"

unsigned int isqrt(unsigned int x)
{
   unsigned int r = 0;
   unsigned int bit = 1u << 30;
   for(int i = 0; i < 16; i++)
   {
      if(x >= r + bit)
      {
         x -= r + bit;
         r = (r >> 1) + bit;
      }
      else
         r >>= 1;
      bit >>= 2;
   }
   return r;
}
