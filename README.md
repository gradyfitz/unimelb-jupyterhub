# JupyterHub Deployment Script
---
This Ansible script can be used to deploy JupyterHub on a cluster of nodes
implementing the OpenStack protocol.

## Setup
---
You will likely need to install Ansible, it can be installed on any Unix or
MacOS X machine using the instructions you can find at
https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html

In order to set up the system to be deployed on your resources, you may need to
change a number of settings in variables/vars.yml

Particularly of note are the following settings:
- `attach_volumes` - If you don't have provisioned persistent storage, you can
  set this to false to deploy without creating any volumes.
- `volume_size_gb` - The number of gigabytes that each volume will be, volumes
  can't be shared between multiple instances at the same time, so you may need
  to adjust this based on what resources are available to you.
- `instance_count` - The number of instances to use for the JupyterHub cluster,
  a greater number of instances will be able to handle more students.
- `instance_flavour` - This defines the number of cores, the amount of memory
  and the size of the ephemeral disk, you can check what flavours are available
  to you when creating an instance on the NeCTAR dashboard.
- `instance_key_pair_name` - This links to the existing key pair name which will
  have been created (or reused) during deployment.
- `instance_availability_zone` - You may need to change this and
  `volume_availability_zone` if the flavour you've selected isn't in the zone
  you've selected, or it is and you want to ensure the instances are closer to
  you.

Additional options are available in the file if you're running on different
networks or availability zones or the image selected simply isn't available
(the architecture isn't terribly demanding, so most images should work just as
well).

## Deployment
---
To deploy you'll need to follow a few simple steps

1. Log into your NeCTAR account.
2. Create (or import) a key pair (Compute → Key Pairs) (Note: You can reuse an
  existing key pair, just ensure you have a key pair available for use)
3. Set up the variables in variables/vars.yml
4. Reset your password (Your username in the top right corner → Settings,
  followed by navigating to the Settings → Reset Password page)
5. Download the OpenStack RC file for the project you want to deploy in and name
  it openrc.sh.
6. Run `./deploy.sh <private key path>`, where `<private key path>` is replaced
with the path to the private key for the key pair from step 2. When prompted,
enter your password. NOTE: Your private key will need to have a secure mode
applied, use `chmod 600 <private key path>`
7. If the process fails and you everything seems correct, try running it again.
  Instance creation often times out, but the script is idempotent, so you can
  re-run it as many times as you like.
8. Add proxy.secretToken (arbitrary token), proxy.https.hosts
  (e.g. `["comp20003-jh.eng.unimelb.edu.au"]`), proxy.https.type (`manual`),
  proxy.https.manual.key (the private key) and proxy.https.manual.cert (the
  https certificate) to config.yml.
9. Run `helm upgrade --install {{ jupyterhub_name }} jupyterhub/jupyterhub --version={{ jupyterhub_version }} --values ./config.yml`, substituting jupyterhub_name and jupyterhub_version for
  the values in variables/vars.yml

## Image Requirements
---
Any image you use is assumed to have nbgitpuller pip installed already. nbgrader
is also not provided by the hub itself, but deployment doesn't rely on it
existing. This requirement can also be removed by dropping the lifecycleHooks
section and all its sub-items from the template in files/config.yml.

## Updating the Image
---
If you update the images, you'll need to kill all pods using the image, then on
all nodes which have pulled the image (check using `sudo docker images`) you'll
need to remove the docker containers using the image (`sudo docker image rm` the
image id(s) and it will tell you which containers you need to kill using `sudo
docker rm`, then rm the image(s) again). The latest image should then be pulled
when someone logs in again.

## Changes
---
The script isn't fundamentally dependent on OpenStack, just about all flavours
of cloud can be found in the ansible documentation. Guides specifically on a
number of public clouds can be found at https://docs.ansible.com/ansible/latest/scenario_guides/cloud_guides.html .
Attempts have been made to make the purpose of each command in the OpenStack
version clear, generally the differences should only occur in the provisioning
stage, the actual cluster setup shouldn't be affected very much. Full details of
available ansible modules can be found here: https://docs.ansible.com/ansible/latest/modules/list_of_cloud_modules.html

## Troubleshooting
---
### A student created a file too big
Log onto the server and run `df -h /mnt/*` to see the list of nfs shares, most
of the time the share containing all the users will be much more used than the
rest. cd into the right share, then cd into the claim for the user who created
a file too big. (If you aren't sure which user is the culprit, `du -chs ./*` is
useful for narrowing this down). You can use `du` to work out exactly where the
large file is, then `rm` the file. Take down the student's server from the
JupyterHub admin and then bring it back again and you should be able to access
their instance without it hanging.

