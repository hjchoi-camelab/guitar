#!/bin/bash

# substitutions
DATASET=%{DATASET}
GRAPH_LOCATION=%{GRAPH_LOCATION}

# script to execute
DATASET_ROOT=/root/anns-dataset
INDEX_ROOT=/root/git/anns/faiss-experiments/index

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
  ${QUERY_DEPTH} \
  ${NDP_INTERFACE}


/root/mnt/test_nsg \
    /root/anns-dataset/sift10K \
    /root/git/anns/faiss-experiments/index \
    --dataset-mode zerocopy \
    --embedding-location cxl \
    --graph-location cxl \
    --device-name jh \
    --search-l 16 \
    --num-query 32 \
    --shard none \
    --num-shard 1 \
    --device-ids 0

umount /root/mnt

m5 exit
