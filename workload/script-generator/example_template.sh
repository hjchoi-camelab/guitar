#!/bin/bash

# substitutions
DATASET=%{DATASET}
SEARCH_L=%{SEARCH_L}
ENABLE_NDP=%{ENABLE_NDP}

# script to execute
DATASET_ROOT=/root/anns-dataset
INDEX_ROOT=/root/git/anns/faiss-experiments/index
GRAPH_LOCATION=cxl
EMBEDDING_LOCATION=cxl
DATASET_MODE=zerocopy
NUM_QUERY=10
SHARD=column
NUM_SHARD=4
DEVICE_IDS="1 2 3 4"
NDP_INTERFACE=dma-one
PREFETCH=
CACHE_BUDGET_MB=
QUERY_DEPTH=

mount /dev/sdb1 /root/mnt

/root/mnt/test_nsg \
  ${DATASET_ROOT}/${DATASET} ${INDEX_ROOT} \
  --graph-location ${GRAPH_LOCATION} \
  --embedding-location ${EMBEDDING_LOCATION} \
  --dataset-mode ${DATASET_MODE} \
  --device-name jh \
  --search-l ${SEARCH_L} \
  --num-query ${NUM_QUERY} \
  --shard ${SHARD} \
  --num-shard ${NUM_SHARD} \
  --device-ids ${DEVICE_IDS} \
  ${ENABLE_NDP} \
  ${NDP_INTERFACE} \
  ${PREFETCH} \
  ${CACHE_BUDGET_MB} \
  ${QUERY_DEPTH} \


m5 exit
