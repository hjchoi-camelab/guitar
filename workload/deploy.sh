#!/bin/bash
set -e
set -o pipefail

export PATH=/opt/riscv64-linux-gnu/bin:${PATH}

SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname "${SCRIPT_PATH}")

PACKAGE_DIR=${SCRIPT_DIR}/package

# Clear output directory
rm -rf ${PACKAGE_DIR}
mkdir -p ${PACKAGE_DIR}

# Copy required libraries
LIBRARY_DIR=${PACKAGE_DIR}/lib
mkdir -p ${LIBRARY_DIR}

# Copy libraries
LIB_PREFIX=/opt/riscv64-linux-gnu/sysroot/lib
LIB_LIST=(
  libdl.so.2
  libpthread.so.0
  libatomic.so.1
  librdmacm.so.1
  libibverbs.so.1
  libstdc++.so.6
  libgfortran.so.5
  libm.so.6
  libgcc_s.so.1
  libc.so.6
  ld-linux-riscv64-lp64d.so.1
  libnl-route-3.so.200
  libnl-3.so.200
  libmlx4-rdmav2.so
)

for name in ${LIB_LIST[@]}
do
  cp ${LIB_PREFIX}/${name} ${LIBRARY_DIR}
done

# Create env.sh
cat << 'EOF' > ${PACKAGE_DIR}/env.sh
#!/bin/bash
export LD_LIBRARY_PATH=/root/lib

echo "Check RNIC exists"

MLX4_EXIST=$(lspci | grep "Mellanox" | wc -l)

if [ ${MLX4_EXIST} -ne 0 ]
then
  FPGA_ID=$(printenv ID)

  if [ ${#FPGA_ID} -eq 0 ]
  then
    echo "Please specify ID environment variable."
    exit 1
  fi

  if [ ${FPGA_ID} -eq 0 ]
  then
    echo "ID must not zero"
    exit 1
  elif [ ${FPGA_ID} -eq 1 ]
  then
    echo "ID == 1, this should be server of RDMA workloads"
  fi

  echo "Loading kernel modules"

  modprobe rdma_ucm
  modprobe mlx4_ib
  modprobe ib_ipoib

  echo "Configure ib0"

  ip addr add 192.168.10.${FPGA_ID}/24 dev ib0
  ip link set dev ib0 up

  ip addr
fi

echo "Configure cgroup"

MEM=$((4*1024*1024*1024)) # 4GB
CPU="1" # Let profiler to run on core 0

mount -t debugfs none /sys/kernel/debug
mount -t tmpfs cgroup_root /sys/fs/cgroup

mkdir -p /sys/fs/cgroup/cpuset
mount -t cgroup cpuset -o cpuset /sys/fs/cgroup/cpuset

mkdir -p /sys/fs/cgroup/memory
mount -t cgroup memory -o memory /sys/fs/cgroup/memory

mkdir -p /sys/fs/cgroup/cpuset/workload
echo ${CPU} > /sys/fs/cgroup/cpuset/workload/cpuset.cpus
echo 0 > /sys/fs/cgroup/cpuset/workload/cpuset.mems

mkdir -p /sys/fs/cgroup/memory/workload
echo ${MEM} > /sys/fs/cgroup/memory/workload/memory.limit_in_bytes
EOF

# Create limit.sh
cat << 'EOF' > ${PACKAGE_DIR}/limit.sh
#!/bin/bash
if [ "$#" -ge 1 ]
then
  if [ $(id -u) -eq "0" ]
  then
    # Configure cpuset cgroup
    if [ -d "/sys/fs/cgroup/cpuset/workload" ]
    then
      # Add self
      echo $$ > /sys/fs/cgroup/cpuset/workload/tasks
    fi

    # Configure memory cgroup
    if [ -d "/sys/fs/cgroup/memory/workload" ]
    then
      # Add self
      echo $$ > /sys/fs/cgroup/memory/workload/tasks
    fi
  fi

  $1 "${@:2}"
else
  echo "Insufficient parameters"
fi
EOF

# Create limit_cpu.sh
cat << 'EOF' > ${PACKAGE_DIR}/limit_cpu.sh
#!/bin/bash
if [ "$#" -ge 1 ]
then
  if [ $(id -u) -eq "0" ]
  then
    # Configure cpuset cgroup
    if [ -d "/sys/fs/cgroup/cpuset/workload" ]
    then
      # Add self
      echo $$ > /sys/fs/cgroup/cpuset/workload/tasks
    fi
  fi

  $1 "${@:2}"
else
  echo "Insufficient parameters"
fi
EOF

# dlmalloc
if [ -d ${SCRIPT_DIR}/dlmalloc ]
then
  BUILD_DIR=${SCRIPT_DIR}/dlmalloc
  OUTPUT_DIR=${PACKAGE_DIR}/lib

  echo "Building dlmalloc"

  cd ${BUILD_DIR}

  make clean
  CROSS_COMPILE=riscv64-unknown-linux-gnu- make

  cp dlmalloc.so ${OUTPUT_DIR}
fi

# FastSwap
if [ -d ${SCRIPT_DIR}/fastswap ]
then
  BUILD_DIR=${SCRIPT_DIR}/fastswap/farmemserver
  OUTPUT_DIR=${PACKAGE_DIR}/fastswap

  echo "Building FastSwap remote server"

  cd ${BUILD_DIR}

  make clean
  CROSS_COMPILE=riscv64-unknown-linux-gnu- make

  mkdir -p ${OUTPUT_DIR}

  cp rmserver ${OUTPUT_DIR}

cat << 'EOF' > ${OUTPUT_DIR}/run_fastswap.sh
#!/bin/bash
set -e
set -o pipefail

THIS_PATH=$(readlink -f "$0")
THIS_DIR=$(dirname ${THIS_PATH})

MODE=$(printenv MODE)

case ${MODE} in
  client)
    echo "Enable swap"
    swapon /dev/nvme0n1p1
    echo "Installing fastswap kernel modules"
    modprobe fastswap_rdma sport=50000 sip="192.168.10.1" cip="192.168.10.2" nq=2
    modprobe fastswap
    ;;
  server)
    echo "Running fastswap remote server"
    ${THIS_DIR}/rmserver 50000
    ;;
  cleanup)
    echo "Disable swap"
    swapoff /dev/nvme0n1p1
    echo "Removing fastswap kernel modules"
    rmmod fastswap
    rmmod fastswap_rdma
    ;;
  *)
    echo "Please specify MODE={client,server,cleanup}"
    exit 1
    ;;
