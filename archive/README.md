# Archive

Historical files kept for reference after the package refactor.

These files are not the supported entrypoints for the current package:

- `llama_cpp_server.py` - original monolithic server
- `llama_cpp_server_guide.md` - guide for the original monolithic server
- `analisi_generalizzazione_server_llm.md` - early design analysis
- `example_server.py` - standalone pre-package example
- `example_mlx_server.py` - standalone pre-package MLX example

Use the package entrypoints documented in the root `README.md` instead:

- CLI: `local-llm`
- Python API: `local_llm_server.serve`
- HTTP server: `src/local_llm_server/server.py`
