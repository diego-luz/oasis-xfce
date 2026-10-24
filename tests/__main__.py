import sys
import unittest
from pathlib import Path

# o __init__ deste pacote ja isolou a pasta pessoal; a busca parte da pasta
# acima do projeto, para os testes importarem o projeto como pacote
_PASTA = Path(__file__).resolve().parent
_suite = unittest.defaultTestLoader.discover(str(_PASTA), top_level_dir=str(_PASTA.parent.parent))
sys.exit(0 if unittest.TextTestRunner(verbosity=2).run(_suite).wasSuccessful() else 1)
