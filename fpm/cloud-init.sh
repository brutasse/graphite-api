# Run with cloud-init:
#
# #cloud-config
# runcmd:
#   - "wget https://raw.githubusercontent.com/brutasse/graphite-api/master/fpm/cloud-init.sh"
#   - "sh cloud-init.sh"

set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get -y upgrade
apt-get -y install git ruby ruby-dev build-essential
gem install fpm
git clone https://github.com/brutasse/graphite-api.git
cd graphite-api/fpm
./build-deb.sh
