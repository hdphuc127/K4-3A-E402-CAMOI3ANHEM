# CO Y DE TRONG - khong re-export bat cu thu gi.
#
# Neu file nay lam `from .prompts import *` hoac `from .rag_engine import *`,
# thi moi lenh `import src.core.<bat_ky_gi>` deu keo theo ca Qdrant,
# sentence-transformers va SDK cua LLM. Hau qua:
#   1. Test cua tang prompts khong con chay duoc trong venv chi co pydantic.
#   2. Sinh import cycle giua prompts/ va rag_engine.py.
#
# Giu file nay rong.
