# 000-smb-consulting-data

Datasets and model artifacts for the SMB AI/ML consulting system. Git LFS enabled for large files.

## Structure

```
_shared/            # Shared helpers (data access, utilities)
_templates/         # Dataset and artifact templates
{engagement-slug}/  # Per-engagement data (created automatically)
  original/         # Raw uploaded data (never modified)
  cleaned/          # Cleaned and transformed data
  models/           # Serialized model artifacts
  notebooks/        # Generated Colab notebooks
  frontend/         # Frontend deployment assets
  docs/             # Engagement-specific documentation
```

## LFS-Tracked File Types

`.csv`, `.parquet`, `.pkl`, `.joblib`, `.h5`, `.keras`, `.pt`, `.zip`, `.tar.gz`

## Conventions

- Each engagement gets its own top-level folder named by slug
- Original uploaded data is preserved unmodified in `original/`
- All model artifacts include the model name and version in the filename
- Notebook naming follows: `{use-case}__{problem-type}__{architecture}-exp`

## Related Repos

- `000-smb-consulting-system-private` — Platform code and agent logic (private)
- [000-smb-consulting-system-public](https://github.com/EvagAIML/000-smb-consulting-system-public) — Public docs and sanitized assets
