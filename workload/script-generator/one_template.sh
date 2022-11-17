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

echo ${DATASET}_${SEARCH_L}_${TYPE}

BUILD_R=""
BUILD_L=""
BUILD_C=""
if [ "${DATASET}" == "gist1M" ]
then
  BUILD_R="--build-r 70"
  BUILD_L="--build-l 60"
  BUILD_C="--build-c 500"
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

# diskANN
if [ "${TYPE}" == "disk" ];
then
  BINARY=test_diskann
  CACHE_BUDGET_MB="--cache-budget-mb 128"
fi

# distributed
if [ "${TYPE}" == "distributed" ];
then
  GRAPH_LOCATION="--graph-location host"
  EMBEDDING_LOCATION="--embedding-location host"
  SHARD="--shard distributed"
  NUM_SHARD="--num-shard 5"
fi

# enable cxl
if [[ " ${BASE_LIST[*]} " =~ " ${TYPE} " ]];
then
  GRAPH_LOCATION="--graph-location cxl"
  EMBEDDING_LOCATION="--embedding-location cxl"
  DEVICE_NAME="--device-name jh"
  SHARD="--shard column"
  NUM_SHARD="--num-shard 4"
  DEVICE_IDS="--device-ids 1 2 3 4"
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
  CACHE_BUDGET_MB="--cache-budget-mb 128"
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
fi

mount /dev/sdb1 /root/mnt

/root/mnt/${BINARY} \
  ${DATASET_ROOT}/${DATASET} ${INDEX_ROOT} \
  ${BUILD_R} \
  ${BUILD_L} \
  ${BUILD_C} \
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

m5 exit

