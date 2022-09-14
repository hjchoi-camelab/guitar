#include <unordered_set>
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
    std::stringstream logStream;
    std::string logString;

    size_t start = 0;
    size_t end = 0;
    std::string_view delimiter = ": ";
    size_t delLen = delimiter.length();
    std::string_view lastDelimiter = "\n";

    std::string_view cmdStirng;
    std::unordered_set <string> cmdSet;

    char *logPath = nullptr;

    if (argc != 2) {
        std::cerr << "Invalid number of arguments." << std::endl;
        std::cerr << argv[0] << " <log file>" << std::endl;
        return 1;
    }

    logPath = argv[1];
    logF.open(logPath);
    if (!logF.is_open()) {
        std::cerr << "Failed to open log file." << std::endl;
        return 1;
    }

    std::cout << "Begin parsing." << std::endl;

    logStream << logF.rdbuf();
    logString = logStream.str();
    std::string_view logView(logString.c_str(), logString.size());

    while (true) {
        start = logView.find(delimiter);
        start = logView.find(delimiter, start + delLen);
        start = logView.find(delimiter, start + delLen);
        start = logView.find(delimiter, start + delLen);

        start = start + delLen;
        end = logView.find(lastDelimiter, start);
        cmdStirng = logView.substr(start, end);
        start = end + 1;

        cmdSet.insert(cmdStirng);

        if (start >= logString.size()) {
            break;
        }
    }

    for (auto iter = cmdStirng.begin(); iter != cmdStirng.end(); iter++)
        std::cout << (*iter) << std::endl;

    logF.close();
    return 0;
}