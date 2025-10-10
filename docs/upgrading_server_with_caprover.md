1. Server is located on Hetzner. Server's main purpose is to run Caprover.
3. Run `sudo apt update && sudo apt upgrade -y`
1. After rebooting Caprover seems to have issues with starting up...
4. After restarting the docker service everything went fine after a while: `sudo systemctl restart docker`
5. I think at some point I ran scale 0 and the whole caprover site failed... Make sure to run this: `docker service scale captain-nginx=1`
6.
