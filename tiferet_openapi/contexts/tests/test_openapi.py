'''Tiferet OpenAPI Context Tests'''

# *** imports

# ** core
from typing import Any
from unittest import mock

# ** infra
import pytest
from pydantic import BaseModel, Field
from tiferet import TiferetError
from tiferet.assets.exceptions import TiferetAPIError
from tiferet.contexts import FeatureContext, ErrorContext, LoggingContext
from tiferet.events import DomainEvent

# ** app
from ..openapi import OpenApiContext
from ..request import OpenApiRequestContext


# *** models

# ** model: sample_model
class SampleModel(BaseModel):
    '''
    A sample Pydantic model for testing serialization.
    '''

    # * attribute: name
    name: str = Field(..., description='The name.')

    # * attribute: value
    value: int = Field(..., description='The value.')


# *** fixtures

# ** fixture: mock_features
@pytest.fixture
def mock_features() -> FeatureContext:
    '''
    Mock FeatureContext for testing.

    :return: A mock FeatureContext.
    :rtype: FeatureContext
    '''
    return mock.Mock(spec=FeatureContext)


# ** fixture: mock_errors
@pytest.fixture
def mock_errors() -> ErrorContext:
    '''
    Mock ErrorContext for testing.

    :return: A mock ErrorContext.
    :rtype: ErrorContext
    '''
    return mock.Mock(spec=ErrorContext)


# ** fixture: mock_logging
@pytest.fixture
def mock_logging() -> LoggingContext:
    '''
    Mock LoggingContext for testing.

    :return: A mock LoggingContext.
    :rtype: LoggingContext
    '''
    return mock.Mock(spec=LoggingContext)


# ** fixture: mock_get_route_evt
@pytest.fixture
def mock_get_route_evt() -> DomainEvent:
    '''
    Mock domain event for get_route.

    :return: A mock DomainEvent with an execute method.
    :rtype: DomainEvent
    '''
    evt = mock.Mock(spec=DomainEvent)
    evt.execute = mock.Mock()
    return evt


# ** fixture: mock_get_status_code_evt
@pytest.fixture
def mock_get_status_code_evt() -> DomainEvent:
    '''
    Mock domain event for get_status_code.

    :return: A mock DomainEvent with an execute method.
    :rtype: DomainEvent
    '''
    evt = mock.Mock(spec=DomainEvent)
    evt.execute = mock.Mock()
    return evt


# ** fixture: context
@pytest.fixture
def context(
        mock_features: FeatureContext,
        mock_errors: ErrorContext,
        mock_logging: LoggingContext,
        mock_get_route_evt: DomainEvent,
        mock_get_status_code_evt: DomainEvent,
    ) -> OpenApiContext:
    '''
    Create an OpenApiContext for testing.

    :param mock_features: The mock feature context.
    :type mock_features: FeatureContext
    :param mock_errors: The mock error context.
    :type mock_errors: ErrorContext
    :param mock_logging: The mock logging context.
    :type mock_logging: LoggingContext
    :param mock_get_route_evt: The mock get_route domain event.
    :type mock_get_route_evt: DomainEvent
    :param mock_get_status_code_evt: The mock get_status_code domain event.
    :type mock_get_status_code_evt: DomainEvent
    :return: The OpenApiContext instance.
    :rtype: OpenApiContext
    '''

    return OpenApiContext(
        interface_id='test_api',
        features=mock_features,
        errors=mock_errors,
        logging=mock_logging,
        get_route_evt=mock_get_route_evt,
        get_status_code_evt=mock_get_status_code_evt,
    )


# *** tests

# ** test: parse_request_returns_openapi_request_context
def test_parse_request_returns_openapi_request_context(context: OpenApiContext) -> None:
    '''
    Test that parse_request returns an OpenApiRequestContext instance.

    :param context: The OpenApiContext instance.
    :type context: OpenApiContext
    '''

    # Parse a request.
    request = context.parse_request(
        headers={'content-type': 'application/json'},
        data={'a': 1, 'b': 2},
        feature_id='calc.add',
    )

    # Assert the result is an OpenApiRequestContext.
    assert isinstance(request, OpenApiRequestContext)
    assert request.feature_id == 'calc.add'
    assert request.data == {'a': 1, 'b': 2}


# ** test: handle_error_tiferet_error_status_code
def test_handle_error_tiferet_error_status_code(
        context: OpenApiContext,
        mock_get_status_code_evt: DomainEvent,
        mock_errors: ErrorContext,
    ) -> None:
    '''
    Test that handle_error resolves status code via get_status_code_handler for TiferetError.

    :param context: The OpenApiContext instance.
    :type context: OpenApiContext
    :param mock_get_status_code_evt: The mock get_status_code domain event.
    :type mock_get_status_code_evt: DomainEvent
    :param mock_errors: The mock error context.
    :type mock_errors: ErrorContext
    '''

    # Configure the mock to return 400 status code.
    mock_get_status_code_evt.execute.return_value = 400

    # Configure ErrorContext.handle_error to return a formatted error dict.
    mock_errors.handle_error.return_value = dict(
        name='Invalid Input',
        message='Value must be a number',
        error_code='INVALID_INPUT',
    )

    # Create a TiferetError.
    error = TiferetError('INVALID_INPUT', 'bad input')

    # Assert TiferetAPIError is raised with the correct status code.
    with pytest.raises(TiferetAPIError) as exc_info:
        context.handle_error(error)

    assert exc_info.value.status_code == 400
    mock_get_status_code_evt.execute.assert_called_once_with(error_code='INVALID_INPUT')