esac
EOF
fi

# DLRM
if [ -d ${SCRIPT_DIR}/dlrm ]
then
  BUILD_DIR=${SCRIPT_DIR}/dlrm/build_riscv
  OUTPUT_DIR=${PACKAGE_DIR}/dlrm

  echo "Building DLRM"

  mkdir -p ${BUILD_DIR}

  cd ${BUILD_DIR}

  cmake -DCMAKE_BUILD_TYPE=Release -DFAST_INIT=1 -DPROFILE=1 -DCROSS_COMPILE=1 -DDISABLE_ROCC=1 -DEMULATE_SWAP=0 ..
  make -j $(nproc)

  mkdir -p ${OUTPUT_DIR}

  cp dlrm-* *-server ${OUTPUT_DIR}

cat << 'EOF' > ${OUTPUT_DIR}/run_dlrm.sh
#!/bin/bash
set -e
set -o pipefail

THIS_PATH=$(readlink -f "$0")
THIS_DIR=$(dirname ${THIS_PATH})

EPOCH=1
ITER=16
INDICES=8

SCALE_LIST=$(printenv SCALE)

if [ ${#SCALE_LIST} -eq 0 ]
then
  SCALE_LIST="1 2 4 8 16"
fi

MODE=$(printenv MODE)
DLRM=

case ${MODE} in
  local)
    DLRM="${THIS_DIR}/../limit_cpu.sh ${THIS_DIR}/dlrm-local"
    ;;
  swap)
    DLRM="${THIS_DIR}/../limit.sh ${THIS_DIR}/dlrm-local"
    ;;
  kvs)
    DLRM="${THIS_DIR}/../limit_cpu.sh ${THIS_DIR}/dlrm-kvs --ip 192.168.10.1 --port 16000"
    ;;
  far)
    DLRM="${THIS_DIR}/../limit_cpu.sh ${THIS_DIR}/dlrm-far --ip 192.168.10.1 --port 16000 --limit 20"
    ;;
  pool)
    DLRM="${THIS_DIR}/../limit_cpu.sh ${THIS_DIR}/dlrm-pooled"
    ;;
  *)
    echo "Please specify MODE={local,swap,kvs,kvsserver,far,pool}"
    exit 1
    ;;
esac

for scale in ${SCALE_LIST}
do
  echo "Running DLRM ${MODE}, scale="${scale}

  ${DLRM} -d random --inference-only --num-indices ${INDICES} -n ${EPOCH} -i ${ITER} --mlp-bot 512-256-64-$((scale*16)) dummy
