# Client for Coldchain workload
import os
from os import urandom, path, environ
from flask import request
from flask import Flask
from avalon_client_sdk.quorum.quorum_worker_registry_client import QuorumWorkerRegistryImpl
from avalon_client_sdk.quorum.quorum_work_invocation_impl import QuorumWorkInvocationImpl
from avalon_client_sdk.utility.hex_utils import hex_to_utf8, pretty_ids
import json
import toml
import logging
import sys
import argparse
import secrets
from web3 import Web3
from flask_cors import CORS
from flask import redirect, url_for
import requests
import asyncio
import time
import uuid
import config.config as pconfig
import utility.logger as plogger
import crypto_utils.crypto_utility as utility
from avalon_client_sdk.utility.tcf_types import WorkerType, WorkerStatus
import avalon_client_sdk.worker.worker_details as worker_details
from avalon_client_sdk.work_order.work_order_params import WorkOrderParams
from avalon_client_sdk.direct.avalon_direct_client \
    import AvalonDirectClient
from error_code.error_status import WorkOrderStatus, ReceiptCreateStatus    
import crypto_utils.signature as signature
from error_code.error_status import SignatureStatus
from flask import request, jsonify

import zmq

context = zmq.Context()
req_id = 1

logging.info("Running server...")
TCFHOME = os.environ.get("TCF_HOME", "../../")
logging.info(TCFHOME)

app = Flask(__name__)
CORS(app)
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
conf_files = [TCFHOME + "/client_sdk/avalon_client_sdk/tcf_connector.toml"]
confpaths = ["."]

try:
    config = pconfig.parse_configuration_files(conf_files, confpaths)
    json.dumps(config)
except pconfig.ConfigurationException as e:
    logger.error(str(e))
    sys.exit(-1)


@app.route('/')
def entry():
    return 'Hello, Welcome to the coldchain application'

# Register worker on blockchain
@app.route("/tcf/api/blockchain/worker",methods=["POST"])
def registerWorker():
    input = json.loads(request.data)
    eth_conn=QuorumWorkerRegistryImpl(config)
    worker_id = (input["workerId"])[:8].encode('utf-8')
    logging.info("Worker Id in bytes")
    logging.info(worker_id)
    logging.info("type of workerId object")
    logging.info(type(worker_id))
    org_id = input["orgId"].encode('utf-8')
    logging.info("Organization Id in Bytes")
    logging.info(org_id)
    logging.info("Type of orgId Object")
    logging.info(type(org_id))
    application_ids=[input["applicationId1"].encode('utf-8'),input["applicationId2"].encode('utf-8')]
    worker_type = WorkerType.TEE_SGX
    worker_api_url = input["workerUrl"]
    details=input["details"]
    logging.info("Type of details Object")
    logging.info(type(details))
    detailsInPythonStringFormat = json.dumps({"workOrderSyncUri":details})
    logging.info("Calling worker_register contract..\n worker_id: %s\n worker_type: %d\n \
        orgId: %s\n applicationIds %s\n details %s",
        hex_to_utf8(worker_id), worker_type.value,
        hex_to_utf8(org_id), pretty_ids(application_ids), detailsInPythonStringFormat)
    result = eth_conn.worker_register(worker_id, worker_type, 
        org_id, application_ids, detailsInPythonStringFormat)
    logging.info("Result")
    logging.info(result)
    logging.info("worker_register status \n{'status': %s', \n'txn_receipt': %s}", 
        result["status"],json.dumps(json.loads(Web3.toJSON(result["txn_receipt"])), indent=4))
    res=json.loads(Web3.toJSON(result["txn_receipt"]))
    return res

# Get worker Ids from blockchain
@app.route("/tcf/api/blockchain/worker",methods=["GET"])
def getWorker():
    logging.info(request)
    org_id = request.args.get("org_id")
    application_id=request.args.get("applicationId")
    logging.info(type(org_id))
    eth_conn=QuorumWorkerRegistryImpl(config)
    worker_type = WorkerType.TEE_SGX
    logging.info("Calling worker_lookup..\n worker_type: %d\n orgId: %s\n applicationId: %s",
        worker_type.value,
        hex_to_utf8(org_id.encode('utf-8')),
        hex_to_utf8(application_id.encode('utf-8')))
    result = eth_conn.worker_lookup(worker_type, org_id.encode('utf-8'), 
        application_id.encode('utf-8'))
    logging.info("worker_lookup status [%d, %s, %s]", 
        result[0], result[1], pretty_ids(result[2]))
    pretty_list = []
    for id in result[2]:
        pretty_list.append((id.decode('utf-8')).rstrip("\u0000"))
    res=json.dumps(pretty_list)
    return res

