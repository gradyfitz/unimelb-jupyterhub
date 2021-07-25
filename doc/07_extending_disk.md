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
  at /dev/vdb), if using xfs, you may need to run `sudo xfs_growfs /dev/vdb`
  instead.
7. Run the swapoff.sh script.

## Step 6 Notes
### Working Node by Node Tip
If you manually work on each node, you may be able to run a set of commands.
For example to also shift docker and the kubelet to the new disk space use the
following:
```bash
sudo swapoff -a
sudo xfs_growfs /dev/vdb
mkdir -p /etc/systemd/system/docker.service.d
sudo su -
echo "[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -g /mnt/cephdisk/ceph -H fd://
" > /etc/systemd/system/docker.service.d/docker.root.conf
sudo systemctl daemon-reload
sudo systemctl restart docker

# Do not do this until the ceph driver correctly handles this
# - https://github.com/intel/pmem-csi/issues/668
#echo "# /etc/sysconfig/kubelet
# KUBELET_EXTRA_ARGS=--root-dir=/mnt/cephdisk/ceph/k8s/kubelet
#" > /etc/default/kubelet

#sudo systemctl daemon-reload
#sudo systemctl restart kubelet
exit
exit
```

### Playing Nice with Ceph
Ceph will do a bit of work to manage the increase of disk space. There are a few
ways you can help this along.

- Before increasing disk space, remove as many old persistent volumes as you
  eventually will. The less data is sitting on the Ceph cluster, the easier it
  will be for Ceph to handle changing disk spaces.
- My recommendation, learning from past mistakes, is to increase the space one
  instance at a time, giving ample time for Ceph to rejuggle the data over the
  set of nodes (ideally the region of a day). Ceph needs to recover from any
  change that you make to the disk space.
- Further options include creating new devices and adding these to ceph's pools.
  Which is likely to be cleaner (additional osds will likely be created), though
  I haven't tried this. New storage triggers movement around the ceph cluster so
  I don't imagine too much difference.
