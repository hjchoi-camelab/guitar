#!/bin/bash

LIST=(
  1G
  2G
  3G
  4G
)

JOBDIR="/home/hjchoi/jobs/anns"
GEM5_PATH="/home/hjchoi/git/anns/jh"
ANNS_DATASET="/home/hjchoi/anns-dataset"

rm ${JOBDIR}/*

function generate_job() {
cat > "${JOBDIR}/qsub_"${OUTPUT}".sh" << EOF
#!/bin/bash
#$ -N ${OUTPUT}
#$ -S /bin/bash
#$ -j y
#$ -o ${OUTDIR}/simout
#$ -V
#$ -l h_vmem=$(( 20 ))G

ulimit -c 0

${GEM5_PATH}/build/ARM/gem5.opt -d ${OUTDIR} \\
    ${GEM5_PATH}/configs/example/fs.py --kernel=arm64-vmlinux-5.15-jh-controller \\
    --machine-type=VExpress_GEM5_V1 \\
    --num-cpu=1 --cpu-clock=${2}Hz --caches --l2cache --cpu-type=TimingSimpleCPU \\
    --mem-size=16GB --mem-type=DDR4_3200_8x8 \\
    --disk=arm64-faiss.img \\
    --disk=data.img \\
    --checkpoint-dir=${GEM5_PATH}/m5out/single -r 1 \\
    --extra-mem-size=2GB --mem-image-file=${ANNS_DATASET}/sift1M/database.fbin \\
    --script=${GEM5_PATH}/script/sift1M-${1}.sh 
EOF
}

for clock in ${LIST[@]}
do
  for search_l in 16 32 64 128 256 512
  do
    OUTDIR="/home/hjchoi/result/anns/sift1M/${search_l}_${clock}Hz_16GB"
    OUTPUT="sift1M_${search_l}_${clock}Hz_16GB"
    mkdir -p ${OUTDIR}
    generate_job ${search_l} ${clock}
  done
done

chmod 755 ${JOBDIR}/*
