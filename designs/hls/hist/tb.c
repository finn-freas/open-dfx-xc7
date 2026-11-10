#include <stdio.h>
#include "hist.h"

int main(void)
{
   unsigned char in[HIST_N];
   unsigned int bins[HIST_B], ref[HIST_B];
   unsigned int s = 4242u;
   for(int i = 0; i < HIST_N; i++)
   {
      s = s * 1103515245u + 12345u;
      in[i] = (unsigned char)(s >> 20);
   }
   for(int b = 0; b < HIST_B; b++)
   {
      ref[b] = 0;
      bins[b] = 0xdeadbeefu;
   }
   for(int i = 0; i < HIST_N; i++)
      ref[in[i] % HIST_B] += 1;
   hist(in, bins);
   int errors = 0;
   for(int b = 0; b < HIST_B; b++)
      if(bins[b] != ref[b])
         errors++;
   printf("hist: %d errors\n", errors);
   return errors;
}
