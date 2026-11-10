#include "fir.h"

static const short coef[FIR_T] = {-3, 7, -12, 25, -41, 66, -108, 312, 312, -108, 66, -41, 25, -12, 7, -3};

void fir(const short x[FIR_N], int y[FIR_N])
{
   for(int i = 0; i < FIR_N; i++)
   {
      int acc = 0;
      for(int t = 0; t < FIR_T; t++)
      {
         if(i - t >= 0)
            acc += coef[t] * x[i - t];
      }
      y[i] = acc;
   }
}