# ** test: handle_error_non_tiferet_error_500
def test_handle_error_non_tiferet_error_500(
        context: OpenApiContext,
        mock_errors: ErrorContext,
    ) -> None:
    '''
    Test that handle_error returns 500 for non-Tiferet exceptions.

    :param context: The OpenApiContext instance.
    :type context: OpenApiContext
    :param mock_errors: The mock error context.
    :type mock_errors: ErrorContext
    '''

    # Configure ErrorContext.handle_error to return a formatted error dict.
    mock_errors.handle_error.return_value = dict(
        name='App Error',
        message='An error occurred',
        error_code='APP_ERROR',
    )

    # Create a generic exception.
    error = RuntimeError('unexpected failure')

    # Assert TiferetAPIError is raised with status code 500.
    with pytest.raises(TiferetAPIError) as exc_info:
        context.handle_error(error)

    assert exc_info.value.status_code == 500


# ** test: handle_response_returns_tuple
def test_handle_response_returns_tuple(
        context: OpenApiContext,
        mock_get_route_evt: DomainEvent,
    ) -> None:
    '''
    Test that handle_response returns (response, status_code) tuple.

    :param context: The OpenApiContext instance.
    :type context: OpenApiContext
    :param mock_get_route_evt: The mock get_route domain event.
    :type mock_get_route_evt: DomainEvent
    '''

    # Create a mock route with status_code.
    mock_route = mock.Mock()
    mock_route.status_code = 201
    mock_get_route_evt.execute.return_value = mock_route

    # Create a request and set a result.
    request = context.parse_request(feature_id='calc.add')
    request.result = {'sum': 3}

    # Handle the response.
    response, status_code = context.handle_response(request)

    # Assert the response and status code.
    assert response == {'sum': 3}
    assert status_code == 201
    mock_get_route_evt.execute.assert_called_once_with(endpoint='calc.add')


# ** test: set_result_none
def test_set_result_none() -> None:
    '''
    Test that set_result converts None to empty string.
    '''

    # Create a request context and set result to None.
    request = OpenApiRequestContext(feature_id='test')
    request.set_result(None)

    # Assert the result is an empty string.
    assert request.result == ''


# ** test: set_result_base_model
def test_set_result_base_model() -> None:
    '''
    Test that set_result serializes a Pydantic BaseModel to dict.
    '''

    # Create a request context and set result to a BaseModel.
    request = OpenApiRequestContext(feature_id='test')
    model = SampleModel(name='foo', value=42)
    request.set_result(model)

    # Assert the result is a dict.
    assert request.result == {'name': 'foo', 'value': 42}


# ** test: set_result_list_of_base_models
def test_set_result_list_of_base_models() -> None:
    '''
    Test that set_result serializes a list of BaseModels to list of dicts.
    '''

    # Create a request context and set result to a list of BaseModels.
    request = OpenApiRequestContext(feature_id='test')
    models = [
        SampleModel(name='a', value=1),
        SampleModel(name='b', value=2),
    ]
    request.set_result(models)

    # Assert the result is a list of dicts.
    assert request.result == [
        {'name': 'a', 'value': 1},
        {'name': 'b', 'value': 2},
    ]


# ** test: set_result_dict_of_base_models
def test_set_result_dict_of_base_models() -> None:
    '''
    Test that set_result serializes a dict of BaseModel values to dict of dicts.
    '''

    # Create a request context and set result to a dict of BaseModels.
    request = OpenApiRequestContext(feature_id='test')
    models = {
        'x': SampleModel(name='x', value=10),
        'y': SampleModel(name='y', value=20),
    }
    request.set_result(models)

    # Assert the result is a dict of dicts.
    assert request.result == {
        'x': {'name': 'x', 'value': 10},
        'y': {'name': 'y', 'value': 20},
    }


# ** test: set_result_primitive
def test_set_result_primitive() -> None:
    '''
    Test that set_result passes primitive values through directly.
    '''

    # Create a request context and set result to a primitive.
    request = OpenApiRequestContext(feature_id='test')
    request.set_result(42)

    # Assert the result is the primitive value.
    assert request.result == 42


# ** test: set_result_with_data_key
def test_set_result_with_data_key() -> None:
    '''
    Test that set_result with data_key delegates to parent (stores in request.data).
    '''

    # Create a request context and set result with a data_key.
    request = OpenApiRequestContext(feature_id='test', data={})
    request.set_result('intermediate', data_key='step_result')

    # Assert the value is stored in request.data.
    assert request.data['step_result'] == 'intermediate'


# ** test: handle_response_serializes_result
def test_handle_response_serializes_result() -> None:
    '''
    Test that handle_response calls set_result before returning.
    '''

    # Create a request context with a BaseModel result.
    request = OpenApiRequestContext(feature_id='test')
    request.result = SampleModel(name='test', value=99)

    # Handle the response.
    response = request.handle_response()

    # Assert the response is a serialized dict.
    assert response == {'name': 'test', 'value': 99}
