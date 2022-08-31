#!/bin/bash

rm /home/hjchoi/jobs/spec/trace/multi/*

function generate_job() {
cat > "/home/hjchoi/jobs/spec/trace/multi/qsub_trace_"$1".sh" << EOF
#!/bin/bash
#$ -N t$1
#$ -S /bin/bash
#$ -j y
#$ -o ${OUTDIR}/simout
#$ -V
#$ -l h_vmem=$(( 12 ))G

ulimit -c 0

cd ${GEM5_PATH}
${GEM5_PATH}/build/ARM/gem5.opt -d ${OUTDIR} \
    ${GEM5_PATH}/configs/example/fs.py --kernel=${M5_PATH}/binaries/vmlinux.arm64 \
    --machine-type=VExpress_GEM5_V1 \
    --num-cpu=4 --cpu-clock=2GHz --caches --cpu-type=DerivO3CPU \
    --mem-size=4GB --mem-type=SimpleMemory \
    --disk=${M5_PATH}/disks/ubuntu-18.04-arm64-docker.img \
    --checkpoint-dir=${GEM5_PATH}/checkpoint/multi -r 1 \
    --elastic-trace-en \
    --data-trace-file=deptrace.proto.gz --inst-trace-file=fetchtrace.proto.gz \
    --script="${GEM5_PATH}/script/multi/${1}.sh" -I 5000000000
EOF
}

while read -r workload
do
  # echo $workload

  GEM5_PATH="/home/hjchoi/git/cxl-sim"
  OUTDIR="/home/hjchoi/result/gem5-ARM-SPEC-CPU2006/trace/multi/trace_${workload}"
  mkdir -p ${OUTDIR}
  generate_job "${workload}"
done

chmod 755 /home/hjchoi/jobs/spec/trace/multi/*
