'''Tiferet OpenAPI Request Context Tests'''

# *** imports

# ** infra
from pydantic import BaseModel, Field

# ** app
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

# *** tests

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
