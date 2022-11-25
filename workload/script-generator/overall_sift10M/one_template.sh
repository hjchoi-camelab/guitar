#!/bin/bash
set -x

# TYPE list
BASE_LIST=( "base" "ndp" "cache" "nearest" "infinite" )
NDP_LIST=( "ndp" "cache" "nearest" "infinite" )
CACHE_LIST=( "cache" "nearest" )
NEAREST_LIST=( "nearest" )

# substitutions
DATASET=%{DATASET}
SEARCH_L=%{SEARCH_L}
TYPE=%{TYPE}
CACHE_BUDGET=%{CACHE_BUDGET}
export OMP_NUM_THREADS=%{OMP_NUM_THREADS}
export OMP_DISPLAY_ENV=VERBOSE

echo ${DATASET}_${SEARCH_L}_${TYPE}

if [ "${DATASET}" == "sift1M" ]
then
  BUILD_R=50
  BUILD_L=40
  BUILD_C=500
elif [ "${DATASET}" == "gist1M" ]
then
  BUILD_R=70
  BUILD_L=60
  BUILD_C=500
elif [ "${DATASET}" == "sift10M" ]
then
  BUILD_R=100
  BUILD_L=60
  BUILD_C=500
else
  BUILD_R=-1
  BUILD_L=-1
  BUILD_C=-1
fi

# script to execute
BINARY=test_nsg
DATASET_ROOT=/root/anns-dataset
INDEX_ROOT=/root/git/anns/faiss-experiments/index
DATASET_MODE=zerocopy
NUM_QUERY=10
GRAPH_LOCATION=""
EMBEDDING_LOCATION=""
DEVICE_NAME=""
SHARD=""
NUM_SHARD=""
DEVICE_IDS=""
ENABLE_NDP=""
NDP_INTERFACE=""
PREFETCH=""
CACHE_BUDGET_MB=""
QUERY_DEPTH=""
GRAPH_TYPE=""

# diskANN
if [ "${TYPE}" == "disk" ];
then
  BINARY=test_diskann
  CACHE_BUDGET_MB="--cache-budget-mb ${CACHE_BUDGET}"
fi

# distributed
if [ "${TYPE}" == "distributed" ];
then
  GRAPH_LOCATION="--graph-location host"
  EMBEDDING_LOCATION="--embedding-location host"
  SHARD="--shard distributed"
  NUM_SHARD="--num-shard 3"
fi

# enable cxl
if [[ " ${BASE_LIST[*]} " =~ " ${TYPE} " ]];
then
  GRAPH_LOCATION="--graph-location cxl"
  EMBEDDING_LOCATION="--embedding-location cxl"
  DEVICE_NAME="--device-name jh"
  SHARD="--shard column"
  NUM_SHARD="--num-shard 8"
  DEVICE_IDS="--device-ids 0 1 2 3 4 5 6 7"
fi

# enable ndp
if [[ " ${NDP_LIST[*]} " =~ " ${TYPE} " ]];
then
  ENABLE_NDP="--enable-ndp"
  NDP_INTERFACE="--ndp-interface dma-one"
fi

# cache & prefetch
if [[ " ${CACHE_LIST[*]} " =~ " ${TYPE} " ]];
then
  PREFETCH="--prefetch 1"
  CACHE_BUDGET_MB="--cache-budget-mb ${CACHE_BUDGET}"
  GRAPH_TYPE="--graph-type cacheline"
fi

# query detph
if [[ " ${NEAREST_LIST[*]} " =~ " ${TYPE} " ]];
then
  QUERY_DEPTH="--query-depth 2"
fi

# infinite memory
if [ "${TYPE}" == "infinite" ];
then
  GRAPH_LOCATION="--graph-location host"
  EMBEDDING_LOCATION="--embedding-location cxl"
  PREFETCH="--prefetch 1"
  GRAPH_TYPE="--graph-type cacheline"
fi

mount /dev/sdb1 /root/mnt

/root/mnt/${BINARY} \
  ${DATASET_ROOT}/${DATASET} ${INDEX_ROOT} \
  --build-r ${BUILD_R} \
  --build-l ${BUILD_L} \
  --build-c ${BUILD_C} \
  --dataset-mode ${DATASET_MODE} \
  --search-l ${SEARCH_L} \
  --num-query ${NUM_QUERY} \
  ${GRAPH_LOCATION} \
  ${EMBEDDING_LOCATION} \
  ${SHARD} \
  ${NUM_SHARD} \
  ${DEVICE_NAME} \
  ${DEVICE_IDS} \
  ${ENABLE_NDP} \
  ${NDP_INTERFACE} \
  ${PREFETCH} \
  ${CACHE_BUDGET_MB} \
  ${QUERY_DEPTH} \
  ${GRAPH_TYPE}

m5 exit

