'''Tiferet OpenAPI Request/Response Domain Objects'''

# *** imports

# ** infra
from pydantic import Field

# ** app
from tiferet import DomainObject


# *** models

# ** model: api_request_model
class ApiRequestModel(DomainObject):
    '''
    Base request model for OpenAPI documentation.

    Application-level request models extend this class to define
    route-specific input schemas. Since DomainObject extends
    pydantic.BaseModel, these models integrate with FastAPI's
    native Pydantic model support for automatic Swagger schema
    generation.
    '''
    pass


# ** model: api_response_model
class ApiResponseModel(DomainObject):
    '''
    Base response model for OpenAPI documentation.

    Application-level response models extend this class to define
    route-specific output schemas.
    '''
    pass


# ** model: api_error_response
class ApiErrorResponse(DomainObject):
    '''
    Standard error response model for OpenAPI error documentation.
    '''

    # * attribute: error
    error: str = Field(
        ...,
        description='The error name.',
    )

    # * attribute: message
    message: str = Field(
        ...,
        description='The error message.',
    )
