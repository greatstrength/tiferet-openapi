'''Tiferet OpenAPI Request/Response Domain Object Tests'''

# *** imports

# ** infra
import pytest
from pydantic import Field, ValidationError

# ** app
from ..request import ApiRequestModel, ApiResponseModel, ApiErrorResponse


# *** tests

# ** test: api_request_model_extensible
def test_api_request_model_extensible() -> None:
    '''
    Test that ApiRequestModel can be extended with custom fields.
    '''

    # Define a custom request model.
    class AddNumberRequest(ApiRequestModel):
        '''Custom request model for addition.'''
        a: float = Field(..., description='First operand.')
        b: float = Field(..., description='Second operand.')

    # Instantiate the custom request model.
    request = AddNumberRequest(a=1.5, b=2.5)

    # Verify the fields.
    assert request.a == 1.5
    assert request.b == 2.5


# ** test: api_request_model_forbids_extra
def test_api_request_model_forbids_extra() -> None:
    '''
    Test that ApiRequestModel rejects unknown fields (extra='forbid').
    '''

    # Define a custom request model.
    class SimpleRequest(ApiRequestModel):
        '''A simple request model.'''
        name: str = Field(..., description='A name.')

    # Attempt to instantiate with an extra field.
    with pytest.raises(ValidationError):
        SimpleRequest(name='test', unknown_field='bad')


# ** test: api_response_model_extensible
def test_api_response_model_extensible() -> None:
    '''
    Test that ApiResponseModel can be extended with custom fields.
    '''

    # Define a custom response model.
    class CalculatorResponse(ApiResponseModel):
        '''Custom response model for calculator results.'''
        result: float = Field(..., description='The computed result.')
        operation: str = Field(..., description='The operation performed.')

    # Instantiate the custom response model.
    response = CalculatorResponse(result=4.0, operation='add')

    # Verify the fields.
    assert response.result == 4.0
    assert response.operation == 'add'


# ** test: api_error_response_constructor
def test_api_error_response_constructor() -> None:
    '''
    Test that ApiErrorResponse can be instantiated with error and message fields.
    '''

    # Create an error response.
    error = ApiErrorResponse(
        error='Invalid Input',
        message='Value must be a number',
    )

    # Verify the fields.
    assert error.error == 'Invalid Input'
    assert error.message == 'Value must be a number'


# ** test: api_error_response_requires_fields
def test_api_error_response_requires_fields() -> None:
    '''
    Test that ApiErrorResponse requires both error and message fields.
    '''

    # Attempt to instantiate without required fields.
    with pytest.raises(ValidationError):
        ApiErrorResponse()


# ** test: api_request_model_empty
def test_api_request_model_empty() -> None:
    '''
    Test that base ApiRequestModel can be instantiated without fields.
    '''

    # Instantiate the base request model.
    request = ApiRequestModel()

    # Verify it is an instance.
    assert isinstance(request, ApiRequestModel)


# ** test: api_response_model_empty
def test_api_response_model_empty() -> None:
    '''
    Test that base ApiResponseModel can be instantiated without fields.
    '''

    # Instantiate the base response model.
    response = ApiResponseModel()

    # Verify it is an instance.
    assert isinstance(response, ApiResponseModel)
