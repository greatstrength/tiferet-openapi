'''Tiferet OpenAPI Context Test Support Models'''

# *** imports

# ** infra
from pydantic import BaseModel

# *** models

# ** model: spec_request_model
class SpecRequestModel(BaseModel):
    '''
    Request payload model used to verify generated request schemas.
    '''

    # * attribute: amount
    amount: int

# ** model: spec_response_model
class SpecResponseModel(BaseModel):
    '''
    Response payload model used to verify generated response schemas.
    '''

    # * attribute: result
    result: int
