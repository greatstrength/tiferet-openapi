'''Tiferet OpenAPI Request Context'''

# *** imports

# ** core
from typing import Any

# ** infra
from pydantic import BaseModel
from tiferet.contexts.request import RequestContext


# *** contexts

# ** context: open_api_request_context
class OpenApiRequestContext(RequestContext):
    '''
    A context for handling OpenAPI request data and responses with Pydantic model serialization.
    '''

    # * method: handle_response
    def handle_response(self) -> Any:
        '''
        Handle the response for the OpenAPI request context.

        :return: The response.
        :rtype: Any
        '''

        # Set the result using the set_result method to ensure proper formatting.
        self.set_result(self.result)

        # Handle the response using the parent method.
        return super().handle_response()

    # * method: set_result
    def set_result(self, result: Any, data_key: str = None):
        '''
        Set the result of the request context.

        :param result: The result to set.
        :type result: Any
        :param data_key: The key in the request data to set the result to.
            If provided, the raw result is stored for downstream commands.
            If None, the result is serialized for the final response.
        :type data_key: str
        '''

        # If a data key is provided, delegate to the parent to store the raw result.
        if data_key:
            super().set_result(result, data_key=data_key)
            return

        # If the response is None, return an empty response.
        if result is None:
            self.result = ''

        # Convert the response to a dictionary if it's a BaseModel.
        elif isinstance(result, BaseModel):
            self.result = result.model_dump()

        # If the response is a list containing BaseModel instances, convert each to a dictionary.
        elif isinstance(result, list) and all(isinstance(item, BaseModel) for item in result):
            self.result = [item.model_dump() for item in result]

        # If the response is a dict containing BaseModel instances, convert each to a dictionary.
        elif isinstance(result, dict) and all(isinstance(value, BaseModel) for value in result.values()):
            self.result = {key: value.model_dump() for key, value in result.items()}

        # Otherwise, set the result directly.
        else:
            self.result = result