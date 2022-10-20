import os
import csv
from multiprocessing import Pool
import pandas as pd
import gzip

ZIP = True

DIRECTORY = '/home/hjchoi/result/anns/sift1M/CXL'
FILE = ''
if ZIP:
    FILE = 'debug.log.gz'
else:
    FILE = 'debug.log.gz.log'

COLUMNS = [
    'l1rreq',
    'l2Brreq',
    'l2rreq',
    'MBrreq',
    'RPsreq',
    'T3sreq',
    'Msres',
    'T3sres',
    'RPsres',
    'MBrres',
    'l2rres',
    'l2sres',
    'l2Brres',
    'l1rres',
    'l1sres',
    'end',
]

CACHE_MISS_COLUMNS = [
    'l1rreq',
    'l2Brreq',
    'l2rreq',
    'MBrreq',
    'l2sres',
    'l2Brres',
    'l1rres',
    'l1sres',
    'end',
]

MEMORY_COLUMNS = ['Msres']

CXL_IP_COLUMNS = [
    'RPsreq',
    'T3sreq',
    'T3sres',
    'RPsres',
    'MBrres',
    'l2rres',
]

stages = zip(COLUMNS, [range(len(COLUMNS))])

delete_cmd = [
    'CleanEvict',
    'WritebackDirty',
    'CxlWritebackDirty',
    'CxlWriteResp',
]

SUM_COLUMNS = [
    'L1',
    'L2',
    'miss',
    'total',
    'cache_miss',
    'cxl_ip',
    'memory',
    'l1rreq',
    'l2Brreq',
    'l2rreq',
    'MBrreq',
    'RPsreq',
    'T3sreq',
    'Msres',
    'T3sres',
    'RPsres',
    'MBrres',
    'l2rres',
    'l2sres',
    'l2Brres',
    'l1rres',
    'l1sres',
    'end',
]
OUT_COLUMNS = ['search_l', 'mem_size', 'query_num'] + SUM_COLUMNS


