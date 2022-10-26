#!/bin/bash

TYPE=jh

GEM5_PATH="/home/hjchoi/git/anns/jh"
ANNS_DATASET="/home/hjchoi/anns-dataset"

function generate_job() {
cat > "${JOBDIR}/qsub_"${OUTPUT}".sh" << EOF
#!/bin/bash
#$ -N ${CONFIG}_${OUTPUT}
#$ -S /bin/bash
#$ -j y
#$ -o ${OUTDIR}/simout
#$ -V
#$ -l h_vmem=$(( 14 ))G

ulimit -c 0

${GEM5_PATH}/build/ARM/gem5.opt -d ${OUTDIR} \\
    ${GEM5_PATH}/configs/example/fs.py --kernel=arm64-vmlinux-5.15-jh-controller \\
    --machine-type=VExpress_GEM5_V1 \\
    --num-cpu=1 --cpu-clock=3.6GHz --cpu-type=TimingSimpleCPU \\
    --caches --l1d_size=512kB --l1i_size=256kB --l2cache --l2_size=64MB \\
    --mem-size=4GB --mem-type=DDR4_3200_8x8 \\
    --cxl-mem-size=2GB --cxl-mem-image-file=${ANNS_DATASET}/sift1M/nsg-sift1M-r50.index \\
    --extra-mem-size=2GB --extra-mem-image-file=${ANNS_DATASET}/sift1M/nsg-sift1M-r50.graph \\
    --disk=arm64-faiss-no-check.img \\
    --disk=data.img \\
    --script=${GEM5_PATH}/script/sift1M-jh-${1}.sh \\
    --pcie-gen=${PCIE_GEN} --flit-mode=${FLIT_MODE} --jh
EOF
}

PCIE_GEN=5
FLIT_MODE=B68
CONFIG=${TYPE}_${PCIE_GEN}_${FLIT_MODE}

JOBDIR="/home/hjchoi/jobs/anns/${CONFIG}"
mkdir -p ${JOBDIR}
rm ${JOBDIR}/*

for search_l in 16 32 64 128 256 512
do
  OUTDIR="/home/hjchoi/result/anns/sift1M/${CONFIG}/${search_l}_4GB"
  OUTPUT="sift1M_${search_l}_4GB"
  mkdir -p ${OUTDIR}
  generate_job ${search_l}
done

PCIE_GEN=6
FLIT_MODE=B68
CONFIG=${TYPE}_${PCIE_GEN}_${FLIT_MODE}

JOBDIR="/home/hjchoi/jobs/anns/${CONFIG}"
mkdir -p ${JOBDIR}
rm ${JOBDIR}/*

for search_l in 16 32 64 128 256 512
do
  OUTDIR="/home/hjchoi/result/anns/sift1M/${CONFIG}/${search_l}_4GB"
  OUTPUT="sift1M_${search_l}_4GB"
  mkdir -p ${OUTDIR}
  generate_job ${search_l}
done

PCIE_GEN=6
FLIT_MODE=B256
CONFIG=${TYPE}_${PCIE_GEN}_${FLIT_MODE}

JOBDIR="/home/hjchoi/jobs/anns/${CONFIG}"
mkdir -p ${JOBDIR}
rm ${JOBDIR}/*

for search_l in 16 32 64 128 256 512
do
  OUTDIR="/home/hjchoi/result/anns/sift1M/${CONFIG}/${search_l}_4GB"
  OUTPUT="sift1M_${search_l}_4GB"
  mkdir -p ${OUTDIR}
  generate_job ${search_l}
done

chmod 755 ${JOBDIR}/*
