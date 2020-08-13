# Extending the Available Disk Space for a Server
For this you will require a couple of things:

1. Research Cloud project permissions.
2. The private key used to perform changes on JupyterHub.

The process is straightforward enough (it should also be automatable, but I
would take care when data being lost could be an issue).

For each server which is going to have additional disk space added, complete the
following steps one server at a time:

1. Shutdown the instance (this might take a little bit of time).
2. Detach the volume for that server (Volume → Manage Attachments → Detach
  Volume)
3. Extend the volume (Volume → Extend Volume)
4. Reattach the volume to that server (Volume → Manage Attachments → Select the
  Server)
5. Start the instance again.
6. Resize the filesystem using `sudo resize2fs /dev/vdb` (if the filesystem is
  at /dev/vdb)
7. Run the swapoff.sh script.