# Get Worker Details From Blockchain
@app.route("/tcf/api/blockchain/workerDetails",methods=["GET"])
def getWorkerDetails():
    worker_id = request.args.get("workerId")
    eth_conn=QuorumWorkerRegistryImpl(config)
    logging.info("Calling worker_retrieve..\n worker_id: %s", 
        hex_to_utf8(worker_id.encode('utf-8')))
    result = eth_conn.worker_retrieve(worker_id.encode('utf-8'))
    logging.info("worker_retrieve status [%d, %s, %s, %s, %s]", result[0], 
        result[1], pretty_ids(result[2]), result[3],result[4])
    logging.info("Type of details")
    logging.info(type(result[4]))
    result[1]=hex_to_utf8(result[1])
    result[2]=pretty_ids(result[2])
    return json.dumps(result)


# Function to submit work order details to blockchain
def submitWorkOrder(workOrder_id,worker_id,requester_id,workOrder_request,workOrderResponse):
    # input = json.loads(request.data)
    print(type(input))
    eth_conn = QuorumWorkInvocationImpl(config) 
    workOrder_id =workOrder_id[:8].encode('utf-8')
    worker_id = worker_id[:8].encode('utf-8')
    requester_id = requester_id[:8].encode('utf-8') # Gateway ID
    workOrder_request = str(workOrder_request)
    logging.info("Calling work Order Submit contract ...\n workOrder_id: %s\n worker_id: %s\n requester_id: %s\n workOrder_request: %s \n",hex_to_utf8(workOrder_id), hex_to_utf8(worker_id), hex_to_utf8(requester_id), workOrder_request )
    try:
        result = eth_conn.workOrder_submit(workOrder_id, worker_id, requester_id, workOrder_request)
        logging.info("#####################################################################################")
        logging.info("workOrder_submit status \n{'status': %s', \n'txn_receipt': %s}", result["status"], json.dumps(json.loads(Web3.toJSON(result["txn_receipt"])), indent=4))
        res = json.loads(Web3.toJSON(result["txn_receipt"]))
        workorderStatus=0
        logging.info("Calling workOrder conmplete..\n workOrder_id: %s\n workOrder_status: %d\n \
                WorkOrder Response %s",
                hex_to_utf8(workOrder_id), workorderStatus, workOrderResponse)
        try:
            result = eth_conn.workOrder_complete(workOrder_id, workorderStatus, workOrderResponse)
            logging.info("--------------Result------------- %s \n", result)
            res = json.loads(Web3.toJSON(result["txn_receipt"]))
            return res
        except Exception as e2:
            logging.info(e2)
            return e2
    except Exception as e:
        logging.info(e)
        return e


# Fetch workorder details from blockchain
@app.route("/tcf/api/blockchain/workOrder", methods=["GET"])
def getResult():
    workOrderId = request.args.get("workOrderId").encode('utf-8')
    eth_conn = QuorumWorkInvocationImpl(config)
    logging.info("Calling work order get result Contract ...\n workOrder_id : %s \n", hex_to_utf8(workOrderId))
    result = eth_conn.workOrder_getResult(workOrderId)
    logging.info("WorkOrder data \n{'status': % d', \n 'WorkOrder Response' : %s}",result[0],result[1])
    return json.dumps(result)


# Get worker details - directly from enclave
@app.route("/tcf/api/enclave/worker", methods=["GET"])
def getWorkers():
    req_id = 3
    direct_jrpc = AvalonDirectClient(config_file=None,config=config)
    worker_registry_instance = direct_jrpc.get_worker_registry_instance()
    worker_lookup_result = worker_registry_instance.worker_lookup(worker_type=WorkerType.TEE_SGX, id=req_id)
    logging.info("\n Worker lookup response: {}\n".format(json.dumps(worker_lookup_result, indent=4)))
    if "result" in worker_lookup_result and "ids" in worker_lookup_result["result"].keys():
        if worker_lookup_result["result"]["totalCount"] != 0:
            worker_id = worker_lookup_result["result"]["ids"][0]
            print(worker_id)
            print(type(worker_id))
            res = [{"worker_id": worker_id}]
            return json.dumps(res)
        else:
            logging.error("ERROR: No workers found")
            return "No workers Found"
            sys.exit(1)
    else:
        logging.error("ERROR: Failed to lookup worker")
        return "Failed to lookup worker"
        sys.exit(1)


