'''Tiferet OpenAPI Request/Response Domain Object Tests'''

# *** imports

# ** infra
import pytest
from pydantic import Field, ValidationError

# ** app
from tiferet import use_tester
from ..request import ApiRequestModel, ApiResponseModel, ApiErrorResponse

# *** testers

# ** tester: test_api_request_model
@use_tester(
    type='domain',
    target_cls=ApiRequestModel,
    sample_data={},
)
class TestApiRequestModel:
    '''
    Bound domain tester for ApiRequestModel.
    '''

    # * test: api_request_model_empty
    def test_api_request_model_empty(self, test_ctx) -> None:
        '''
        Test that base ApiRequestModel can be instantiated without fields.

        :param test_ctx: The bound domain tester context.
        :type test_ctx: object
        :return: None
        :rtype: None
        '''

        # Construct from empty sample data and assert the instance type.
        test_ctx.assert_new()

    # * test: api_request_model_extensible
    def test_api_request_model_extensible(self) -> None:
        '''
        Test that ApiRequestModel can be extended with custom fields.

        :return: None
        :rtype: None
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

    # * test: api_request_model_forbids_extra
    def test_api_request_model_forbids_extra(self) -> None:
        '''
        Test that ApiRequestModel rejects unknown fields (extra='forbid').

        :return: None
        :rtype: None
        '''

        # Define a custom request model.
        class SimpleRequest(ApiRequestModel):
            '''A simple request model.'''
            name: str = Field(..., description='A name.')

        # Attempt to instantiate with an extra field.
        with pytest.raises(ValidationError):
            SimpleRequest(name='test', unknown_field='bad')

# ** tester: test_api_response_model
@use_tester(
    type='domain',
    target_cls=ApiResponseModel,
    sample_data={},
)
class TestApiResponseModel:
    '''
    Bound domain tester for ApiResponseModel.
    '''

    # * test: api_response_model_empty
    def test_api_response_model_empty(self, test_ctx) -> None:
        '''
        Test that base ApiResponseModel can be instantiated without fields.

        :param test_ctx: The bound domain tester context.
        :type test_ctx: object
        :return: None
        :rtype: None
        '''

        # Construct from empty sample data and assert the instance type.
        test_ctx.assert_new()

    # * test: api_response_model_extensible
    def test_api_response_model_extensible(self) -> None:
        '''
        Test that ApiResponseModel can be extended with custom fields.

        :return: None
        :rtype: None
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

# ** tester: test_api_error_response
@use_tester(
    type='domain',
    target_cls=ApiErrorResponse,
    sample_data={'error': 'Invalid Input', 'message': 'Value must be a number'},
    equality_fields=['error', 'message'],
)
class TestApiErrorResponse:
    '''
    Bound domain tester for ApiErrorResponse.
    '''

    # * test: api_error_response_constructor
    def test_api_error_response_constructor(self, test_ctx) -> None:
        '''
        Test that ApiErrorResponse can be instantiated with error and message fields.

        :param test_ctx: The bound domain tester context.
        :type test_ctx: object
        :return: None
        :rtype: None
        '''

        # Construct from sample data and assert field equality.
        test_ctx.assert_new()

    # * test: api_error_response_requires_fields
    def test_api_error_response_requires_fields(self) -> None:
        '''
        Test that ApiErrorResponse requires both error and message fields.

        :return: None
        :rtype: None
        '''

        # Attempt to instantiate without required fields.
        with pytest.raises(ValidationError):
            ApiErrorResponse()
