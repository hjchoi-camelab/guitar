#!/bin/bash

LIST=(
  ################################## 400.perlbench
  401.bzip2
  # 403.gcc
  # 429.mcf
  # 433.milc
  # 434.zeusmp
  # 435.gromacs
  # 436.cactusADM
  # 437.leslie3d
  # 444.namd
  # 445.gobmk
  ################################## 447.dealII
  ################################## 450.soplex
  # 453.povray
  # 454.calculix
  # 456.hmmer
  458.sjeng
  # 459.GemsFDTD
  # 462.libquantum
  # 464.h264ref
  # 465.tonto
  470.lbm
  # 471.omnetpp
  # 473.astar
  ################################## 482.sphinx3
  ################################## 483.xalancbmk
)

rm ../jobs/spec/replay/*

function generate_job() {
cat > "../jobs/spec/replay/qsub_replay_${1}_${2}_${3}_${4}.sh" << EOF
#!/bin/bash
#$ -N r${1}_${2}_${3}_${4}
#$ -S /bin/bash
#$ -j y
#$ -o /dev/null
#$ -V
#$ -l h_vmem=$(( 10 ))G

ulimit -c 0

/home/hjchoi/git/cxl-sim/build/ARM/gem5.opt \
    -d ${OUTDIR} \
    --stats-file=${1}_${2}_${3}_${4}_stats.txt \
    /home/hjchoi/git/cxl-sim/configs/example/cxl_etrace_replay.py \
    --cpu-type=TraceCPU --caches --l2cache \
    --data-trace-file=${TRACEDIR}/system.switch_cpus.traceListener.deptrace.proto.gz \
    --inst-trace-file=${TRACEDIR}/system.switch_cpus.traceListener.fetchtrace.proto.gz \
    --mem-size=4GB --cxl=${2} --addr-map3=${3} --mem-channels=${4} --cxl-switch=0 --num-type3=1
EOF
}

for file in ${LIST[@]}
do
  # echo $file

  TRACEDIR="/home/hjchoi/result/gem5-ARM-SPEC-CPU2006/trace/single/trace_${file}"
  OUTDIR="/home/hjchoi/result/gem5-ARM-SPEC-CPU2006/replay/single/replay_${file}"
  mkdir -p ${OUTDIR}
  for ((i = 0; i < 1 * 96; i++))
  do
    addr_map=$(( i % 96 ))
    # addr_map=999
    ctrl_num=2
    # ctrl_num=$(( 2 ** ( i / 120 ) ))

    # echo generate_job "${file}" 1 ${addr_map} ${ctrl_num}

    generate_job "${file}" 1 ${addr_map} ${ctrl_num}
  done
done

chmod 755 ../jobs/spec/replay/*

