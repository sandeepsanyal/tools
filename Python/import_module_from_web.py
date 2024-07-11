# importing modules
import os
from importlib.util import module_from_spec
import requests

def import_cdn(
  url: str,
  name: str = None
):
    """
    Imports a python module from web given it's URL

    Parameters:
    -----------
    url: string
        complete url to the location of the .py file
    name: string (Optional)
        Name of the python script
        
    Returns:
    --------
        An imported module

    Usage:
    module1 = import_cdn(url="url/path/to/a_file.py")
    """
    if not name:
        name = os.path.basename(url).lower().rstrip('.py')
 
    r = requests.get(url)
    r.raise_for_status()
 
    codeobj = compile(r.content, url, 'exec')
    module = module_from_spec(name)
    exec(codeobj, module.__dict__)
    
    return module
