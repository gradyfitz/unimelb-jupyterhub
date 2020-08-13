# Layout of Control, Access and General Overview
JupyterHub deployments have a number of layers and different authentication
points and admins. It can be valuable to have a clear understanding of what
these are and how to manage them.

## Areas
Broadly speaking, the areas which you might interact with are:

1. Research Cloud Project Member
2. Ansible
3. Research Cloud Project Manager
4. Server Head Node
5. Kubernetes Cluster
6. JupyterHub Admins
7. JupyterHub Chart Admins
8. Docker

## Purposes
The purposes of each level are different and generally grant different
permissions.

### Research Cloud Project Member Purpose
Any member of the research cloud project is able to launch jobs and make changes
to the underlying (virtual) hardware that runs the JupyterHub deployment.

### Ansible
Ansible is used to talk to the Research Cloud to retrieve information about all  
the servers deployed in the research cloud project. Talking to these servers
also involves using the private key assigned to the servers. Ansible is used to
avoid manually interacting with each server or the research cloud dashboard.

### Research Cloud Project Manager
The manager of the research cloud project is able to add members and request
resources for use in the project.

### Server Head Node
The head node of the server is one in the JupyterHub deployment, the default way
this is organised in the deployment script is to make the highest numbered node
the managing node. This is where you'll make changes to the JupyterHub
deployment beyond the default deployment and deploy the additional services.

### Kubernetes Cluster
The kubernetes cluster is setup across all the servers set up on the research
cloud. It can be interacted with through the services set up, or directly
through the head node.

### JupyterHub Admins
JupyterHub admins can edit users, stop and start servers and access student
servers when they're running.

### JupyterHub Chart Admins
These are an extension that I use, by setting a number of users apart in the
JupyterHub Chart to be treated specially, additional volumes, keys, powers and
images can be added. However, these must be added manually and the chart
redeployed. There may be a way to check the database to connect this with the
JupyterHub Admins directly, but there's a decent time investment required to do
so, so I haven't investigated this fully.

### Docker
In some rare edge cases, you might need or want to interact with containers
themselves (e.g. one case we ran into one year had a container which wouldn't
stop from kubernetes itself, which required access to the container via Docker
directly). These run on each node, so you will have to log onto that specific
node to work with pods running on it via Docker. A key simple use case is where
you might want a piece of software installed in a container but you don't want
the image pushed for one reason or another.

## Permissions
Different levels have different authentication mechanisms and methods of access.

### Research Cloud Project Member
Research cloud project members which have been added to a project can log into
the research cloud at https://dashboard.cloud.unimelb.edu.au/ , this dashboard
can be used to deploy servers. Importantly, if the key pair being used is lost
(say the person who is managing the server leaves and forgets to pass on that
key), a new key pair can be created and attached.

Also of importance is when interacting with the research cloud, you'll reset
your password and use this new password for access. Passwords in the research
cloud generally shouldn't have much longevity, so no need to save the password
anywhere, just create a new password whenever you need to interact.

### Ansible
Though not technically its own class. Ansible uses the password from the
research cloud and the private key created for the key pair to interact with
both the cloud and the servers themselves. The openrc.sh file sets up the
interaction with OpenStack and the private key handles interaction with the
servers.

### Research Cloud Manager
This role is able to add new members to the project and request more resources.
I haven't been in this role so can't speak too much to it. But generally this is
the person who gets the project going in the first place.

### Server Head Node
To access the head node directly, you'll need the IP (from the cloud dashboard)
and the private key created for the key pair attached to the instance. This all
works in the usual way, you log on as the user ubuntu which is given
passwordless sudoer rights. To elevate to root, run `sudo su -`.

### Kubernetes Cluster
Interacting with the kubernetes cluster can be done from the head node, using
kubectl commands, or you can create services which can do this for you. In order
to make requests using the python kubernetes API, you'll need to attach a
service account when creating the pods. This service account will need to have
appropriate roles to use the API routes you want to use. This is handled using
Role Based Access Control. This access is split into two categories,
interactions with namespaced resources (generally things to do with deployments,
conceptual "applications"), and interaction with non-namespaced resources
(generally cluster-wide, such as interactions with underlying resources and how
namespaced resource requests are fulfilled). Namespaced resource access is
handled by service accounts with particular Roles, and non-namespaced resource
access is handled by service accounts with particular Cluster Roles. These Roles
and Cluster Roles are bound to those service accounts using Role Bindings and
Cluster Role Bindings, respectively.

It is not too worth getting caught up with the difference between cluster roles
and normal roles, all that you need to know is that some .

### JupyterHub Admins
Permission here is straightforward, any admin can view the admin listing at
the admin page (e.g. https://comp20008-jh.eng.unimelb.edu.au/hub/admin ), and
then edit users to make them admins. An admin can immediately access all admin
functionality. This also grants you access to JupyterHub API actions, such as
group assignment and retrieval.

### JupyterHub Chart Admins
Permission here is granted by accessing the server head node, adding the
username to the list of usernames checked for admin status and then redeploying
the chart. I generally use this permission level for all management activities,
e.g. webserver admin, assignment setup, archive interaction & other management.

### Docker
Docker is mostly the same as when used locally. By specifying -u 0 when
executing a command, you can run it as root, which is useful for installing
software in a container temporarily (which can tighten the feedback loop during
development), or apply additional permissions (e.g. providing read-only
resources on the shared volume).
