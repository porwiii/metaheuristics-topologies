#!/bin/bash

island_counts=(25 50 100 200 500)
migrant_counts=(5)
migrant_intervals=(5)
m0_values=(1 2 3 5 10)

len1=${#island_counts[@]}
len2=${#migrant_counts[@]}
len3=${#migrant_intervals[@]}
len4=${#m0_values[@]}

total_len=$((len1 * len2 * len3 * len4))

> ./params.txt

for ((i=0; i<total_len; i++)); do
  island_count=${island_counts[i / (len2 * len3 * len4) % len1]}
  migrant_count=${migrant_counts[i / (len3 * len4) % len2]}
  migrant_interval=${migrant_intervals[i / len4 % len3]}
  m0=${m0_values[i % len4]}

  for ((m=1; m<=m0; m++)); do
    echo "$island_count $migrant_count $migrant_interval $m0 $m" >> ./params.txt
  done
done
