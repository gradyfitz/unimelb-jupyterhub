# RBAC Permissions for Hub Account
The submit-pod and archive tools require stronger permissions than provided by
the default setup of JupyterHub.

To add these permissions,
1. Copy hub-rbac.yaml to the server.
2. Run `kubectl create -f hub-rbac.yaml`
