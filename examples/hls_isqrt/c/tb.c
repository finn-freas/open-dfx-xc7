#include <stdio.h>
#include "isqrt.h"

int main(void)
{
   static const unsigned int v[] = {0u, 1u, 2u, 3u, 4u, 15u, 16u, 17u, 99u, 100u, 65535u, 65536u, 1000000u,
                                    2147483647u, 4294967295u, 4294836225u, 4294836224u, 123456789u};
   int errors = 0;
   for(unsigned int i = 0; i < sizeof(v) / sizeof(v[0]); i++)
   {
      unsigned int r = isqrt(v[i]);
      unsigned long long lo = (unsigned long long)r * r;
      unsigned long long hi = (unsigned long long)(r + 1) * (r + 1);
      if(!(lo <= v[i] && v[i] < hi))
      {
         printf("isqrt(%u) = %u wrong\n", v[i], r);
         errors++;
      }
   }
   printf("isqrt: %d errors\n", errors);
   return errors;
}
