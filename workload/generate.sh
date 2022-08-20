#!/bin/bash
WORKLOAD=(
#  rocksdb/readseq
#  rocksdb/readrandom
#  rocksdb/overwrite
#  rocksdb/readrandomwriterandom
#  rocksdb/deleterandom
#  mysql/tpcc
#  mysql/tpch-2
  mysql/tpch-4
#  mysql/tpch-6
#  mysql/tpch-7
#  mysql/tpch-10
  mysql/tpch-11
#  mysql/tpch-12
#  mysql/tpch-14
#  mysql/tpch-20
#  text/grep
#  text/wordcount
#  text/linecount
  nginx/stream
  nginx/web0
  nginx/web1
  vsftpd/upload
)

SIM_CONFIG=sim.xml
TRACE_ROOT=/home/kukdh1/git/lambda-script
CKP_ISP=/home/kukdh1/lambda_new/ckp_isp
CKP_HOST=/home/kukdh1/lambda_new/ckp_host
OUTDIR_PREFIX=/home/kukdh1/lambda_new/result_fw

function generate_host() {
cat > "${OUTDIR_PREFIX}/../scripts/qsub_"$1".sh" << EOF
#!/bin/bash
#$ -q hipri.q
#$ -N $1
#$ -S /bin/bash
#$ -j y
#$ -o ${OUTDIR}/simout
#$ -V
#$ -l h_vmem=20G

ulimit -c 0

cd /home/kukdh1/lambda_new
/home/kukdh1/git/kukdh1-standalone/build_lambda/simplessd-standalone \
    -R "${CKP_HOST}" \
    "-O=[sim][cputrace]TraceDirectory=${TRACE_PATH}" \
    -O=[sim][cputrace]ReplayMode=0 \
    -O=[sim][sim]Interface=1 \
    "${SIM_CONFIG}" \
    "${CKP_HOST}/config.xml" \
    "${OUTDIR}"
EOF
}

function generate_device() {
cat > "${OUTDIR_PREFIX}/../scripts/qsub_"$1".sh" << EOF
#!/bin/bash
#$ -q hipri.q
#$ -N $1
#$ -S /bin/bash
#$ -j y
#$ -o ${OUTDIR}/simout
#$ -V
#$ -l h_vmem=20G

ulimit -c 0

cd /home/kukdh1/lambda_new
/home/kukdh1/git/kukdh1-standalone/build_lambda/simplessd-standalone \
    -R "${CKP_ISP}" \
    "-O=[sim][cputrace]TraceDirectory=${TRACE_PATH}" \
    -O=[sim][cputrace]ReplayMode=$2 \
    -O=[sim][sim]Interface=0 \
    -O=[sim][sim]SubmissionLatency=0 \
    -O=[sim][sim]CompletionLatency=0 \
    "${SIM_CONFIG}" \
    "${CKP_ISP}/config.xml" \
    "${OUTDIR}"
EOF
}

for workload in ${WORKLOAD[@]}
do
  program=$(dirname ${workload})
  workload=$(basename ${workload})

  TRACE_PATH=${TRACE_ROOT}/${program}/out_ext4/trace_${workload}_3800MHz
  OUTDIR="${OUTDIR_PREFIX}/host_${program}_${workload}_3800"
  mkdir -p ${OUTDIR}
  generate_host "host_${program}_${workload}_3800"

  TRACE_PATH=${TRACE_ROOT}/${program}/out_ext4/trace_${workload}_2200MHz
  OUTDIR="${OUTDIR_PREFIX}/host_${program}_${workload}_2200"
  mkdir -p ${OUTDIR}
  generate_host "host_${program}_${workload}_2200"

  OUTDIR="${OUTDIR_PREFIX}/full_${program}_${workload}_2200"
  mkdir -p ${OUTDIR}
  generate_device "full_${program}_${workload}_2200" 0

  OUTDIR="${OUTDIR_PREFIX}/opt_${program}_${workload}_2200"
  mkdir -p ${OUTDIR}
  generate_device "opt_${program}_${workload}_2200" 2

  OUTDIR="${OUTDIR_PREFIX}/rpc_${program}_${workload}_2200"
  mkdir -p ${OUTDIR}
  generate_device "rpc_${program}_${workload}_2200" 3

  OUTDIR="${OUTDIR_PREFIX}/vsc_${program}_${workload}_2200"
  mkdir -p ${OUTDIR}
  generate_device "vcs_${program}_${workload}_2200" 4
done
