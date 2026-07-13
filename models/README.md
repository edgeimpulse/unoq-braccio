# Models

Drop your **aarch64** Edge Impulse `.eim` model here so the on-device Docker
container can load it.

`docker-compose.yml` bind-mounts this folder read-only into the container:

```yaml
volumes:
  - ./models:/models:ro
```

and the launch reads it via `MODEL_PATH` (default `/models/model.eim`).

## Steps

1. Export your model from Edge Impulse Studio as a **Linux (AARCH64)** `.eim`
   binary, or download it on the UNO Q with the Edge Impulse CLI.
2. Copy it here and name it `model.eim`:

   ```text
   models/model.eim
   ```

   To use a different filename, override `MODEL_PATH` in `docker-compose.yml`.

## Important

- The model must be built for **aarch64** (the UNO Q's Cortex-A53). x86 or
  MCU exports will not load.
- The detector's labels **must match** the item names in
  `edge_impulse/pick_place_workflows.yaml` (e.g. `Red Block`, `Blue Block`,
  `Yellow Block`). If the container logs a different model (for example the
  Edge Impulse tutorial model with `coffee`/`lamp` labels), you mounted the
  wrong `.eim`.
- Never commit `.eim` files or your Edge Impulse API key. `.eim` binaries are
  git-ignored; keep API keys in the `EDGE_IMPULSE_API_KEY` environment
  variable only.
