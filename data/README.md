# Dataset Directory

The dataset will contain synthetic Python debugging examples and later benchmark adaptations.

## Planned layout

```text
data/
├── raw/        # Original or generated samples before normalization
├── processed/  # Validated samples following configs/dataset_schema.json
└── splits/     # Train, validation, and test manifests
```

Do not place secrets, private source code, or unrestricted executable programs in this directory.

Each processed sample should follow the schema in `configs/dataset_schema.json`.
