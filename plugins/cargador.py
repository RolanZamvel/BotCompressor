import importlib
import pkgutil
from handlers import CommandInterface
from pathlib import Path
from typing import List



def load_handlers(app, package_name: str = "handlers"):
    """Carga dinámicamente todos los módulos de handlers"""
    
    # Obtiene la ruta del paquete
    package_path = Path(__file__).parent.parent / package_name
    
    # Importa el paquete base
    package = importlib.import_module(package_name)
    
    # Cada módulo debe tener una función 'register'
    for _, name, _ in pkgutil.iter_modules([str(package_path)]):
        module = importlib.import_module(f"{package_name}.{name}")
        
        # Inyecta la interfaz al módulo
        if hasattr(module, 'register'):
            interface = CommandInterface(app)
            module.register(app, interface)
            print(f"✅ Handler '{name}' cargado")

def load_helpers(app, package_name: str = "handlers"):
    """Carga dinámicamente todos los módulos de handlers"""
    #
    helpers = ""
    # Obtiene la ruta del paquete
    package_path = Path(__file__).parent.parent / package_name
    
    # Importa el paquete base
    package = importlib.import_module(package_name)
    
    # Cada módulo debe tener una función 'help'
    for _, name, _ in pkgutil.iter_modules([str(package_path)]):
        module = importlib.import_module(f"{package_name}.{name}")
        
        # Salta comando help
        #if name == "help": continue
        # Crea la cadena de texto de ayuda
        if hasattr(module, 'help'):
            helpers = helpers + (f"/{name}: {module.help()} \n")
            print(f"✅ Ayuda '{name}' cargada")
    return helpers