def parsing(file_full_name):
    path = file_full_name[0]
    file = file_full_name[1]

    tmp_results = {}
    sum_list = []
    start_flag = False
    l1_sum = 0
    l2_sum = 0
    miss_sum = 0
    cache_miss_sum = 0
    cxl_ip_sum = 0
    memory_sum = 0
    miss_sum_dict = dict.fromkeys(COLUMNS, 0)
    output = path.split('/')[-1]
    print(f'START\t\t{path}/{file}')
    f = 0
    if ZIP:
        f = gzip.open(f'{path}/{file}')
        csv_f = open(f'{DIRECTORY}/{output}_distance_calculation.csv', 'w', newline='')
        wr = csv.writer(csv_f)
        wr.writerow(SUM_COLUMNS)
    else:
        f = open(f'{path}/{file}')
    for line in f:
        if ZIP:
            line = line.decode()
        row = line[:-1].split(': ')
        if row[2] == "m5sum":
            if miss_sum != 0:
                cache_miss_sum = 0
                cxl_ip_sum = 0
                memory_sum = 0

                for key in CACHE_MISS_COLUMNS:
                    cache_miss_sum += miss_sum_dict[key]
                for key in CXL_IP_COLUMNS:
                    cxl_ip_sum += miss_sum_dict[key]
                for key in MEMORY_COLUMNS:
                    memory_sum += miss_sum_dict[key]

                if ZIP:
                    wr.writerow([
                            l1_sum,
                            l2_sum,
                            miss_sum,
                            l1_sum + l2_sum + miss_sum,
                            cache_miss_sum,
                            cxl_ip_sum,
                            memory_sum
                        ] + [miss_sum_dict[key] for key in miss_sum_dict]
                    )
                else:
                    sum_dict = {
                        'L1': l1_sum,
                        'L2': l2_sum,
                        'miss': miss_sum,
                        'total': l1_sum + l2_sum + miss_sum,
                        'cache_miss': cache_miss_sum,
                        'cxl_ip': cxl_ip_sum,
                        'memory': memory_sum
                    }
                    sum_dict.update(miss_sum_dict)
                    sum_list.append(sum_dict)

            tmp_results = {}
            l1_sum = 0
            l2_sum = 0
            cxl_ip_sum = 0
            miss_sum = 0
            miss_sum_dict = dict.fromkeys(COLUMNS, 0)
            continue

        if row[2] == "BREAKDOWN START":
            start_flag = True
            continue

        if row[2] == "BREAKDOWN END":
            start_flag = False
            continue

        if not start_flag:
            continue

        stage = row[2]
        addr = int(row[3], 16)
        timestamp = int(row[4])
        cmd = row[5]

        if cmd in delete_cmd:
            continue

        if stage == 'l1rreq':
            tmp_results[addr] = {stage: timestamp}
        elif stage == 'end':
            tmp_results[addr][stage] = timestamp
            tmp_result = tmp_results.pop(addr, None)
            prev_timestamp = 0
            total_time = 0

            for stage in COLUMNS:
                if stage not in tmp_result:
                    tmp_result[stage] = 0
                    continue
                if prev_timestamp == 0:
                    prev_timestamp = tmp_result[stage]
                    tmp_result[stage] = 0
                    continue
                cur_timestamp = tmp_result[stage]
                tmp_result[stage] = cur_timestamp - prev_timestamp
                prev_timestamp = cur_timestamp
                total_time += tmp_result[stage]

            tmp_result['total'] = total_time
            tmp_result['addr'] = addr
            if tmp_result['l2Brreq'] == 0:
                # L1 hit
                tmp_result['type'] = 0
                l1_sum += total_time
            elif tmp_result['Msres'] == 0:
                # L2 hit
                tmp_result['type'] = 1
                l2_sum += total_time
            else:
                # LLC miss
                tmp_result['type'] = 2
                miss_sum += total_time

                for stage in COLUMNS:
                    miss_sum_dict[stage] += tmp_result[stage]

        else:
            if addr not in tmp_results:
                continue
            tmp_results[addr][stage] = timestamp

    f.close()
    print(f'PARSING END\t{path}/{file}')
    if ZIP:
        csv_f.close()
    else:
        df = pd.DataFrame(sum_list, columns=SUM_COLUMNS).astype(int)
        mean = output.split('_')
        mean.append(len(sum_list))
        mean.extend(df.mean().values.tolist())

        df.to_csv(f'{DIRECTORY}/{output}_distance_calculation.csv', index=False)
        df.to_excel(f'{DIRECTORY}/{output}_distance_calculation.xlsx', index=False)
        print(f'WRITE END\t{path}/{file}')

        return mean


if __name__ == '__main__':
    # pool input
    file_full_names = []
    for (path, dir, files) in os.walk(DIRECTORY):
        for file in files:
            if file != FILE:
                continue
            file_full_names.append((path, file))

    # multiprocessing
    with Pool(6) as p:
        if ZIP:
            p.map(parsing, file_full_names)
        else:
            out_row_list = p.map(parsing, file_full_names)

    # generate mean file
    if ZIP:
        output = DIRECTORY.split('/')[-1] + '_distance_calculation'
        out_list = []
        for (path, dir, files) in os.walk(DIRECTORY):
            for f in files:
                if path[-3:] != 'CXL':
                    continue
                if f[-24:] != 'distance_calculation.csv':
                    continue
                print(f"{path}/{f}")
                search_l = int(f.split('_')[0])
                memory_size = f.split('_')[1]

                csv_data = pd.read_csv(f"{path}/{f}")
                mean = csv_data.mean().to_frame().T
                mean['search_l'] = search_l
                mean['memory_size'] = memory_size
                print(mean)

                out_list.append(mean)

        df = pd.concat(out_list, axis=0, ignore_index=True)
        df.sort_values(["search_l"],
            axis=0,
            ascending=[True],
            inplace=True)
        print(f'\n{DIRECTORY}/{output}')
        print(df)

        df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
        df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)
    else:
        output = DIRECTORY.split('/')[-1]
        df = pd.DataFrame(out_row_list, columns=OUT_COLUMNS)
        df['search_l'] = df['search_l'].astype(int)
        df.sort_values(["search_l"],
            axis=0,
            ascending=[True],
            inplace=True)
        print(f'\n{DIRECTORY}/{output}')
        print(df)

        df.to_csv(f'{DIRECTORY}/{output}_distance_calculation.csv', index=False)
        df.to_excel(f'{DIRECTORY}/{output}_distance_calculation.xlsx', index=False)
