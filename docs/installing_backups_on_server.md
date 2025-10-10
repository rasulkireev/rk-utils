If you have to run `sudo apt update && sudo apt upgrade -y`, make sure you follow the upgrading quide in this dir, so that the Caprover doesn't fail.

1. Bought a Storage box on Hetzner
2. `sudo apt install borgbackup borgmatic`
3. create ssh keys: `ssh-keygen -t ed25519 -f ~/.ssh/storagebox -C "caprover-backup"`
4. Copy the public key: `cat ~/.ssh/storagebox.pub` and insert into SSH key field
5.  test connection with `ssh -p 23 -i ~/.ssh/storagebox {user}@{storage_box_connection_string}`
6.  run:
```
export BORG_REPO='ssh://u123456@u123456.your-storagebox.de:23/./caprover-backup'
export BORG_PASSPHRASE='YourStrongPassphraseHere'
```

...

ok, redo steps 7-10. I did this without a passphrase initially, and apparently Borg requires it.

11. init BORG `borg init --encryption=repokey`
12. export the key `borg key export $BORG_REPO ~/borg-key-backup.txt`
13. Save it somewhere safe, not on the same server
14. Create borgmatic dir: `sudo mkdir -p /etc/borgmatic`
15. Generate config file: `sudo generate-borgmatic-config --destination /etc/borgmatic/config.yaml`
16. Configure the file: `sudo vim /etc/borgmatic/config.yaml`. My config will be stored here:
