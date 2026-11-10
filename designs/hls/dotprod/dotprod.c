#include "dotprod.h"

int dotprod(const short a[DOT_N], const short b[DOT_N])
{
   int acc = 0;
   for(int i = 0; i < DOT_N; i++)
      acc += a[i] * b[i];
   return acc;
}