done
EOF
fi

# Microbench
if [ -d ${SCRIPT_DIR}/microbench ]
then
  BUILD_DIR=${SCRIPT_DIR}/microbench/build_riscv
  OUTPUT_DIR=${PACKAGE_DIR}/microbench

  echo "Building microbench"

  mkdir -p ${BUILD_DIR}

  cd ${BUILD_DIR}

  cmake -DCMAKE_BUILD_TYPE=Release -DPROFILE=1 -DCROSS_COMPILE=1 ..
  make -j $(nproc)

  mkdir -p ${OUTPUT_DIR}

  cp local* rdma* ${OUTPUT_DIR}

cat << 'EOF' > ${OUTPUT_DIR}/run_microbench.sh
#!/bin/bash
set -e
set -o pipefail

THIS_PATH=$(readlink -f "$0")
THIS_DIR=$(dirname ${THIS_PATH})

MODE=$(printenv MODE)

case ${MODE} in
  local)
    echo "Run local memory benchmark"
    ${THIS_DIR}/../limit_cpu.sh ${THIS_DIR}/local 1
    ;;
  rdma)
    echo "Run rdma benchmark"
    ${THIS_DIR}/../limit_cpu.sh ${THIS_DIR}/rdma 192.168.10.1 16000
    ;;
  rdmabreak)
    echo "Run rdma breakdown"
    ${THIS_DIR}/../limit_cpu.sh ${THIS_DIR}/rdma_breakdown 192.168.10.1 16000
    ;;
  rdmaserver)
    echo "Run rdma server"
    ${THIS_DIR}/rdma_server 16000 32
    ;;
  pool)
    echo "Run pooled memory benchmark"
    ${THIS_DIR}/../limit_cpu.sh ${THIS_DIR}/local 0
    ;;
  *)
    echo "Please specify MODE={local,rdma,rdmabreak,rdmaserver,pool}"
    exit 1
    ;;
esac
EOF
fi

# Memcache
if [ -d ${SCRIPT_DIR}/memcache ]
then
  BUILD_DIR=${SCRIPT_DIR}/memcache/build_riscv
  OUTPUT_DIR=${PACKAGE_DIR}/memcache

  echo "Building memcache"

  mkdir -p ${BUILD_DIR}

  cd ${BUILD_DIR}

  cmake -DCMAKE_BUILD_TYPE=Release -DPROFILE=1 -DCROSS_COMPILE=1 ..
  make -j $(nproc)

  mkdir -p ${OUTPUT_DIR}

  cp kvs-* memcache ${OUTPUT_DIR}

cat << 'EOF' > ${OUTPUT_DIR}/run_memcache.sh
#!/bin/bash
set -e
set -o pipefail

THIS_PATH=$(readlink -f "$0")
THIS_DIR=$(dirname ${THIS_PATH})

NUM_KEYS=$((1048576*8))
VALUE_LIST="64 128 256 512 1024 2048 4096"

MODE=$(printenv MODE)
LIMIT_SCRIPT=${THIS_DIR}/../limit_cpu.sh

case ${MODE} in
  kvscdf)
    echo "Run kvs cdf"
    ${THIS_DIR}/../limit_cpu.sh ${THIS_DIR}/kvs-cdf --ip 192.168.10.1 --port 16000
    exit 0
    ;;
  kvsserver)
    echo "Run kvs server"
    ${THIS_DIR}/kvs-server
    exit 0
    ;;
  local)
    ;;
  kvs)
    ;;
  pool)
    ;;
  swap)
    LIMIT_SCRIPT=${THIS_DIR}/../limit.sh
    MODE=local
    ;;
  *)
    echo "Please specify MODE={local,swap,kvs,pool,kvscdf,kvsserver}"
    exit 1
    ;;
esac

for value_size in ${VALUE_LIST};
do
  ${LIMIT_SCRIPT} ${THIS_DIR}/memcache -m ${MODE} -n ${NUM_KEYS} -v ${value_size} --size 40 --ip 192.168.10.1 --port 16000
done

EOF
fi

# ligra
if [ -d ${SCRIPT_DIR}/ligra ]
then
  BUILD_DIR=${SCRIPT_DIR}/ligra/apps
  OUTPUT_DIR=${PACKAGE_DIR}/ligra``

  echo "Building ligra"

  cd ${BUILD_DIR}

  make clean
  CROSS_COMPILE=riscv64-unknown-linux-gnu- make BC BFS Components MIS -j $(nproc)

  mkdir -p ${OUTPUT_DIR}

  cp BC BFS Components MIS ${OUTPUT_DIR}

