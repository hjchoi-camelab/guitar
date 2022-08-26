#include <map>
#include <vector>
#include <iostream>
#include <fstream>
#include <sstream>
#include <numeric>
#include <cstdlib> 
#include <string>
#include <string_view>

int main(int argc, char *argv[]) {
    std::ifstream logF;
    std::ofstream csvF;
    std::stringstream logStream;
    std::string logString;

    size_t oddPos = 0;
    size_t evenPos = 0;
    std::string_view delimiter = ": ";
    std::string_view lastDelimiter = "\n";

    uint64_t timestamp;
    std::string_view objName;
    std::string_view stage;
    std::string_view pktId;
    std::string_view pktAddr;
    std::string_view pktCmd;

    std::map<std::string_view, std::vector<uint64_t>> tmpResults;

    char *logPath = nullptr;
    char *csvPath = nullptr;

    if (argc != 3) {
        std::cerr << "Invalid number of arguments." << std::endl;
        std::cerr << argv[0] << " <log file> <csv output file>" << std::endl;
        return 1;
    }

    logPath = argv[1];
    csvPath = argv[2];

    logF.open(logPath);
    csvF.open(csvPath, std::ofstream::out | std::ofstream::trunc);

    if (!logF.is_open()) {
        std::cerr << "Failed to open log file." << std::endl;
        return 1;
    }

    csvF << "Start Time,Downstream Link,Device to Controller,Memory Controller,Upstream Link,Latency,Address" << std::endl;

    std::cout << "Begin parsing." << std::endl;

    logStream << logF.rdbuf();
    logString = logStream.str();
    std::string_view logView(logString.c_str(), logString.size());

    while (true) {
        oddPos = logView.find_first_of("0123456789", oddPos);
        evenPos = logView.find(delimiter, oddPos+1);
        timestamp = std::strtoull(std::string( \
            logView.substr(oddPos, evenPos-oddPos)).c_str(), NULL, 10);
        evenPos +=2;

        oddPos = logView.find(delimiter, evenPos+1);
        // objName = logView.substr(evenPos, oddPos-evenPos);
        oddPos +=2;

        evenPos = logView.find(delimiter, oddPos+1);
        stage = logView.substr(oddPos, evenPos-oddPos);
        evenPos +=2;

        oddPos = logView.find(delimiter, evenPos+1);
        // pktId = logView.substr(evenPos, oddPos-evenPos);
        oddPos +=2;

        evenPos = logView.find(delimiter, oddPos+1);
        pktAddr = logView.substr(oddPos, evenPos-oddPos);
        evenPos +=2;

        oddPos = logView.find(lastDelimiter, evenPos+1);
        // pktCmd = logView.substr(evenPos, oddPos-evenPos);
        oddPos +=1;

        if (stage.compare("rpReq") == 0) {
        // start
            std::vector<uint64_t> timestamps;
            tmpResults[pktAddr] = timestamps;
            tmpResults[pktAddr].emplace_back(timestamp);
        } else if (stage.compare("rpResp") == 0) {
        // end
            auto tmpResult = std::move(tmpResults[pktAddr]);
            tmpResults.erase(pktAddr);

            uint64_t latency = timestamp - tmpResult.front();
            tmpResult.emplace_back(timestamp);
            std::adjacent_difference(tmpResult.begin(), tmpResult.end(), tmpResult.begin());

            for (auto i : tmpResult) {
                csvF << i << ",";
            }
            csvF << latency << ",";
            csvF << pktAddr << std::endl;
        } else {
        // middle
            tmpResults[pktAddr].emplace_back(timestamp);
        }

        if (oddPos >= logString.size()) {
            break;
        }
    }

    logF.close();
    csvF.close();
    return 0;
}