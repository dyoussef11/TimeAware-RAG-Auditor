
from pathlib import Path
import sys

def ensure_project_root_in_path(marker_files=("pyproject.toml", "requirements.txt", "README.md")):
    """
    Garante a raiz do projeto e pastas utils no sys.path sem quebrar dependências externas.
    """
    current = Path(__file__).resolve()
    root = None

    # Busca a raiz
    for parent in [current] + list(current.parents):
        if any((parent / marker).exists() for marker in marker_files):
            root = parent
            break

    if not root:
        raise RuntimeError("Raiz do projeto não encontrada.")

    # Raiz sempre no topo (índice 0) para priorizar seus módulos (core, etc)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    # Injeta utils das pastas numeradas (01, 02...) no final do path
    # Isso evita que seus scripts 'utils' sobrescrevam módulos padrão do Python
    for utils_path in root.glob("0*/utils"):
        if utils_path.is_dir() and str(utils_path) not in sys.path:
            sys.path.append(str(utils_path))

    return root