f = open("./cxl_type2_test_logparser/example.log", 'r')

results = set()

while True:
    line = f.readline()[:-1]
    if not line:
        break
    line = line.split(": ")
    
    timestamp = int(line[0])
    func_name = line[2]
    cmd = line[4]

    results.add(cmd)
f.close()

print(results)
