#!/bin/bash

size=4*1024*1024*1024
random=0
full=1

JOBDIR="/home/hjchoi/jobs/memtest/cxl"

rm ${JOBDIR}/*

function generate_job() {
cat > "${JOBDIR}/qsub_"${OUTPUT}".sh" << EOF
#!/bin/bash
#$ -N ${OUTPUT}
#$ -S /bin/bash
#$ -j y
#$ -o ${OUTDIR}/simout_${OUTPUT}.log
#$ -V
#$ -l h_vmem=$(( 4 ))G

ulimit -c 0

$M5_PATH/build/ARM/gem5.opt -d ${OUTDIR} \\
  --stats-file=stats_${OUTPUT}.txt \\
  /home/hjchoi/git/cxl-sim/configs/example/cxl_memtest.py --max-loads=$(( 16777216 )) --cxl=${cxl} --size=$(($size * $ctrl_num)) \\
  --num-cpu=1 --percent-reads=$percent_reads --mem-channels=$ctrl_num --addr-map=$addr_map --random=$random --full=$full
EOF
}

for ((i = 0; i < 2 * 120; i++))
do
  addr_map=$(( i % 120 ))
  percent_reads=$(( ( ( i / (120) ) % 2 ) * 100 ))
  cxl=1
  ctrl_num=2
  
  if [ $cxl -eq 0 ]
  then
    type=dram
  else
    type=cxl
  fi

  # echo ${type} ${addr_map} ${ctrl_num} ${random} ${percent_reads}

  OUTDIR="/home/hjchoi/result/memtest/cxl"
  OUTPUT="${type}_${addr_map}_${ctrl_num}_${random}_${percent_reads}"
  mkdir -p ${OUTDIR}
  generate_job
done

chmod 755 ${JOBDIR}/*
