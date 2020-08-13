# JupyterHub API
The JupyterHub API is fairly rich, a list of routes is described at
https://jupyterhub.readthedocs.io/en/stable/_static/rest-api/index.html
this is heavily useful for operating on users.

A simple test demonstrating how to use the API is available at
doc/api_test.ipynb. This should be run from inside JupyterHub.

A simple demo showing how to use the groups functionality of JupyterHub is shown
in doc/groups_demo.ipynb. This should be run from inside JupyterHub.

## api_test.ipynb
The API test makes use of JUPYTERHUB_API_URL, the _internal_ URL for the API,
and JUPYTERHUB_API_TOKEN, the token used for the server, it is also possible to
use the token to perform actions on your behalf. This might be useful for
various marking-related tasks.

## groups_demo.ipynb
This builds on some of the ideas in the API test notebook to show how to manage
groups in JupyterHub. These can be useful in various ways.
