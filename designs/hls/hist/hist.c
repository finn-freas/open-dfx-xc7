#include "hist.h"

void hist(const unsigned char in[HIST_N], unsigned int bins[HIST_B])
{
   for(int b = 0; b < HIST_B; b++)
      bins[b] = 0;
   for(int i = 0; i < HIST_N; i++)
      bins[in[i] & (HIST_B - 1)]++;
}
