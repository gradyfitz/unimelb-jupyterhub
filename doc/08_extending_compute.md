# Scaling - Compute
This section is one I haven't yet tested.

To add nodes to the cluster after it has been deployed, a simple process should
suffice.

1. Create the instance according to all the steps given in playbook.yml.
2. Generate a join token from the head node server.
3. Use the token to join the node to the kubernetes cluster.

Kubernetes should make use of the additional node and its resources.
