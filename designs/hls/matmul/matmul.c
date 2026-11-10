#include "matmul.h"

void matmul(const short a[MM_N][MM_N], const short b[MM_N][MM_N], int c[MM_N][MM_N])
{
   for(int i = 0; i < MM_N; i++)
   {
      for(int j = 0; j < MM_N; j++)
      {
         int acc = 0;
         for(int k = 0; k < MM_N; k++)
            acc += a[i][k] * b[k][j];
         c[i][j] = acc;
      }
   }
}
