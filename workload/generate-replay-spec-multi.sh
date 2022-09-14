#!/bin/bash

LIST=(
  429.mcf-433.milc-434.zeusmp-445.gobmk
  429.mcf-433.milc-434.zeusmp-471.omnetpp
  429.mcf-434.zeusmp-437.leslie3d-470.lbm
  429.mcf-434.zeusmp-445.gobmk-453.povray
  429.mcf-434.zeusmp-453.povray-459.GemsFDTD
  429.mcf-453.povray-459.GemsFDTD-470.lbm
  429.mcf-453.povray-459.GemsFDTD-471.omnetpp
  433.milc-434.zeusmp-437.leslie3d-471.omnetpp
  433.milc-434.zeusmp-445.gobmk-471.omnetpp
  433.milc-434.zeusmp-453.povray-470.lbm
  433.milc-434.zeusmp-459.GemsFDTD-470.lbm
  433.milc-434.zeusmp-459.GemsFDTD-471.omnetpp
  433.milc-437.leslie3d-445.gobmk-453.povray
  434.zeusmp-437.leslie3d-445.gobmk-459.GemsFDTD
  434.zeusmp-437.leslie3d-470.lbm-471.omnetpp
  434.zeusmp-445.gobmk-459.GemsFDTD-470.lbm
  434.zeusmp-453.povray-470.lbm-471.omnetpp
  437.leslie3d-459.GemsFDTD-470.lbm-471.omnetpp
)

function generate_job() {
cat > "/home/hjchoi/jobs/spec/replay/multi/qsub_replay_${1}_${2}_${3}_${4}.sh" << EOF
#!/bin/bash
#$ -N r${1}_${2}_${3}_${4}
#$ -S /bin/bash
#$ -j y
#$ -o ${OUTDIR}/${1}_${2}_${3}_${4}_simout
#$ -V
#$ -l h_vmem=$(( 10 ))G

ulimit -c 0

/home/hjchoi/git/cxl-sim/build/ARM/gem5.opt \\
    -d ${OUTDIR} \\
    --stats-file=${1}_${2}_${3}_${4}_stats.txt \\
    /home/hjchoi/git/cxl-sim/configs/example/cxl_etrace_replay.py \\
    --cpu-type=TraceCPU --num-cpu=4 --caches --l2cache \\
    --data-trace-files=${TRACEDIR}/system.switch_cpus0.traceListener.deptrace.proto.gz \\
    --inst-trace-files=${TRACEDIR}/system.switch_cpus0.traceListener.fetchtrace.proto.gz \\
    --data-trace-files=${TRACEDIR}/system.switch_cpus1.traceListener.deptrace.proto.gz \\
    --inst-trace-files=${TRACEDIR}/system.switch_cpus1.traceListener.fetchtrace.proto.gz \\
    --data-trace-files=${TRACEDIR}/system.switch_cpus2.traceListener.deptrace.proto.gz \\
    --inst-trace-files=${TRACEDIR}/system.switch_cpus2.traceListener.fetchtrace.proto.gz \\
    --data-trace-files=${TRACEDIR}/system.switch_cpus3.traceListener.deptrace.proto.gz \\
    --inst-trace-files=${TRACEDIR}/system.switch_cpus3.traceListener.fetchtrace.proto.gz \\
    --mem-size=4GB --cxl=${2} --addr-map${5}=${3} --mem-channels=${4} --cxl-switch=0 --num-type3=1
EOF
}

rm /home/hjchoi/jobs/spec/replay/multi/*

for file in ${LIST[@]}
do
  # echo $file

  TRACEDIR="/home/hjchoi/result/gem5-ARM-SPEC-CPU2006/trace/multi/trace_${file}"
  OUTDIR="/home/hjchoi/result/gem5-ARM-SPEC-CPU2006/replay/multi/replay_${file}"
  mkdir -p ${OUTDIR}
  
  ctrl_num=2
  # ctrl_num=$(( 2 ** ( i / 120 ) ))

  for ((i = 0; i < 1 * 96; i++))
  do
    addr_map=$(( i % 96 ))
    addr_map_version=2
    # addr_map=999
    # addr-map-version=3


    # echo generate_job "${file}" 1 ${addr_map} ${ctrl_num}

    generate_job "${file}" 1 ${addr_map} ${ctrl_num} ${addr_map_version}
  done

  generate_job "${file}" 1 999 ${ctrl_num} 3
done

chmod 755 /home/hjchoi/jobs/spec/replay/multi/*

