f = open("./simout", 'r')

results = set()

while True:
    line = f.readline()[:-1]
    if not line:
        break
    line = line.split(": ")
    
    timestamp = int(line[0])
    func_name = line[2]
    cmd = line[5]

    results.add(cmd)
f.close()

print(results)