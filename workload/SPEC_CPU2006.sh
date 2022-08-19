#!/bin/bash
set -e
set -o pipefail

SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname "${SCRIPT_PATH}")

PACKAGE_DIR=${SCRIPT_DIR}/package

# Clear output directory
rm -rf ${PACKAGE_DIR}
mkdir -p ${PACKAGE_DIR}

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
    EXECNAME=${DIRNAME:4}_base.amd64

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

#   # 400.perlbench
#   copy_spec 400.perlbench

# cat << 'EOF' > ${BENCH_DIR}/run.sh
# #!/bin/bash
# ./perlbench_base.amd64 -I. -I./lib attrs.pl > /dev/null 2>&1
# ./perlbench_base.amd64 -I. -I./lib gv.pl > /dev/null 2>&1
# ./perlbench_base.amd64 -I. -I./lib makerand.pl > /dev/null 2>&1
# ./perlbench_base.amd64 -I. -I./lib pack.pl > /dev/null 2>&1
# ./perlbench_base.amd64 -I. -I./lib redef.pl > /dev/null 2>&1
# ./perlbench_base.amd64 -I. -I./lib ref.pl > /dev/null 2>&1
# ./perlbench_base.amd64 -I. -I./lib regmesg.pl > /dev/null 2>&1
# ./perlbench_base.amd64 -I. -I./lib test.pl > /dev/null 2>&1
# EOF

  # 401.bzip2
  copy_spec 401.bzip2

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
./bzip2_base.amd64 input.program 5 > /dev/null 2>&1
./bzip2_base.amd64 dryer.jpg 2 > /dev/null 2>&1
EOF

  # 403.gcc
  copy_spec 403.gcc

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
./gcc_base.amd64 cccp.i -o cccp.s > /dev/null 2>&1
EOF

  # 429.mcf
  copy_spec 429.mcf

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
./mcf_base.amd64 inp.in > /dev/null 2>&1
EOF

  # 445.gobmk
  copy_spec 445.gobmk

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
./gobmk_base.amd64 --quiet --mode gtp < capture.tst > /dev/null 2>&1
./gobmk_base.amd64 --quiet --mode gtp < connect.tst > /dev/null 2>&1
./gobmk_base.amd64 --quiet --mode gtp < connect_rot.tst > /dev/null 2>&1
./gobmk_base.amd64 --quiet --mode gtp < connection.tst > /dev/null 2>&1
./gobmk_base.amd64 --quiet --mode gtp < connection_rot.tst > /dev/null 2>&1
./gobmk_base.amd64 --quiet --mode gtp < cutstone.tst > /dev/null 2>&1
./gobmk_base.amd64 --quiet --mode gtp < dniwog.tst > /dev/null 2>&1
EOF

  # 456.hmmer
  copy_spec 456.hmmer

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
./hmmer_base.amd64 --fixed 0 --mean 325 --num 45000 --sd 200 --seed 0 bombesin.hmm > /dev/null 2>&1
EOF

  # 458.sjeng
  copy_spec 458.sjeng

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
./sjeng_base.amd64 test.txt > /dev/null 2>&1
EOF

  # 462.libquantum
  copy_spec 462.libquantum

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
./libquantum_base.amd64 33 5 > /dev/null 2>&1
EOF

  # 464.h264ref
  copy_spec 464.h264ref

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
./h264ref_base.amd64 -d foreman_test_encoder_baseline.cfg > /dev/null 2>&1
EOF

  # 471.omnetpp
  copy_spec 471.omnetpp

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
./omnetpp_base.amd64 omnetpp.ini > /dev/null 2>&1
EOF

  # 473.astar
  copy_spec 473.astar

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
./astar_base.amd64 lake.cfg > /dev/null 2>&1
EOF

#   # 483.xalancbmk
#   DIRNAME=483.xalancbmk
#   OUTDIR=${OUTPUT_DIR}/${DIRNAME}
#   EXECNAME=Xalan_base.amd64

#   mkdir -p ${OUTDIR}
#   cp ${DIRNAME}/exe/${EXECNAME} ${OUTDIR}
#   cp -R ${DIRNAME}/data/test/input/* ${OUTDIR}

# cat << 'EOF' > ${OUTDIR}/run.sh
# #!/bin/bash
# ./Xalan_base.amd64 -v test.xml xalanc.xsl > /dev/null 2>&1
# EOF

#   # 410.bwaves
#   copy_spec 410.bwaves

