/* Copyright 2019 Intel Corporation
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/
#include <string>
#include <cmath>
#include "cold_chain_evaluation_logic.h"

ColdChainEvalLogic::ColdChainEvalLogic() {}

ColdChainEvalLogic::~ColdChainEvalLogic() {}

// Set your minimum and maximum temperature and humidity respectively

int TEMP_MIN = 15;
int TEMP_MAX = 50;
int HUMID_MIN = 30 ;
int HUMID_MAX = 90 ; 

template<typename Out>
void splitn(const std::string &str, char delim, Out result) {
        std::size_t current, previous = 0;

        current = str.find(delim);
        while (current != std::string::npos) {
                std::string item = str.substr(previous, current - previous);
                if (item.compare("") != 0)
                        *(result++) = item; 
                previous = current + 1;
                current = str.find(delim, previous);
        }

        std::string item = str.substr(previous, current - previous);
        if (item.compare("") != 0)
                *(result++) = item;
}

std::vector<std::string> splitn(const std::string &s, char delim) {
    std::vector<std::string> elems;
    splitn(s, delim, std::back_inserter(elems));
    return elems;
}
// Range Check function 
double ColdChainEvalLogic::model_A(double min, double max, double data) {
    double flag = 0.0;
    if (data >= min && data <=max)
        flag = 1;
    else 
        flag = 0;     
    return flag;
}
// Bollean Check Function
double ColdChainEvalLogic::model_B(bool b1) {
    if ( b1 == true)    
        return true;
    else
        return false;
}

double ColdChainEvalLogic::temperature_check(double data) {
    return model_A(TEMP_MIN, TEMP_MAX, data);
}

double ColdChainEvalLogic::humidity_check(double data) {
    return model_A(HUMID_MIN, HUMID_MAX, data);
}


std::string ColdChainEvalLogic::executeWorkOrder(std::string decrypted_user_input_str) {
    static int count = 0;

    if (decrypted_user_input_str.empty()) {
        count = 0;
        return "";
    }

    std::string resultString;
    try {
        std::string dataString;
        dataString = decrypted_user_input_str;

        std::vector<std::string> medData = splitn(dataString, ' ');
        if (medData.size() != 5)
            //return medData.size();
            return "Error with missing or incorrect input format";
        int temperature_result = temperature_check(std::stoi(medData[3]));
        int humidity_result = humidity_check(std::stoi(medData[4]));

        count++;
        // Use accumulated data to calculate the result
        if (temperature_result==1 && humidity_result==1)
            resultString = "1 1";
        else if (temperature_result==0 && humidity_result == 1)
            resultString = "0 1";
        else if (temperature_result==1 && humidity_result == 0)
            resultString = "1 0";
        else if (temperature_result == 0 && humidity_result == 0)  
            resultString = "0 0";
        else
            resultString = " There is some internal error";           
    } catch (...) {
        resultString = "Caught exception while processing workload data";
    }
    return resultString;
}
