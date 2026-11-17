"""Reproduce the nested validation issue described in SWE-bench Lite 1343."""

from marshmallow import Schema, fields, validates


def test_invalid_nested_value_returns_validation_errors():
    class Bar(Schema):
        value = fields.String()

        @validates("value")
        def validate_value(self, value):
            pass

    class Foo(Schema):
        bar = fields.Nested(Bar)

    errors = Foo().validate({"bar": "invalid"})
    assert "bar" in errors
