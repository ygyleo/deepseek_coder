int _func0(float param_1,long param_2,int param_3)
{
  int local_20;
  int local_1c;
  local_1c = 0;
  do {
    local_20 = local_1c;
    if (param_3 <= local_1c) {
      return 0;
    }
    while (local_20 = local_20 + 1, local_20 < param_3) {
      if (ABS(*(float *)(param_2 + (long)local_1c * 4) - *(float *)(param_2 + (long)local_20 * 4)) < param_1) {
        return 1;
      }
    }
    local_1c = local_1c + 1;
  } while( true );
}