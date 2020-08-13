# Modifying the JupyterHub config.yml
## Changing what Happens When Notebooks Start
The process for changing what happens when notebooks start is quite
straightforward.
1. Open /home/ubuntu/config.yml (nano is quite useful for this)
2. Move to singleuser.lifecycleHooks.postStart.exec.command
3. This value is the program and arguments to run following the start of the
  pod. For example "['/bin/bash', '-c', 'mkdir -p assignments']" would create
  the assignments folder for each user when they logged on. This can also be
  used for more complex use cases, e.g. logging in with some git credentials and
  pulling assignment materials from the repo. Or even looking for a shared
  script and running it (for a more user friendly approach).
4. Redeploy the chart with the config.

## Changing Behaviour Based on User
For user friendliness, it makes sense to integrate a number of things with
JupyterHub, but it often doesn't make as much sense to give all of these powers
to students as well. In this case it is very possible to check if the user is
within a list and give them these powers only if they are in that list.

The JupyterHub chart allows you to define additional spawner and kubernetes
functions to customise what happens when setting up JupyterHub servers.

1. Open /home/ubuntu/config.yml
2. Move to hub.extraConfig.myExtraConfig
3. Add the functions you want to run and then set the spawner to use this
  function.

Though the API for this is explained at
https://jupyterhub-kubespawner.readthedocs.io/en/latest/spawner.html#module-kubespawner.spawner
It will be easier to dissect an example.

### Example
An example of what this might look like when many extensions are setup could be:
```yaml
    myExtraConfig: |
      async def my_pre_spawn_hook(spawner):
        username = spawner.user.name
        if (username in ['gfitzpatrick', 'cewin', 'pwchou', 'anamk', 'myuan5', 'tuandungn']):
          spawner.image = "gradyfitz/comp20003-jupyter-c-kernel:admin"

          spawner.volumes = c.KubeSpawner.volumes.copy()
          spawner.volumes.append({"name": "nginx-web", "persistentVolumeClaim": {"claimName": "nginx-shared-space"}})
          spawner.volumes.append({"name": "submit-assignment-config", "persistentVolumeClaim": {"claimName": "submit-assignment-config"}})
          spawner.volumes.append({"name": "submit-raw-submissions", "persistentVolumeClaim": {"claimName": "submit-raw-submissions"}})
          spawner.volumes.append({"name": "submit-private-results", "persistentVolumeClaim": {"claimName": "submit-private-results"}})
          spawner.volumes.append({"name": "claim-assignment", "persistentVolumeClaim": {"claimName": "claim-assignment"}})
          spawner.volume_mounts = c.KubeSpawner.volume_mounts.copy()
          spawner.volume_mounts.append({"mountPath": "/home/web", "name": "nginx-web"})
          spawner.volume_mounts.append({"mountPath": "/home/submit/config", "name": "submit-assignment-config"})
          spawner.volume_mounts.append({"mountPath": "/home/submit/raw", "name": "submit-raw-submissions"})
          spawner.volume_mounts.append({"mountPath": "/home/submit/results", "name": "submit-private-results"})
          spawner.volume_mounts.append({"mountPath": "/home/assignments", "name": "claim-assignment"})
        else:
          spawner.volumes = c.KubeSpawner.volumes
          spawner.volume_mounts = c.KubeSpawner.volume_mounts
          spawner.image = "gradyfitz/comp20003-jupyter-c-kernel:user"
      c.KubeSpawner.pre_spawn_hook = my_pre_spawn_hook
```

Simplifying this to each essential component a simpler example could be:
```yaml
    myExtraConfig: |
      async def my_pre_spawn_hook(spawner):
        username = spawner.user.name
        if (username in ['gfitzpatrick', 'cewin']):
          spawner.image = "gradyfitz/comp20003-jupyter-c-kernel:admin"

          spawner.volumes = c.KubeSpawner.volumes.copy()
          spawner.volumes.append({"name": "nginx-web", "persistentVolumeClaim": {"claimName": "nginx-shared-space"}})
          spawner.volume_mounts = c.KubeSpawner.volume_mounts.copy()
          spawner.volume_mounts.append({"mountPath": "/home/web", "name": "nginx-web"})
        else:
          spawner.volumes = c.KubeSpawner.volumes
          spawner.volume_mounts = c.KubeSpawner.volume_mounts
          spawner.image = "gradyfitz/comp20003-jupyter-c-kernel:user"
      c.KubeSpawner.pre_spawn_hook = my_pre_spawn_hook
```

We create a pre spawn hook and then set this as the function that is called
before the spawner runs.

In this hook we check whether the user is one of the admin users 'gfitzpatrick'
or 'cewin'
```python
        if (username in ['gfitzpatrick', 'cewin']):
```
if they are
```python
          spawner.image = "gradyfitz/comp20003-jupyter-c-kernel:admin"
```
we set the image which is used to "gradyfitz/comp20003-jupyter-c-kernel:admin",
this might be useful if there are additional marking tools that you don't want
to burden students with, or if you want to test a new image version in an
earlier step before you push it to everyone.

Following this we add a volume for nginx, the webserver which we create as
described in roles/tools/webserv/README.md

First we get a clean copy from the configuration of JupyterHub itself (this
will include the user disk already)
```python
          spawner.volumes = c.KubeSpawner.volumes.copy()
```

then we add the new volume to the list of volumes which will be attached to the
pod being spawned.
```python
          spawner.volumes.append({"name": "nginx-web", "persistentVolumeClaim": {"claimName": "nginx-shared-space"}})
```
This is the pvc created in roles/tools/webserv/nginx-pvc.yaml, which has the
name "nginx-shared-space", the "name" field is just how we will refer to it when
mounting the volume, so it is arbitrary and doesn't have to match anything
created before.

Next, we have to mount the volume, this is done by again copying the clean copy
of existing mounts and adding the volume we just connected somewhere.
```python
          spawner.volume_mounts = c.KubeSpawner.volume_mounts.copy()
          spawner.volume_mounts.append({"mountPath": "/home/web", "name": "nginx-web"})
```
Here the mountPath is where the volume is where we can find it from JupyterLab,
and the name should match the name we gave the volume when we attached it.

The second last part of the example is the else case:
```python
        else:
          spawner.volumes = c.KubeSpawner.volumes
          spawner.volume_mounts = c.KubeSpawner.volume_mounts
          spawner.image = "gradyfitz/comp20003-jupyter-c-kernel:user"
```
hopefully straightforwardly, we set the volumes and volumes to mount to be the
values they initially had with no changes and the image to be the one we give
students. These can all be changed in the same way as the above.

And then lastly
```python
      c.KubeSpawner.pre_spawn_hook = my_pre_spawn_hook
```
We assign the function we created to be run before creating the server.

## Redeploying the Chart with Updated config.yml
For an example of the steps to redeploy (where version 0.8.2 was deployed):

1. e.g. `sudo su -`
2. `cd /home/ubuntu`
3. `helm upgrade --install jupyterhub jupyterhub/jupyterhub --version=0.8.2 --values ./config.yml` make sure the **version** you patch is the same as the version of
  JupyterHub you initially deployed, or else you may introduce issues where workaround have
  been patched.

## Note: What Changes to Make Where
There are two examples given.

1. singleuser.lifecycleHooks.postStart.exec.command and
2. hub.extraConfig.myExtraConfig

The first (singleuser) is run on the pod itself, so relates to things that
happen for the user (e.g. setup and so on, which they could theoretically run
themselves). While the second (hub) runs on the JupyterHub side, and generally
involves kubernetes-related things.