# Archive Tool for JupyterHub
This tool is similar to the submit system offering backup and volume delete
capabilities.

## How to set up
1. If it hasn't been set up before, set up the redis service using the
  instructions in roles/tools/submit-pod/README.md (steps (1), (2), (3)).
2. If the permissions haven't been applied before, grant the permissions as
  described in roles/tools/permissions/README.md
3. Copy queue/archive-daemon.yaml and queue/archive-pvc.yaml to the head server
  node.
4. Run `kubectl create -f archive-daemon.yaml`
5. Run `kubectl create -f archive-pvc.yaml`

## How to use
Send a message to the redis queue "archive", encrypted with the public key in
roles/tools/submit-pod/secrets of one of the following formats:

A backup request
```json
{
  "backup": "username"
}
```

A delete volume request
```json
{
  "delete_pvc": "username"
}
```

The backup request zips the contents of the given user's volume and stores it
in the backup volume. The delete request deletes the volume for the user
specified permanently, reclaiming that space.
