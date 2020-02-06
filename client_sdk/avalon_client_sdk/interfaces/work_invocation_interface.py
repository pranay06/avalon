from abc import ABC,abstractmethod

class WorkInvocationInterface(ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def workOrder_submit(self, workeOrder_id, worker_id, requester_id, workOrder_request, id=None):
        """
        Adding a new registry
        Inputs
        1. organization_id bytes[] identifies organization that hosts the registry, 
        e.g. a bank in the consortium or anonymous entity.
        2. uri string defines a URI for this registry that supports Off-Chain Worker Registry 
        JSON RPC API.
        3. sc_addr bytes[] defines an Ethereum address that runs Worker Registry 
        Smart Contract API smart contract for this registry.
        4. app_type_ids []bytes[] is an optional parameter that defines application types 
        supported by the worker managed by the registry.
        """
        pass


    @abstractmethod
    def workOrder_complete(self, workOrder_id, workOrder_status, workOrder_response, id=None):
        """
        Update a registry
        Inputs
        1. organization_id bytes[] identifies organization that hosts the registry, 
        e.g. a bank in the consortium or anonymous entity.
        2. uri string defines a URI for this registry that supports Off-Chain Worker 
        Registry JSON RPC API.
        3. sc_addr bytes[] defines an Ethereum address that runs Worker Registry 
        Smart Contract API smart contract for this registry.
        4. application_type_ids []bytes[] is an optional parameter that defines 
        application types supported by the worker managed by the registry.
        """
        pass

    @abstractmethod
    def workOrder_getResult(self, workOrder_id, id=None):
        """
        Update a registry
        Inputs
        1. organization_id bytes[] identifies organization that hosts the registry, 
        e.g. a bank in the consortium or anonymous entity.
        2. uri string defines a URI for this registry that supports Off-Chain Worker 
        Registry JSON RPC API.
        3. sc_addr bytes[] defines an Ethereum address that runs Worker Registry 
        Smart Contract API smart contract for this registry.
        4. application_type_ids []bytes[] is an optional parameter that defines 
        application types supported by the worker managed by the registry.
        """
        pass
