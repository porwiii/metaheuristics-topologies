#!/bin/bash

island_counts=(250)
migrant_counts=(5)
migrant_intervals=(5)

# z_star_values=(4 5 6 8)
# n_steps_values=(500 1000)
# npr0_values=(20)
# nmr1_values=(400)
# ne_gamma_values=(1 2)

z_star_values=(6 10 15 20)
n_steps_values=(500 1000)
npr0_values=(10 20)
nmr1_values=(25 50)
ne_gamma_values=(3 5)

> ./params.txt

for island_count in "${island_counts[@]}"; do
  for migrant_count in "${migrant_counts[@]}"; do
    for migrant_interval in "${migrant_intervals[@]}"; do
      for z_star in "${z_star_values[@]}"; do
        for n_steps in "${n_steps_values[@]}"; do
          for npr0 in "${npr0_values[@]}"; do
            for nmr1 in "${nmr1_values[@]}"; do
              for ne_gamma in "${ne_gamma_values[@]}"; do
                echo "$island_count $migrant_count $migrant_interval 0 0 $z_star $n_steps $npr0 $nmr1 $ne_gamma" >> ./params.txt
              done
            done
          done
        done
      done
    done
  done
done