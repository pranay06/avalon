pragma solidity >=0.4.0;

contract WorkOrder {
    // To store the contractor owner
    address private contractOwner;
    // Total number of workerOrders
    uint256 private workOrdersCount;
    //Version number of the Api
    uint256 private version;
    // Map of workOrder identified by key workOrderId
    mapping(bytes32 => WorkOrderInfo) private workOrdersMap;
    // Map of index to workOrderId
    mapping(uint256 => bytes32) private workOrderList;

    constructor() public {
        contractOwner = msg.sender;
        workOrdersCount = 0;
        ///Set version number here
        version = 1;
    }
    //-----------------Enum Definitions-------------------
    //errorCode is an error code, 0 - success, otherwise an error.
    enum ErrorCode {Success, Error}
    enum WorkOrderStatus {Complete, Processing, Error}
    struct WorkOrderInfo {
        bytes32 workOrderId;
        bytes32 requesterId;
        address requesterAddress;
        WorkOrderStatus workOrderStatus;
        string workOrderResponse;
        bytes32 workerServiceId;
        bytes32 workerId;
        bytes32 receiptId;
    }
    struct Receipt {
        uint32 receiptCreateStatus;
        bytes workOrderRequestHash;
        uint32 currentReceiptStatus;
    }

    //----------------------Event Definitions-------------------
    event workOrderNew(
        bytes32 indexed workOrderId,
        bytes32 indexed requesterId,
        address senderAddress,
        string workOrderRequest,
        bytes32 indexed workerId,
        ErrorCode errorCode
    );

    event workOrderDone(
        bytes32 workOrderId,
        bytes32 requesterId,
        WorkOrderStatus workOrderStatus,
        string workOrderResponse,
        ErrorCode errorCode
    );

    event encryptionKeySet(
        bytes32 indexed workerId,
        bytes32 tag,
        bytes32 nonce,
        bytes signature,
        uint32 errorCode
    );

    //-------------------------Function definitions----------------------------

    //Restrict call from authorised requester
    function onlyRequester(address requester) internal view returns (bool) {
        if (msg.sender == requester) {
            return true;
        } else {
            return false;
        }
    }

    // This function is called to submit a new workorder
    function workOrderSubmit(
        bytes32 workOrderId,
        bytes32 requesterId,
        bytes32 workerId,
        string memory workOrderRequest
    ) public returns (ErrorCode err) {
        require(workOrderId.length != 0, "Empty work Order id");
        // Check if work Order already submitted, if yes then do not add
        WorkOrderInfo storage workOrder = workOrdersMap[workOrderId];
        ErrorCode error = ErrorCode.Error;
        if (workOrder.workOrderId == workOrderId) {
            return error;
        } else {
            // Insert to workersMap with worker id as key and workerInfo as value
            workOrdersMap[workOrderId] = WorkOrderInfo(
                workOrderId,
                requesterId,
                msg.sender,
                WorkOrderStatus.Processing,
                "No response generated yet",
                0,
                workerId,
                0
            );
            // Insert to workersList with current workersCount as key and workerId as value.
            workOrderList[workOrdersCount] = workerId;
            // Increment work order count
            workOrdersCount++;
            error = ErrorCode.Success;
        }
        emit workOrderNew(
            workOrderId,
            requesterId,
            msg.sender,
            workOrderRequest,
            workerId,
            ErrorCode.Success
        );
    }

    //To be invoked by Worker or Worker Service Address
    //This function is called by the Worker Service to complete a Work Order successfully or in error
    function workOrderComplete(
        bytes32 workOrderId,
        uint16 status,
        string memory workOrderResponse
    ) public returns (ErrorCode error) {
        require(
            onlyRequester(workOrdersMap[workOrderId].requesterAddress) == true,
            "You are not authorized to perform this operation"
        );
        require(workOrderId.length != 0, "Empty workOrder Id");
        WorkOrderInfo storage workOrderDetails = workOrdersMap[workOrderId];
        ErrorCode er = ErrorCode.Error;
        if (workOrderDetails.workOrderId != workOrderId) {
            return er;
        } else {
            if (status == 0) {
                er = ErrorCode.Success;
                workOrderDetails.workOrderResponse = workOrderResponse;
                workOrderDetails.workOrderStatus = WorkOrderStatus.Complete;
            } else {
                er = ErrorCode.Success;
                workOrderDetails.workOrderResponse = workOrderResponse;
                workOrderDetails.workOrderStatus = WorkOrderStatus.Error;
            }
        }
        emit workOrderDone(
            workOrderId,
            workOrderDetails.requesterId,
            workOrderDetails.workOrderStatus,
            workOrderDetails.workOrderResponse,
            er
        );
        return er;

    }

    //Fetch workorder result
    function workOrderGetResult(bytes32 workOrderId)
        public
        view
        returns (WorkOrderStatus status, string memory workOrderResponse)
    {
        require(
            onlyRequester(workOrdersMap[workOrderId].requesterAddress) == true,
            "You are not authorized to perform this operation"
        );
        WorkOrderInfo storage details = workOrdersMap[workOrderId];
        return (details.workOrderStatus, details.workOrderResponse);

    }

}