def fetchWorkerObj(worker_id):
    worker_obj = worker_details.SGXWorkerDetails()
    logging.info(worker_obj)
    direct_jrpc = AvalonDirectClient(config_file=None,config=config)
    worker_registry_instance = direct_jrpc.get_worker_registry_instance()
    req_id = 9
    try:
        worker_retrieve_result= worker_registry_instance.worker_retrieve(worker_id, req_id)
    except Exception as error:
        logging.error(error)
    try:
        worker_obj.load_worker(worker_retrieve_result)
    except Exception as  error2:
        logging.error(error2)
    logging.info(worker_obj)
    return worker_obj

def evaluateWorkorder(work_order_id, urlString):
    context = zmq.Context()
    #  Socket to talk to server
    logging.info("Connecting to enclave manager")
    try:
        socket = context.socket(zmq.REQ)
        logging.info(socket)
        socket.connect(urlString)
        logging.info("Sending request")
        logging.info("request sent workorder id:")
        logging.info(work_order_id)
        socket.send_string(work_order_id, flags=0, encoding='utf-8')
        
        replymessage = socket.recv()
        logging.info("Received reply from enclave")
        logging.info(replymessage)
        replymessage= json.loads(replymessage.decode('utf-8'))
        socket.disconnect(urlString)
        return replymessage
    except Exception as er:
        logging.info("Exception in fetching socket")
        logging.error(er)  

# This function records txns in BlockChain    
def storeResultBlockchain(replymessage, worker_obj, session_key, session_iv, input):
    if replymessage:
        logging.info("Work order get result :") 
        logging.info(replymessage)
        # Decrypt the result
        in_data = input["inData"]
        work_order_id = input["workOrder_id"]
        worker_id = input["worker_id"]
        workload_id = (input["workload_id"]).encode("UTF-8").hex()
        requester_id = (input["requester_id"]).encode("UTF-8").hex()

        if "result" in replymessage:
            logging.info("inside if block")
            sig_obj = signature.ClientSignature()
            status = sig_obj.verify_signature(replymessage, worker_obj.verification_key)
            logging.info(status)
            try:
                if status == SignatureStatus.PASSED:
                    logging.info("Signature verification Successful")
                    decrypted_res = utility.decrypted_response(replymessage, session_key, session_iv)
                    print ("==============================================")
                    print (decrypted_res)
                    logging.info(type(decrypted_res))
                    finalResponseTobeStoredOnBlockchain = []
                    arr = ["Temperature", "Humidity", "Shock_alert", "Tamper_alert"]  

                    for i in range(len(decrypted_res)):
                        entry=decrypted_res[i]
                        logging.info(entry)
                        logging.info("Type of entry object")
                        logging.info(type(entry))
                        logging.info(type(entry.get('data')))
                        newData = entry.get('data')
                        if in_data[i].get('shock_alert') is True:
                            shockAlert = 0
                            newData = newData + " 0"
                        else:
                            shockAlert = 1
                            newData =  newData +" 1"
                        if in_data[i].get('tamper_alert') is True:
                            tamperAlert = 0
                            newData = newData + " 0"
                        else :
                            tamperAlert = 1
                            newData =  newData + " 1"
                            
                        listData = newData.split(" ")
                        for j in range(len(listData)) :
                            if listData[j] == '0' :
                                # These details to be sent from client -as per requirement.
                                responseEntry1 = {'Shipment ID': 'Wip-Ship_0085', 'Beacon ID': 'da21437ea06', 'Gateway ID' : 'C030011837-0085','Alert Type': arr[j] , 'Alert Value':'1', 'Alert Location' : 'Electronic City' , 'Alert Start Time (UTC)' : 'Jan 13, 2020, 10:37:53 AM', 'Alert End Time (UTC)': ' ', 'Object ID': 'Carton-2', 'Object Type': 'Carton', 'Pallet ID': 'WS-085-PL-1'}
                                finalResponseTobeStoredOnBlockchain.append(responseEntry1)
                    print ("================================================")
                    logging.info(finalResponseTobeStoredOnBlockchain)
                    responseFromBlockchainCall = submitWorkOrder(work_order_id,worker_id,requester_id,in_data,str(finalResponseTobeStoredOnBlockchain))
                    return json.dumps(decrypted_res)
                    if show_decrypted_output:
                        logging.info("\nDecrypted response:\n {}".format(decrypted_res))
                        return decrypted_res 
                else:
                    logging.info("Signature verification Failed")
                    sys.exit(1)
            except Exception as e:
                print(e)
                logging.info("ERROR: Failed to decrypt response")
                sys.exit(1)
    else :
        return "Could not decrypt the respose.Response in undecrypted format"

