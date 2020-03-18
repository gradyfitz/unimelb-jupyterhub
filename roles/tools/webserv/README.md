# Setup

Set up values as appropriate in files then:
1. Run `kubectl create -f nginx-pvc.yaml`
2. Run `kubectl create -f nginx-configmap.yaml`
3. Run `kubectl create -f webserv.yaml`
4. Run `kubectl create -f nginx-expose.yaml`
5. Open the ingress port in the security group.
6. Find any node running an nginx pod (using `kubectl describe nodes | grep nginx -B50 | grep Hostname`, for example)
7. ssh to that node.
8. Find the container running nginx using `sudo docker ps | grep nginx`
  (use the container which doesn't have "POD" in the name)
9. Upload the web files to the node and use `docker cp` to copy them into
  /www/data/ (or wherever else your files are served from).
