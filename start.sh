#!/bin/bash

if [[ -e ".env" ]]; then
    set -a
    source .env
    set +a
fi

if [[ -z "$SBATCH_ACCOUNT" && -z $1 ]]; then
    echo "'SBATCH_ACCOUNT' and the first argument is not set. Please set one of them."
    exit 1
fi

is_array=0
if [[ "$1" == "array" ]]; then
    if [[ ! -f ./params.txt ]]; then
        echo "File 'params.txt' not found."
        exit 1
    fi

    is_array=1
fi

export SBATCH_PARTITION=${SBATCH_PARTITION:-plgrid}
export SBATCH_JOB_NAME=${SBATCH_JOB_NAME:-island-metaheuristics}
export SBATCH_TASKS_PER_NODE=${SBATCH_TASKS_PER_NODE:-1}
export SBATCH_CPUS_PER_TASK=${SBATCH_CPUS_PER_TASK:-48}
export SBATCH_TIME=${SBATCH_TIME:-0:10:00}
export SBATCH_MEM_PER_CPU=${SBATCH_MEM_PER_CPU:-3850MB}
export ISLAND_COUNT=${ISLAND_COUNT:-47}
export TOPOLOGY=${TOPOLOGY:-complete}
export STRATEGY=${STRATEGY:-best}
export MIGRANT_COUNT=${MIGRANT_COUNT:-5}
export MIGRATION_INTERVAL=${MIGRATION_INTERVAL:-5}

if [[ "$TOPOLOGY" == "scale_free" ]]; then
    export M0=${M0:-5}
    export M=${M:-3}
fi

if [[ "$TOPOLOGY" == "meeting" ]]; then
    export z_star=${z_star:-5}
    export n_steps=${n_steps:-500}
    export npr0=${npr0:-20}
    export nmr1=${nmr1:-400}
    export ne_gamma=${ne_gamma:-1}
    export seed=${seed:-123}
fi


if [[ -z "$SBATCH_NODES" ]]; then
    x=$(bc -l <<< "($ISLAND_COUNT * $CPU_PER_ISLAND) / $SBATCH_CPUS_PER_TASK")
    SBATCH_NODES=$(awk -v x="$x" 'BEGIN { print (x == int(x)) ? int(x) : int(x) + 1 }')
fi

if [[ $is_array == 0 ]]; then
    echo "Submitting a job with the following parameters:"
else
    echo "Submitting a job array with the following parameters:"
fi

echo "Account:            ${SBATCH_ACCOUNT}"
echo "Partition:          ${SBATCH_PARTITION}"
echo "Job name:           ${SBATCH_JOB_NAME}"
echo "Nodes:              ${SBATCH_NODES}"
echo "Tasks per node:     ${SBATCH_TASKS_PER_NODE}"
echo "CPUs per task:      ${SBATCH_CPUS_PER_TASK}"
echo "Time:               ${SBATCH_TIME}"
echo "Memory per CPU:     ${SBATCH_MEM_PER_CPU}"
echo "Topology:           ${TOPOLOGY}"
echo "Strategy:           ${STRATEGY}"

if [[ $is_array == 0 ]]; then
    echo "Number of islands:  ${ISLAND_COUNT}"
    echo "Number of migrants: ${MIGRANT_COUNT}"
    echo "Migration interval: ${MIGRATION_INTERVAL}"

    if [[ "$TOPOLOGY" == "scale_free" ]]; then
        echo "m0:                 ${M0}"
        echo "m:                  ${M}"
    fi

    if [[ "$TOPOLOGY" == "meeting" ]]; then
        echo "z_star:             ${z_star}"
        echo "n_steps:            ${n_steps}"
        echo "npr0:               ${npr0}"
        echo "nmr1:               ${nmr1}"
        echo "ne_gamma:           ${ne_gamma}"
    fi
fi

args=(
  --account="${SBATCH_ACCOUNT}"
  --partition="${SBATCH_PARTITION}"
  --job-name="${SBATCH_JOB_NAME}"
  --nodes="${SBATCH_NODES}"
  --ntasks-per-node="${SBATCH_TASKS_PER_NODE}"
  --cpus-per-task="${SBATCH_CPUS_PER_TASK}"
  --time="${SBATCH_TIME}"
  --mem-per-cpu="${SBATCH_MEM_PER_CPU}"
)

if [[ $is_array == 1 ]]; then
  array_max=$(( $(wc -l < ./params.txt) - 1 ))
  args+=(
    --array=0-"${array_max}"%8
    --output="slurm/slurm-%A-%a.out"
    --error="slurm/slurm-%A-%a.out"
  )
fi

sbatch "${args[@]}" ./start_ray.sh
