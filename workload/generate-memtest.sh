#!/bin/bash

rm jobs/memtest_cxl/*

size=4*1024*1024*1024
random=0

if [ $random -eq 0 ]
then
    full=1
else
    full=0
fi

function generate_job() {
cat > "jobs/memtest_cxl/qsub_"$1".sh" << EOF
#!/bin/bash
#$ -N $1
#$ -S /bin/bash
#$ -j y
#$ -o /dev/null
#$ -V
#$ -l h_vmem=$(( 4 * $ctrl_num + 4 ))G

ulimit -c 0

cd /home/hjchoi/git/gem5
/home/hjchoi/git/gem5/build/X86/gem5.opt \
  --stats-file=${OUTDIR}/stats_${type}_${addr_map}_${ctrl_num}_${random}_${percent_reads}.txt \
  /home/hjchoi/git/gem5/configs/example/cxl_memtest.py --max-loads=1000000 --cxl=${cxl} --size=$(($size * $ctrl_num)) \
  --num-cpu=1 --percent-reads=$percent_reads --num-memctrl=$ctrl_num --addr-map=$addr_map --random=$random --full=$full
  # --debug-flags=HanjinTest
  # --debug-file=${OUTDIR}/${type}_${addr_map}_${ctrl_num}_${random}_${percent_reads}.log
EOF
}

for ((i = 0; i < 2 * 120; i++))
do
  addr_map=$(( i % 120 ))
  percent_reads=$(( ( ( i / (120) ) % 2 ) * 100 ))
  # cxl=$(( ( i / (2 * 120) ) % 2 ))
  # ctrl_num=$(( 2 ** ( i / (4 * 120) ) ))
  cxl=1
  ctrl_num=2
  
  if [ $cxl -eq 0 ]
  then
    type=dram
  else
    type=cxl
  fi

  # echo ${type} ${addr_map} ${ctrl_num} ${random} ${percent_reads}

  OUTDIR="/home/hjchoi/git/gem5/m5out/${addr_map}"
  mkdir -p ${OUTDIR}
  generate_job "${type}_${addr_map}_${ctrl_num}_${random}_${percent_reads}"
done

for ((i = 0; i < 4 * 120; i++))
do
  addr_map=$(( i % 120 ))
  percent_reads=$(( ( ( i / (120) ) % 2 ) * 100 ))
  cxl=$(( ( i / (2 * 120) ) % 2 ))
  # ctrl_num=$(( 2 ** ( i / (4 * 120) ) ))
  ctrl_num=4
  
  if [ $cxl -eq 0 ]
  then
    type=dram
  else
    type=cxl
  fi

  # echo ${type} ${addr_map} ${ctrl_num} ${random} ${percent_reads}

  OUTDIR="/home/hjchoi/git/gem5/m5out/${addr_map}"
  mkdir -p ${OUTDIR}
  generate_job "${type}_${addr_map}_${ctrl_num}_${random}_${percent_reads}"
done

chmod 755 jobs/memtest_cxl/*