### Git Pull Fails for User
If git pulling fails for the user, mv their existing directory to another
location, reopen the server, and then cp the old files back over the top. You
can let students know that they can delete the files which they haven't made
changes to in order to pull the latest versions again.

### A Node Stops Working
If a node stops working properly and you need to move students off that node,
apply a taint to the node (e.g. running
  `kubectl taint nodes jupyterhub-4-compute node-role.kubernetes.io/master=temp:PreferNoSchedule`,
which applies a taint to a node called jupyterhub-4-compute as a master node
with the completely arbitrary value 'temp'), then kill the servers of all users
who are on the node from the JupyterHub instance (you can see the list of these
users using e.g. `kubectl describe node jupyterhub-4-compute`, where
jupyterhub-4-compute is the name of the node you've just tainted), once the
issue is resolved, you can allow nodes to be scheduled again using
e.g. `kubectl taint nodes jupyterhub-4-compute node-role.kubernetes.io/master-`
again where jupyterhub-4-compute is the name of the node you tainted.

### Catastrophic Failure and the Pod Won't Stop
If a user's server appears to catastrophically fail and the underlying docker
container becomes stuck in a state of being running, but also can't be
terminated by using `sudo kubectl delete pod jupyter-xxxxxx`, find the node the
container runs on (`sudo kubectl describe nodes` can help with this), then ssh
into that node and find the container running the user's node using e.g.
`sudo docker ps | grep xxxxxx`, then run `sudo docker container top yyyyyyy`
where yyyyyyy is the name of the container (the first column returned by the
grep), then use `ps -c -o ppid= PID`, where PID is the PID of the process
running in the container, repeat this until you find the docker containerd
process. Kill all the processes you saw in that subtree. You may need to delete
the user from JupyterHub if the state is broken in the database, their
persistent data should remain.

### Clocks Getting Out of Sync
Run `sudo systemctl restart systemd-timesyncd.service` on all hosts.

### Disk Fills Up
Sometimes your operating disk might fill up, this can bring down
the entire cluster. A few things which have helped for me:
- Move Docker's image repo to the ephemeral disk. To do so, add the
following to /etc/systemd/system/docker.service.d/docker.root.conf
on all nodes:
```
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -g /mnt/dockerd -H fd://
```
then run
```
sudo systemctl daemon-reload
sudo systemctl restart docker
```
- Move the kubelet directory to the ephemeral disk. To do so, add
the following to /etc/default/kubelet
```
# /etc/sysconfig/kubelet
KUBELET_EXTRA_ARGS=--root-dir=/mnt/k8s/kubelet
```
then run
```
sudo systemctl daemon-reload
sudo systemctl restart kubelet
```
- Following these, some pods may still be failing. In which case you
can use `kubectl get pods`,
`kubectl get pods --namespace=kube-system` to see any that don't
self-heal. In my case the scheduler failed to bind to the port it
wanted (check using
  `kubectl logs --namespace=<whatever namespace the pod isn't starting in> <pod-name>`),
so I used `sudo lsof -i :<port number>` to check what was using the
port. Because this was an earlier instance of the scheduler, I just
`sudo kill`ed the PID. After a couple of minutes the cluster was all
working again.

NOTE: The Docker and Kubelet changes above would ideally be made in
  the setup of the cluster as well.

### General Kubelet/Docker Issues
- If issues occur with the kubelet starting, you can look at
  `cat /var/log/syslog | tail -n 50` to see where this occurs, for
  us, swap turned on again for some reason at one point, meaning we
  needed to turn it off with `sudo swapoff -a`

## Ephemeral Issues
These issues may be fixed before we need to do anything about them in practice.
### Timestamp Issues
To resolve failing based on timestamp comparison.
https://github.com/jupyterhub/kubespawner/issues/354
```bash
kubectl patch deploy hub --type json --patch '[{"op": "replace", "path": "/spec/template/spec/containers/0/command", "value": ["bash", "-c", "\nmkdir -p ~/hotfix\ncp -r /usr/local/lib/python3.6/dist-packages/kubespawner ~/hotfix\nls -R ~/hotfix\npatch ~/hotfix/kubespawner/spawner.py << EOT\n72c72\n<             key=lambda x: x.last_timestamp,\n---\n>             key=lambda x: x.last_timestamp and x.last_timestamp.timestamp() or 0.,\nEOT\n\nPYTHONPATH=$HOME/hotfix jupyterhub --config /srv/jupyterhub_config.py --upgrade-db\n"]}]'
```
