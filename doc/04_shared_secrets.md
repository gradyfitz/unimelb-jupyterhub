# Adding Shared Secrets
Some tools might benefit from private keys, a clean way to handle these is
kubernetes managed secrets. These secrets are mounted as volumes somewhere on
the system.

## Creating Secrets
The creation process is pretty simple generally.

1. Create a key pair using normal RSA techniques.
2. Create these secrets from the server head node, an example of this which
  creates two secrets "ass-rsa-public" and "ass-rsa-private" from a public and
  private key also uploaded to the server (ass_rsa.public and ass_rsa.private,
  respectively).

## Mounting Secrets
Files given are stored in volumes, and these volumes are attached to pods in the
same way as all other volumes. The files the secrets were created from are
stored in the volume (so if the "ass-rsa-private" secret was mounted at
/etc/secret, you could find the file "ass_rsa.private" at
/etc/secret/ass_rsa.private).

An example of mounting these secrets can be seen at
roles/tools/archive/queue/archive-daemon.yaml, which is the standard attached
volume and volume mount.
