# Archiving / Cleaning a JupyterHub Server for a New Semester
The simplest way to clean a JupyterHub Server is to tear down the server and
then rebuild from scratch, but sometimes additional tools and extensions might
have been set up beyond the default process and you might want to preserve
these.

The cleanup process is best performed in three steps.

1. Backup - Process through each volume on the server and collect the data
  stored into a single archive which can be downloaded.
2. User Selection - Select the users to remove from the server. Typically it
  makes sense to make this the set of users which aren't admins, which can be
  found and filtered using the JupyterHub API (see doc/01_jupyterhub_api.md). It
  is possible to extend this group using the group functionality of JupyterHub.
3. Deletion - Delete the volume of each selected users. It is worth verifying
  the contents of the archive before doing this.

## Backup
### NFS Deployment
Backup using NFS is fairly straightforward, simply log onto the data server,
move to the NFS share directory and run
`tar -zcvf $(date +'%Y%m%d')-clean-backup.tar.gz ./*/`, then extract the
clean-backup.tar.gz file.

### CephFS / General
Backing up a more decentralised system is best done with the assistance of that
system, so here we employ a five-step backup process.

1. Create a persistent volume claim (if not yet present). An example of this is
  in roles/tools/archive/queue/archive-pvc.yaml, which can be launched by
  uploading the file to the Kubernetes command node and running
  `kubectl create -f archive-pvc.yaml`.
2. Add this persistent volume claim to the JupyterHub admin users' attached
  volumes (see doc/03_jh_config.md).
3. Deploy a daemon (if not yet deployed) which listens for authorised commands
  on the 'backup-service' pipe and backs up that user's files to the pvc from
  step 2, an example can be launched by similar process to step 1, this time
  running `kubectl create -f archive-daemon.yaml` after uploading
  roles/tools/archive/queue/archive-daemon.yaml.
4. Send commands to backup all users (see doc/01_jupyterhub_api.md) encrypted
  with a private key.
5. Once completed, an admin can run the tar command on the attached storage from
  JupyterLab and download the file from there in much the same way.

The deployment is also focused on in roles/tools/archive/README.md

## User Selection
See doc/01_jupyterhub_api, get all users and filter by username. Store this list
somewhere and download it.

## Deletion
Deletion is a four step process.

1. Remove the user from JupyterHub through the JupyterHub API (see
  doc/01_jupyterhub_api)
2. Collect all Persistent Volumes tied to those users using kubernetes using
  awk and a query of the Persistent Volumes.
3. Delete all Persistent Volume Claims tied to any of the users to be deleted.
4. Delete all Persistent Volumes tied to any of the users to be deleted.

