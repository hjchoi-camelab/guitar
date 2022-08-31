#!/bin/bash

LIST=(
  # 401.bzip2
  # 403.gcc
  # 429.mcf
  # 433.milc
  # 434.zeusmp
  # 435.gromacs
  # 436.cactusADM
  # 437.leslie3d
  # 444.namd
  # 445.gobmk
  # 453.povray
  # 454.calculix
  # 456.hmmer
  # 458.sjeng
  # 459.GemsFDTD
  # 462.libquantum
  # 464.h264ref
  465.tonto
  470.lbm
  471.omnetpp
  473.astar
)

rm jobs/spec/trace/single/*

function generate_job() {
cat > "/home/hjchoi/jobs/spec/trace/single/qsub_trace_"$1".sh" << EOF
#!/bin/bash
#$ -N t$1
#$ -S /bin/bash
#$ -j y
#$ -o /dev/null
#$ -V
#$ -l h_vmem=$(( 10 ))G

ulimit -c 0

cd /home/hjchoi/git/cxl-sim
/home/hjchoi/git/cxl-sim/build/ARM/gem5.opt -d ${OUTDIR} \
    /home/hjchoi/git/cxl-sim/configs/example/fs.py --kernel=/home/hjchoi/m5/binaries/vmlinux.arm64 \
    --machine-type=VExpress_GEM5_V1 \
    --num-cpu=1 --cpu-clock=2GHz --caches --cpu-type=DerivO3CPU \
    --mem-size=4GB --mem-type=SimpleMemory \
    --disk=/home/hjchoi/m5/disks/ubuntu-18.04-arm64-docker.img \
    --checkpoint-dir=/home/hjchoi/git/cxl-sim/checkpoint -r 1 \
    --elastic-trace-en \
    --data-trace-file=deptrace.proto.gz --inst-trace-file=fetchtrace.proto.gz \
    --script=/home/hjchoi/git/cxl-sim/script/single/${1}.sh -I 5000000000
EOF
}

for file in ${LIST[@]}
do
  # echo $file

  OUTDIR="/home/hjchoi/result/gem5-ARM-SPEC-CPU2006/trace/single/trace_${file}"
  mkdir -p ${OUTDIR}
  generate_job "${file}"
done

chmod 755 /home/hjchoi/jobs/spec/*
