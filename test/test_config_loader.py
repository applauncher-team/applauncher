from pydantic import BaseModel, validator
from applauncher.configuration import load_configuration
import pytest
from pydantic import ValidationError
import os

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

