def flatten(data, prefix=""):
    rows = []
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            rows.extend(flatten(value, new_prefix))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            new_prefix = f"{prefix}[{index}]"
            rows.extend(flatten(item, new_prefix))
    else:
        rows.append({
            "path": prefix,
            "value": data,
            "type": type(data).__name__,
        })
    return rows


if __name__ == "__main__":
    ejemplo = {
        "name": "cpython",
        "stars": 73315,
        "private": False,
        "owner": {"login": "python", "id": 1525981},
        "topics": ["python", "language"],
    }
    for row in flatten(ejemplo):
        print(row)