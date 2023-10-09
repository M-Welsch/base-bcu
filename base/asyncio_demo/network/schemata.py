from jsonschema import Draft7Validator, validate

schema = {
    "type": "object",
    "properties": {
        "price": {"type": "number"},
        "name": {"type": "string"},
    },
}


def main():
    instance = {"name": "Eggs", "price": 34.99}
    validate(instance=instance, schema=schema)

    validator = Draft7Validator(schema)

    for error in validator.iter_errors({}):
        print(f"Validation error: {error.message}")

    print("\nSchema specification:")
    print(validator.schema)


if __name__ == "__main__":
    main()
