import os
from typing import List
from unittest import mock

import pytest
import yaml
from pydantic import BaseModel, validator, ValidationError

from applauncher.configuration import FormatterWithListYAML, is_string, load_configuration


class TestModel(BaseModel):
    value: str
    default_value: str = "default"
    number: int = 0

    @validator('value')
    def value_must_contain_space(cls, v):
        if ' ' not in v:
            raise ValueError('must contain a space')
        return v.title()


TestModel.__test__ = False


class Bundle:
    def __init__(self):
        self.config_mapping = {
            "test": TestModel
        }


class ListModel(BaseModel):
    some_list: List[str]
    custom_splitter: List[str]
    yaml_style: List[str]
    yaml_style_same_line: List[str]


class ListBundle:
    def __init__(self):
        self.config_mapping = {
            "test": ListModel
        }


class TestClass:
    def test_validation_error_case(self):
        with pytest.raises(ValidationError):
            # Testing validation annotation
            load_configuration("test/config_assets/config.yml", "test/config_assets/parameters.yml", [Bundle()])

        with pytest.raises(ValidationError):
            # Testing wrong data type
            load_configuration("test/config_assets/config_3.yml", "test/config_assets/parameters_2.yml", [Bundle()])

    def test_success_case(self):
        c = load_configuration("test/config_assets/config.yml", "test/config_assets/parameters_2.yml", [Bundle()])
        assert c.test.value == "Two Words"
        assert c.test.number == 0

    def test_extra_config(self):
        c = load_configuration("test/config_assets/config_2.yml", "test/config_assets/parameters_2.yml", [Bundle()])
        assert c.test.value == "Two Words"
        assert c.test.number == 2

    def test_empty_config(self):
        with pytest.raises(KeyError):
            load_configuration("test/config_assets/config.yml", "test/config_assets/empty.yml", [Bundle()])

    def test_env_vars(self):
        with pytest.raises(ValidationError):
            os.environ['VALUE'] = "one"
            c = load_configuration("test/config_assets/config.yml", "test/config_assets/parameters_2.yml", [Bundle()])

        os.environ['VALUE'] = "from env"
        c = load_configuration("test/config_assets/config.yml", "test/config_assets/parameters_2.yml", [Bundle()])
        assert c.test.value == "From Env"

    def test_parse_lists(self):
        c = load_configuration(
            "test/config_assets/config_list.yml",
            "test/config_assets/parameters_list.yml",
            [ListBundle()]
        )
        assert c.test.some_list == ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        assert c.test.custom_splitter == ['a,b,c', 'd,e', 'f', 'g']
        assert c.test.yaml_style == ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'other-value', 'and-more']
        assert c.test.yaml_style_same_line == ['a', 'b', 'c', 'd', 'e', 'f', 'g']


def test_is_string():
    assert is_string("4") is False
    assert is_string(4) is False
    assert is_string("true") is False
    assert is_string("True") is False
    assert is_string("TRue") is False
    assert is_string("false") is False
    assert is_string("False") is False
    assert is_string("faLse") is False
    assert is_string("a text") is True


@pytest.fixture
def formatter():
    return FormatterWithListYAML()


@pytest.fixture
def simple_format_sample():
    return "Simple, {VALUE}", {'VALUE': 'without lists'}


@pytest.fixture
def config_list_test():
    return yaml.safe_load('test/config_assets/config_list.yml')


@pytest.fixture
def parameters_list_test():
    return yaml.safe_load('test/config_assets/parameters_list.yml')


class TestFormatterWithListYAML:
    def test_not_called_if_no_list(self, formatter, simple_format_sample):
        with mock.patch('applauncher.configuration.FormatterWithListYAML._format_list_field') as mocked_format_list:
            formatter.format(simple_format_sample[0], **simple_format_sample[1])
            mocked_format_list.assert_not_called()

    def test_format_field_called_if_no_list(self, formatter, simple_format_sample):
        with mock.patch('applauncher.configuration.FormatterWithListYAML.format_field', return_value='') as mocked:
            formatter.format(simple_format_sample[0], **simple_format_sample[1])
            mocked.assert_called_once()

    def test_basic_list_default_splitter(self, formatter):
        assert formatter.format('Some value: {VALUE:[]}', VALUE='a,b,c') == 'Some value: ["a", "b", "c"]'
        assert formatter.format('Some value: {VALUE:[]}', VALUE='a|b|c') == 'Some value: ["a|b|c"]'

    def test_basic_list_custom_splitter(self, formatter):
        assert formatter.format('Some value: {VALUE:[|]}', VALUE='a,b,c') == 'Some value: ["a,b,c"]'
        assert formatter.format('Some value: {VALUE:[|]}', VALUE='a|b|c') == 'Some value: ["a", "b", "c"]'

    def test_yaml_list_default_spaces(self, formatter):
        assert formatter.format('Some value: {VALUE:[]-}', VALUE='a,b,c') == 'Some value: a\n  - b\n  - c'

    def test_yaml_list_custom_spaces(self, formatter):
        assert formatter.format('Some value: {VALUE:[]-.4}', VALUE='a,b,c') == 'Some value: a\n    - b\n    - c'

    def test_yaml_list_add_prefix_to_first(self, formatter):
        assert formatter.format('Some value: {VALUE:[]-^}', VALUE='a,b,c') == 'Some value: \n  - a\n  - b\n  - c'

    def test_yaml_list_all_params(self, formatter):
        expected_value = 'Some value: \n    - a\n    - b\n    - c,d'
        assert formatter.format('Some value: {VALUE:[|]-.4^}', VALUE='a|b|c,d') == expected_value
