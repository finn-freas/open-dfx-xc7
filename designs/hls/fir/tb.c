#include <stdio.h>
#include "fir.h"

static const short ref_coef[FIR_T] = {-3, 7, -12, 25, -41, 66, -108, 312, 312, -108, 66, -41, 25, -12, 7, -3};

int main(void)
{
   short x[FIR_N];
   int y[FIR_N];
   unsigned int s = 12345u;
   for(int i = 0; i < FIR_N; i++)
   {
      s = s * 1103515245u + 12345u;
      x[i] = (short)((s >> 16) & 0xffff);
   }
   fir(x, y);
   int errors = 0;
   for(int i = 0; i < FIR_N; i++)
   {
      int r = 0;
      for(int t = 0; t <= i && t < FIR_T; t++)
         r += ref_coef[t] * x[i - t];
      if(r != y[i])
         errors++;
   }
   printf("fir: %d errors\n", errors);
   return errors;
}
