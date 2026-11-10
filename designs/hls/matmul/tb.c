#include <stdio.h>
#include "matmul.h"

int main(void)
{
   short a[MM_N][MM_N], b[MM_N][MM_N];
   int c[MM_N][MM_N];
   unsigned int s = 777u;
   for(int i = 0; i < MM_N; i++)
      for(int j = 0; j < MM_N; j++)
      {
         s = s * 1103515245u + 12345u;
         a[i][j] = (short)(((s >> 16) & 0xfff) - 2048);
         s = s * 1103515245u + 12345u;
         b[i][j] = (short)(((s >> 16) & 0xfff) - 2048);
      }
   matmul(a, b, c);
   int errors = 0;
   for(int i = 0; i < MM_N; i++)
      for(int j = 0; j < MM_N; j++)
      {
         int r = 0;
         for(int k = 0; k < MM_N; k++)
            r += a[i][k] * b[k][j];
         if(r != c[i][j])
            errors++;
      }
   printf("matmul: %d errors\n", errors);
   return errors;
}