cat << 'EOF' > ${OUTPUT_DIR}/run_ligra.sh
#!/bin/bash
set -e
set -o pipefail

THIS_PATH=$(readlink -f "$0")
THIS_DIR=$(dirname ${THIS_PATH})

DEGREE=16
EDGES=$((128*1024*1024)) # n22

MODE=$(printenv MODE)
LIMIT_SCRIPT=${THIS_DIR}/../limit_cpu.sh
OPTION=--local

case ${MODE} in
  local)
    ;;
  swap)
    LIMIT_SCRIPT=${THIS_DIR}/../limit.sh
    ;;
  pool)
    OPTION=--pool
    ;;
  cdf)
    echo "trace-cmd record -e 'fastswap:*' -b 131072 &"
    echo "./limit.sh ./ligra/BFS --local -g -e 134217728 -d 16 &"
    exit 0
    ;;
  *)
    echo "Please specify MODE={local,swap,pool,cdf}"
    exit 1
    ;;
esac

for app in MIS BFS Components BC;
do
  echo "Running "${MODE}" "${app}" "${EDGES}

  ${LIMIT_SCRIPT} ${THIS_DIR}/$app ${OPTION} -g -e ${EDGES} -d ${DEGREE}
done
EOF
fi

# SPECCPU2006
if [ -d ${SCRIPT_DIR}/CPU2006v1.0.1 ]
then
  EXE_DIR=${SCRIPT_DIR}/CPU2006v1.0.1/benchspec/CPU2006
  OUTPUT_DIR=${PACKAGE_DIR}/speccpu

  echo "Copying SPECCPU2006"

  mkdir -p ${OUTPUT_DIR}

  cd ${EXE_DIR}

  function copy_spec() {
    DIRNAME=$1
    OUTDIR=${OUTPUT_DIR}/${DIRNAME}
    EXECNAME=${DIRNAME:4}_base.riscv64

    mkdir -p ${OUTDIR}
    cp ${DIRNAME}/exe/${EXECNAME} ${OUTDIR}

    if [ -d ${DIRNAME}/data/test/input ]
    then
      cp -R ${DIRNAME}/data/test/input/* ${OUTDIR}
    fi
    if [ -d ${DIRNAME}/data/all ]
    then
      cp -R ${DIRNAME}/data/all/input/* ${OUTDIR}
    fi

    # hack
    export BENCH_DIR=${OUTDIR}
  }

  # 400.perlbench
  copy_spec 400.perlbench

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./perlbench_base.riscv64 -I. -I./lib attrs.pl > /dev/null 2>&1
LD_PRELOAD=${DLMALLOC} ./perlbench_base.riscv64 -I. -I./lib gv.pl > /dev/null 2>&1
LD_PRELOAD=${DLMALLOC} ./perlbench_base.riscv64 -I. -I./lib makerand.pl > /dev/null 2>&1
LD_PRELOAD=${DLMALLOC} ./perlbench_base.riscv64 -I. -I./lib pack.pl > /dev/null 2>&1
LD_PRELOAD=${DLMALLOC} ./perlbench_base.riscv64 -I. -I./lib redef.pl > /dev/null 2>&1
LD_PRELOAD=${DLMALLOC} ./perlbench_base.riscv64 -I. -I./lib ref.pl > /dev/null 2>&1
LD_PRELOAD=${DLMALLOC} ./perlbench_base.riscv64 -I. -I./lib regmesg.pl > /dev/null 2>&1
LD_PRELOAD=${DLMALLOC} ./perlbench_base.riscv64 -I. -I./lib test.pl > /dev/null 2>&1
EOF

  # 401.bzip2
  copy_spec 401.bzip2

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./bzip2_base.riscv64 input.program 5 > /dev/null 2>&1
LD_PRELOAD=${DLMALLOC} ./bzip2_base.riscv64 dryer.jpg 2 > /dev/null 2>&1
EOF

  # 403.gcc
  copy_spec 403.gcc

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./gcc_base.riscv64 cccp.i -o cccp.s > /dev/null 2>&1
EOF

  # 429.mcf
  copy_spec 429.mcf

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./mcf_base.riscv64 inp.in > /dev/null 2>&1
EOF

  # 445.gobmk
  copy_spec 445.gobmk

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./gobmk_base.riscv64 --quiet --mode gtp < capture.tst > /dev/null 2>&1
LD_PRELOAD=${DLMALLOC} ./gobmk_base.riscv64 --quiet --mode gtp < connect.tst > /dev/null 2>&1
LD_PRELOAD=${DLMALLOC} ./gobmk_base.riscv64 --quiet --mode gtp < connect_rot.tst > /dev/null 2>&1
LD_PRELOAD=${DLMALLOC} ./gobmk_base.riscv64 --quiet --mode gtp < connection.tst > /dev/null 2>&1
LD_PRELOAD=${DLMALLOC} ./gobmk_base.riscv64 --quiet --mode gtp < connection_rot.tst > /dev/null 2>&1
LD_PRELOAD=${DLMALLOC} ./gobmk_base.riscv64 --quiet --mode gtp < cutstone.tst > /dev/null 2>&1
LD_PRELOAD=${DLMALLOC} ./gobmk_base.riscv64 --quiet --mode gtp < dniwog.tst > /dev/null 2>&1
EOF

  # 456.hmmer
  copy_spec 456.hmmer

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./hmmer_base.riscv64 --fixed 0 --mean 325 --num 45000 --sd 200 --seed 0 bombesin.hmm > /dev/null 2>&1
EOF

  # 458.sjeng
  copy_spec 458.sjeng

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./sjeng_base.riscv64 test.txt > /dev/null 2>&1
EOF

  # 462.libquantum
  copy_spec 462.libquantum

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./libquantum_base.riscv64 33 5 > /dev/null 2>&1
EOF

  # 464.h264ref
  copy_spec 464.h264ref

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./h264ref_base.riscv64 -d foreman_test_encoder_baseline.cfg > /dev/null 2>&1
EOF

  # 471.omnetpp
  copy_spec 471.omnetpp

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./omnetpp_base.riscv64 omnetpp.ini > /dev/null 2>&1
EOF

  # 473.astar
  copy_spec 473.astar

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./astar_base.riscv64 lake.cfg > /dev/null 2>&1
EOF

  # 483.xalancbmk
  DIRNAME=483.xalancbmk
  OUTDIR=${OUTPUT_DIR}/${DIRNAME}
  EXECNAME=Xalan_base.riscv64

  mkdir -p ${OUTDIR}
  cp ${DIRNAME}/exe/${EXECNAME} ${OUTDIR}
  cp -R ${DIRNAME}/data/test/input/* ${OUTDIR}

cat << 'EOF' > ${OUTDIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./Xalan_base.riscv64 -v test.xml xalanc.xsl > /dev/null 2>&1
EOF

  # 410.bwaves
  copy_spec 410.bwaves

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./bwaves_base.riscv64 > /dev/null 2>&1
EOF

  ## 416.gamess
  # 433.milc
  copy_spec 433.milc

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./milc_base.riscv64 < su3imp.in > /dev/null 2>&1
EOF

  # 434.zeusmp
  copy_spec 434.zeusmp

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./zeusmp_base.riscv64 > /dev/null 2>&1
EOF

  # 435.gromacs
  copy_spec 435.gromacs

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./gromacs_base.riscv64 -silent -deffnm gromacs -nice 0 > /dev/null 2>&1
EOF

  # 436.cactusADM
  copy_spec 436.cactusADM

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./cactusADM_base.riscv64 benchADM.par > /dev/null 2>&1
EOF

  # 437.leslie3d
  copy_spec 437.leslie3d

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./leslie3d_base.riscv64 < leslie3d.in > /dev/null 2>&1
EOF

  # 444.namd
  copy_spec 444.namd

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./namd_base.riscv64 --input namd.input --iterations 1 --output namd.out > /dev/null 2>&1
EOF

  # 447.dealII
  copy_spec 447.dealII

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./dealII_base.riscv64 8 > /dev/null 2>&1
EOF

  # 450.soplex
  copy_spec 450.soplex

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./soplex_base.riscv64 -m10000 test.mps > /dev/null 2>&1
EOF

  # 453.povray
  copy_spec 453.povray

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./povray_base.riscv64 SPEC-benchmark-test.ini > /dev/null 2>&1
EOF

  # 454.calculix
  copy_spec 454.calculix

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./calculix_base.riscv64 -i beampic > /dev/null 2>&1
EOF

  # 459.GemsFDTD
  copy_spec 459.GemsFDTD

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./GemsFDTD_base.riscv64 > /dev/null 2>&1
EOF

  # 465.tonto
  copy_spec 465.tonto

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./tonto_base.riscv64 > /dev/null 2>&1
EOF

  # 470.lbm
  copy_spec 470.lbm

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./lbm_base.riscv64 20 reference.dat 0 1 100_100_130_cf_a.of > /dev/null 2>&1
EOF

  ## 481.wrf
  # 482.sphinx3
  DIRNAME=482.sphinx3
  OUTDIR=${OUTPUT_DIR}/${DIRNAME}
  EXECNAME=sphinx_livepretend_base.riscv64

  mkdir -p ${OUTDIR}
  cp ${DIRNAME}/exe/${EXECNAME} ${OUTDIR}
  cp -R ${DIRNAME}/data/all/input/* ${OUTDIR}
  cp -R ${DIRNAME}/data/test/input/* ${OUTDIR}

cat << 'EOF' > ${OUTDIR}/run.sh
#!/bin/bash
LD_PRELOAD=${DLMALLOC} ./sphinx_livepretend_base.riscv64 ctlfile . args.an4 > /dev/null 2>&1
EOF

cat << 'EOF' > ${OUTDIR}/ctlfile
an406-fcaw-b.le 128000
an407-fcaw-b.le 131200
EOF

cat << 'EOF' > ${OUTPUT_DIR}/run_speccpu.sh
#!/bin/bash
THIS_PATH=$(readlink -f "$0")
THIS_DIR=$(dirname ${THIS_PATH})

cd ${THIS_DIR}

LIST=(
  400.perlbench
  401.bzip2
  403.gcc
  429.mcf
  445.gobmk
  456.hmmer
  458.sjeng
  462.libquantum
  464.h264ref
  471.omnetpp
  473.astar
  483.xalancbmk
  410.bwaves
  433.milc
  434.zeusmp
  435.gromacs
  436.cactusADM
  437.leslie3d
  444.namd
  447.dealII
  450.soplex
  453.povray
  454.calculix
  459.GemsFDTD
  465.tonto
  470.lbm
  482.sphinx3
)

MODE=$(printenv MODE)
LIMIT_SCRIPT=${THIS_DIR}/../limit_cpu.sh

case ${MODE} in
  local)
    ;;
  swap)
    LIMIT_SCRIPT=${THIS_DIR}/../limit.sh
    ;;
  pool)
    export DLMALLOC=/root/lib/dlmalloc.so
    ;;
  *)
    echo "Please specify MODE={local,swap,pool}"
    exit 1
    ;;
esac

for dir in ${LIST[@]}
do
  cd ${dir}

  echo "Running "${dir}" for first time"

  # Warmup (mitigate slow SD card performance)
  LATENCY=$({ time ${THIS_DIR}/../limit_cpu.sh ./run.sh; } 2>&1 | grep real | awk '{ print $2; }')

  echo ${dir} ${LATENCY}

  echo "Running "${dir}

  LATENCY=$({ time ${LIMIT_SCRIPT} ./run.sh; } 2>&1 | grep real | awk '{ print $2; }')

  echo ${dir} ${LATENCY}

  cd ..
done

EOF
fi

# X-Mem
if [ -d ${SCRIPT_DIR}/x-mem ]
then
  BUILD_DIR=${SCRIPT_DIR}/x-mem/src
  OUTPUT_DIR=${PACKAGE_DIR}/xmem

  echo "Building X-Mem"

  cd ${BUILD_DIR}

  make clean
  CROSS_COMPILE=riscv64-unknown-linux-gnu- make -j $(nproc)

  mkdir -p ${OUTPUT_DIR}

  cp xmem ${OUTPUT_DIR}

cat << 'EOF' > ${OUTPUT_DIR}/run_xmem.sh
#!/bin/bash
set -e
set -o pipefail

THIS_PATH=$(readlink -f "$0")
THIS_DIR=$(dirname ${THIS_PATH})

MODE=$(printenv MODE)

case ${MODE} in
  local)
    ;;
  pool)
    export DLMALLOC=/root/lib/dlmalloc.so
    ;;
  *)
    echo "Please specify MODE={local,pool}"
    exit 1
    ;;
esac

echo "Running X-Mem"
LD_PRELOAD=${DLMALLOC} ${THIS_DIR}/xmem
EOF
fi

# TODO: Add more

# Package
echo "Compressing output directory"

cd ${PACKAGE_DIR}

find . -name '*.sh' -exec chmod +x {} \;

tar czf ../workload.tgz *
