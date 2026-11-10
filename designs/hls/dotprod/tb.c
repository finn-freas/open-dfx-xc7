#include <stdio.h>
#include "dotprod.h"

int main(void)
{
   short a[DOT_N], b[DOT_N];
   unsigned int s = 99u;
   for(int i = 0; i < DOT_N; i++)
   {
      s = s * 1103515245u + 12345u;
      a[i] = (short)(((s >> 16) & 0xfff) - 2048);
      s = s * 1103515245u + 12345u;
      b[i] = (short)(((s >> 16) & 0xfff) - 2048);
   }
   int r = 0;
   for(int i = 0; i < DOT_N; i++)
      r += a[i] * b[i];
   int got = dotprod(a, b);
   int errors = got != r;
   printf("dotprod: %d expected %d, %d errors\n", got, r, errors);
   return errors;
}