# createWorkOrder Function defination:
def createWorkOrder(input, session_key, session_iv):
    work_order_id = input["workOrder_id"]
    worker_id = input["worker_id"]
    workload_id = (input["workload_id"]).encode("UTF-8").hex()
    requester_id = (input["requester_id"]).encode("UTF-8").hex()
    in_data = input["inData"]
    requester_nonce = secrets.token_hex(16)
    worker_obj = fetchWorkerObj(worker_id)   
    wo_params = WorkOrderParams(
	work_order_id, worker_id, workload_id, requester_id,
	session_key, session_iv, requester_nonce,
	result_uri=" ", notify_uri=" ",
	worker_encryption_key=worker_obj.encryption_key,
	data_encryption_algorithm="AES-GCM-256"
    )
    # Add worker input data
    #global in_data
    for value in in_data:
        print(value)
        newValue = value["sensorID"] + " " + str(value["shock_alert"]) + " " + str(value["tamper_alert"]) + " " + str(value["temperature"]) + " " + str(value["humidity"])
        wo_params.add_in_data(newValue)

	# Encrypt work order request hash
    wo_params.add_encrypted_request_hash()
    requester_signature=""
    if requester_signature:
        private_key = utility.generate_signing_keys()
		# Add requester signature and requester verifying_key
        if wo_params.add_requester_signature(private_key) == False:
            logging.info("Work order request signing failed")
            exit(1)
    logging.info("Work order submit request : %s, \n \n ",wo_params.to_string())           
    direct_jrpc = AvalonDirectClient(config_file=None,config=config) 
    work_order_instance = direct_jrpc.get_work_order_instance()
    response = work_order_instance.work_order_submit( wo_params.get_work_order_id(), wo_params.get_worker_id(), wo_params.get_requester_id(), wo_params.to_string(), id=10)
    logging.info("Work order submit response : {}\n ".format(json.dumps(response, indent=4)))
    

# Submit Work Order and return a decrypted response.Check the response and make a call to blockhain.
@app.route("/tcf/api/sync/workorder", methods=["POST"])
def directSubmitWorkOrder():
    input = json.loads(request.data)
    work_order_id = input["workOrder_id"]
    worker_id = input["worker_id"]
    session_key = utility.generate_key()
    session_iv = utility.generate_iv()
    # This is config file implementaion
    conffiles = ["tcs_config.toml"]
    confpaths = [".", TCFHOME + "/" + "config"]
    try:
        config = pconfig.parse_configuration_files(conffiles, confpaths)
        json.dumps(config, indent=4)
    except pconfig.ConfigurationException as e:
        logger.error(str(e))
        sys.exit(-1)
    #host = "tcp://localhost:"
    urlString = config.get('Listener')['zmq_url'] + config.get('Listener')['zmq_port']
    logging.info(urlString)
    # This function fetch a worker from enclave
    worker_obj = fetchWorkerObj(worker_id)
    # This function creates a workOrder Request
    createWorkOrder(input, session_key, session_iv)
    # This function evaluate the workOrder request
    replymessage = evaluateWorkorder(work_order_id, urlString)
    # This functions submits result to the blockchain in case of any violations
    replyResult = storeResultBlockchain(replymessage, worker_obj, session_key, session_iv, input)
    return replyResult

#Generates random id for workOrder
@app.route("/tcf/api/workorder/generate",methods=["GET"])
def createRandomId():
    workOrderId = "0x" + uuid.uuid4().hex[:6].upper()
    return workOrderId


if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded= True)
