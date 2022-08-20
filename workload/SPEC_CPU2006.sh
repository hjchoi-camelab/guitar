#!/bin/bash
set -e
set -o pipefail

SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname "${SCRIPT_PATH}")

PACKAGE_DIR=${SCRIPT_DIR}/package

# Clear output directory
rm -rf ${PACKAGE_DIR}
mkdir -p ${PACKAGE_DIR}

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
    EXECNAME=${DIRNAME:4}_base.arm64

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
# echo $0
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
echo $0
./bzip2_base.amd64 input.program 5 > /dev/null 2>&1
./bzip2_base.amd64 dryer.jpg 2 > /dev/null 2>&1
EOF

  # 403.gcc
  copy_spec 403.gcc

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./gcc_base.amd64 cccp.i -o cccp.s > /dev/null 2>&1
EOF

#   # 410.bwaves
#   copy_spec 410.bwaves

# cat << 'EOF' > ${BENCH_DIR}/run.sh
# #!/bin/bash
# echo $0
# ./bwaves_base.amd64 > /dev/null 2>&1
# EOF

  ## 416.gamess
  # 433.milc
  copy_spec 433.milc

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./milc_base.amd64 < su3imp.in > /dev/null 2>&1
EOF

  # 429.mcf
  copy_spec 429.mcf

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./mcf_base.amd64 inp.in > /dev/null 2>&1
EOF

  # 434.zeusmp
  copy_spec 434.zeusmp

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./zeusmp_base.amd64 > /dev/null 2>&1
EOF

  # 435.gromacs
  copy_spec 435.gromacs

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./gromacs_base.amd64 -silent -deffnm gromacs -nice 0 > /dev/null 2>&1
EOF

  # 436.cactusADM
  copy_spec 436.cactusADM

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./cactusADM_base.amd64 benchADM.par > /dev/null 2>&1
EOF

  # 437.leslie3d
  copy_spec 437.leslie3d

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./leslie3d_base.amd64 < leslie3d.in > /dev/null 2>&1
EOF

  # 444.namd
  copy_spec 444.namd

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./namd_base.amd64 --input namd.input --iterations 1 --output namd.out > /dev/null 2>&1
EOF

  # 445.gobmk
  copy_spec 445.gobmk

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./gobmk_base.amd64 --quiet --mode gtp < capture.tst > /dev/null 2>&1
./gobmk_base.amd64 --quiet --mode gtp < connect.tst > /dev/null 2>&1
./gobmk_base.amd64 --quiet --mode gtp < connect_rot.tst > /dev/null 2>&1
./gobmk_base.amd64 --quiet --mode gtp < connection.tst > /dev/null 2>&1
./gobmk_base.amd64 --quiet --mode gtp < connection_rot.tst > /dev/null 2>&1
./gobmk_base.amd64 --quiet --mode gtp < cutstone.tst > /dev/null 2>&1
./gobmk_base.amd64 --quiet --mode gtp < dniwog.tst > /dev/null 2>&1
EOF

#   # 447.dealII
#   copy_spec 447.dealII

# cat << 'EOF' > ${BENCH_DIR}/run.sh
# #!/bin/bash
# echo $0
# ./dealII_base.amd64 8 > /dev/null 2>&1
# EOF

#   # 450.soplex
#   copy_spec 450.soplex

# cat << 'EOF' > ${BENCH_DIR}/run.sh
# #!/bin/bash
# echo $0
# ./soplex_base.amd64 -m10000 test.mps > /dev/null 2>&1
# EOF

  # 453.povray
  copy_spec 453.povray

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./povray_base.amd64 SPEC-benchmark-test.ini > /dev/null 2>&1
EOF

  # 454.calculix
  copy_spec 454.calculix

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./calculix_base.amd64 -i beampic > /dev/null 2>&1
EOF

  # 456.hmmer
  copy_spec 456.hmmer

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./hmmer_base.amd64 --fixed 0 --mean 325 --num 45000 --sd 200 --seed 0 bombesin.hmm > /dev/null 2>&1
EOF

  # 458.sjeng
  copy_spec 458.sjeng

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./sjeng_base.amd64 test.txt > /dev/null 2>&1
EOF

  # 459.GemsFDTD
  copy_spec 459.GemsFDTD

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./GemsFDTD_base.amd64 > /dev/null 2>&1
EOF

  # 462.libquantum
  copy_spec 462.libquantum

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./libquantum_base.amd64 33 5 > /dev/null 2>&1
EOF

  # 464.h264ref
  copy_spec 464.h264ref

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./h264ref_base.amd64 -d foreman_test_encoder_baseline.cfg > /dev/null 2>&1
EOF

  # 465.tonto
  copy_spec 465.tonto

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./tonto_base.amd64 > /dev/null 2>&1
EOF

  # 470.lbm
  copy_spec 470.lbm

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./lbm_base.amd64 20 reference.dat 0 1 100_100_130_cf_a.of > /dev/null 2>&1
EOF

  # 471.omnetpp
  copy_spec 471.omnetpp

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
./omnetpp_base.amd64 omnetpp.ini > /dev/null 2>&1
EOF

  # 473.astar
  copy_spec 473.astar

cat << 'EOF' > ${BENCH_DIR}/run.sh
#!/bin/bash
echo $0
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
# echo $0
# ./Xalan_base.amd64 -v test.xml xalanc.xsl > /dev/null 2>&1
# EOF

  ## 481.wrf
#   # 482.sphinx3
#   DIRNAME=482.sphinx3
#   OUTDIR=${OUTPUT_DIR}/${DIRNAME}
#   EXECNAME=sphinx_livepretend_base.amd64

#   mkdir -p ${OUTDIR}
#   cp ${DIRNAME}/exe/${EXECNAME} ${OUTDIR}
#   cp -R ${DIRNAME}/data/all/input/* ${OUTDIR}
#   cp -R ${DIRNAME}/data/test/input/* ${OUTDIR}

# cat << 'EOF' > ${OUTDIR}/run.sh
# #!/bin/bash
# echo $0
# ./sphinx_livepretend_base.amd64 ctlfile . args.an4 > /dev/null 2>&1
# EOF

# cat << 'EOF' > ${OUTDIR}/ctlfile
# an406-fcaw-b.le 128000
# an407-fcaw-b.le 131200
# EOF

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
  434.zeusmp
  435.gromacs
  436.cactusADM
  437.leslie3d
  444.namd
  445.gobmk
  # 447.dealII
  # 450.soplex
  453.povray
  454.calculix
  456.hmmer
  458.sjeng
  459.GemsFDTD
  462.libquantum
  464.h264ref
  465.tonto
  470.lbm
  471.omnetpp
  473.astar
  # 482.sphinx3
  # 483.xalancbmk
)


for dir in ${LIST[@]}
do
  cd ${dir}

  echo "Running "${dir}

  LATENCY=$({ time ./run.sh; } 2>&1 | grep real | awk '{ print $2; }')

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
