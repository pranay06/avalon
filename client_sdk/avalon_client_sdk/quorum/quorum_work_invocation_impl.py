# Copyright 2019 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import binascii
import json
import logging
from os import environ
from os.path import exists, realpath

from eth_utils.hexadecimal import is_hex

from avalon_client_sdk.utility.tcf_types import WorkerStatus, WorkerType
from avalon_client_sdk.quorum.quorum_wrapper import QuorumWrapper
from avalon_client_sdk.interfaces.work_invocation_interface import WorkInvocationInterface
from avalon_client_sdk.utility.utils import construct_message, validate_details

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

class QuorumWorkInvocationImpl(WorkInvocationInterface):
    """
    Implements WorkerRegistryInterface interface
    Detail method description will be available in interface
    """

    def __init__(self, config):
        if self.__validate(config) is True:
            self.__initialize(config)
        else:
            raise Exception("Invalid configuration parameter")

    def workOrder_submit(self, workOrder_id, worker_id, requester_id, workOrder_request):
        """
        Registry new worker with details of worker
        """
        if (self.__contract_instance != None):
            if not is_hex(binascii.hexlify(worker_id).decode("utf8")):
                logging.info("Invalid worker id {}".format(worker_id))
                return construct_message("failed", "Invalid worker id {}".format(worker_id))
            if not is_hex(binascii.hexlify(workOrder_id).decode("utf8")):
                logging.info("Invalid workOrder id {}".format(workOrder_id))
                return construct_message("failed", "Invalid workerType {}".format(workeOrder_id))
            if not is_hex(binascii.hexlify(requester_id).decode("utf8")):
                logging.info("Invalid Requester id {}".format(requester_id))
                return construct_message("failed", "Invalid oRequester id {}".format(requester_id))

            txn_hash = self.__contract_instance.functions.workOrderSubmit(workOrder_id, worker_id, requester_id, workOrder_request).buildTransaction(
            {
                "chainId": self.__eth_client.get_channel_id(),
                "gas": self.__eth_client.get_gas_limit(),
                "gasPrice": self.__eth_client.get_gas_price(),
                "nonce": self.__eth_client.get_txn_nonce()
            })
            tx = self.__eth_client.execute_transaction(txn_hash)
            return tx
        else:
            logging.error("Submit registry contract instance is not initialized")
            return construct_message("failed", "Submit contract instance is not initialized")


    def workOrder_complete(self, workOrder_id, workOrder_status, workOrder_response):
        """
        Set the registry status identified by worker id
        status is worker type enum type
        """
        if (self.__contract_instance != None):
            if not is_hex(binascii.hexlify(workOrder_id).decode("utf8")):
                logging.info("Invalid work Order Id {}".format(workOrder_id))
                return construct_message("failed", "Invalid worke Order id {}".format(workeOrder_id))
            # if not is_hex(binascii.hexlify(workOrder_status).decode("utf8")):
            #     logging.info("Invalid workOrder status {}".format(workOrder_status))
            #     return construct_message("failed", "Invalid worker status {}".format(workOrder_status))
            txn_hash = self.__contract_instance.functions.workOrderComplete(workOrder_id,
                workOrder_status, workOrder_response).buildTransaction(
                {
                    "chainId": self.__eth_client.get_channel_id(),
                    "gas": self.__eth_client.get_gas_limit(),
                    "gasPrice": self.__eth_client.get_gas_price(),
                    "nonce": self.__eth_client.get_txn_nonce()
                })
            tx = self.__eth_client.execute_transaction(txn_hash)
            return tx
        else:
            logging.error("workOrder_complete contract instance is not initialized")
            return construct_message("failed", "workeOrder_complete contract instance is not initialized")

    def workOrder_getResult(self, workOrder_id):
        """
        Lookup a worker identified worker_type, org_id and application_id
        all fields are optional and if present condition should match for all
        fields. If none passed it should return all workers.
        """
        if (self.__contract_instance != None):
            if not is_hex(binascii.hexlify(workOrder_id).decode("utf8")):
                logging.info("Invalid workOrder id {}".format(workOrder_id))
                return construct_message("failed", "Invalid workOrder id {}".format(workOrder_id))

            workOrderDetails = self.__contract_instance.functions.workOrderGetResult(workOrder_id).call()
            return workOrderDetails
        else:
            logging.error("work_Order_get_Result contract instance is not initialized")
            return construct_message("failed", "work_Order_get_Result contract instance is not initialized")
      
    def __validate(self, config):
        """
        validates parameter from config parameters for existence.
        Returns false if validation fails and true if it success
        """
        if config["quorum"]["workOrder_contract_file"] is None:
            logging.error("Missing work Order Contract file path!!")
            return False
        if config["quorum"]["workOrder_contract_contract_address"] is None:
            logging.error("Missing work Order contract address!!")
            return False
        return True
 
    def __initialize(self, config):
        """
        Initialize the parameters from config to instance variables.
        """
        self.__eth_client = QuorumWrapper(config)
        tcf_home = environ.get("TCF_HOME", "../../../")
        contract_file_name = tcf_home + "/" + \
            config["quorum"]["workOrder_contract_file"]
        contract_address = config["quorum"]["workOrder_contract_contract_address"]
        self.__contract_instance = self.__eth_client.get_contract_instance(
            contract_file_name, contract_address
        )