# cat << 'EOF' > ${BENCH_DIR}/run.sh
# #!/bin/bash
# ./bwaves_base.amd64 > /dev/null 2>&1
# EOF

  ## 416.gamess
  # 433.milc
  copy_spec 433.milc

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
./milc_base.amd64 < su3imp.in > /dev/null 2>&1
EOF

#   # 434.zeusmp
#   copy_spec 434.zeusmp

# cat << 'EOF' > ${BENCH_DIR}/run.sh
# #!/bin/bash
# ./zeusmp_base.amd64 > /dev/null 2>&1
# EOF

#   # 435.gromacs
#   copy_spec 435.gromacs

# cat << 'EOF' > ${BENCH_DIR}/run.sh
# #!/bin/bash
# ./gromacs_base.amd64 -silent -deffnm gromacs -nice 0 > /dev/null 2>&1
# EOF

#   # 436.cactusADM
#   copy_spec 436.cactusADM

# cat << 'EOF' > ${BENCH_DIR}/run.sh
# #!/bin/bash
# ./cactusADM_base.amd64 benchADM.par > /dev/null 2>&1
# EOF

#   # 437.leslie3d
#   copy_spec 437.leslie3d

# cat << 'EOF' > ${BENCH_DIR}/run.sh
# #!/bin/bash
# ./leslie3d_base.amd64 < leslie3d.in > /dev/null 2>&1
# EOF

  # 444.namd
  copy_spec 444.namd

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
./namd_base.amd64 --input namd.input --iterations 1 --output namd.out > /dev/null 2>&1
EOF

#   # 447.dealII
#   copy_spec 447.dealII

# cat << 'EOF' > ${BENCH_DIR}/run.sh
# #!/bin/bash
# ./dealII_base.amd64 8 > /dev/null 2>&1
# EOF

#   # 450.soplex
#   copy_spec 450.soplex

# cat << 'EOF' > ${BENCH_DIR}/run.sh
# #!/bin/bash
# ./soplex_base.amd64 -m10000 test.mps > /dev/null 2>&1
# EOF

  # 453.povray
  copy_spec 453.povray

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
./povray_base.amd64 SPEC-benchmark-test.ini > /dev/null 2>&1
EOF

#   # 454.calculix
#   copy_spec 454.calculix

# cat << 'EOF' > ${BENCH_DIR}/run.sh
# #!/bin/bash
# ./calculix_base.amd64 -i beampic > /dev/null 2>&1
# EOF

#   # 459.GemsFDTD
#   copy_spec 459.GemsFDTD

# cat << 'EOF' > ${BENCH_DIR}/run.sh
# #!/bin/bash
# ./GemsFDTD_base.amd64 > /dev/null 2>&1
# EOF

#   # 465.tonto
#   copy_spec 465.tonto

# cat << 'EOF' > ${BENCH_DIR}/run.sh
# #!/bin/bash
# ./tonto_base.amd64 > /dev/null 2>&1
# EOF

  # 470.lbm
  copy_spec 470.lbm

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
./lbm_base.amd64 20 reference.dat 0 1 100_100_130_cf_a.of > /dev/null 2>&1
EOF

  ## 481.wrf
  # 482.sphinx3
  DIRNAME=482.sphinx3
  OUTDIR=${OUTPUT_DIR}/${DIRNAME}
  EXECNAME=sphinx_livepretend_base.amd64

  mkdir -p ${OUTDIR}
  cp ${DIRNAME}/exe/${EXECNAME} ${OUTDIR}
  cp -R ${DIRNAME}/data/all/input/* ${OUTDIR}
  cp -R ${DIRNAME}/data/test/input/* ${OUTDIR}

cat << 'EOF' > ${OUTDIR}/run.sh
#!/bin/bash
./sphinx_livepretend_base.amd64 ctlfile . args.an4 > /dev/null 2>&1
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
  # 400.perlbench
  401.bzip2
  403.gcc
  # 410.bwaves
  429.mcf
  433.milc
  # 434.zeusmp
  # 435.gromacs
  # 436.cactusADM
  # 437.leslie3d
  444.namd
  445.gobmk
  # 447.dealII
  # 450.soplex
  453.povray
  # 454.calculix
  456.hmmer
  458.sjeng
  # 459.GemsFDTD
  462.libquantum
  464.h264ref
  # 465.tonto
  470.lbm
  471.omnetpp
  473.astar
  482.sphinx3
  # 483.xalancbmk
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

# TODO: Add more

# Package
# echo "Compressing output directory"

# cd ${PACKAGE_DIR}

# find . -name '*.sh' -exec chmod +x {} \;

# tar czf ../workload.tgz *
