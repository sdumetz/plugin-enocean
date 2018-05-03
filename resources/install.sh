touch /tmp/dependancy_openenocean_in_progress
echo 0 > /tmp/dependancy_openenocean_in_progress
echo "********************************************************"
echo "*             Installation des dépendances             *"
echo "********************************************************"
apt-get update
echo 50 > /tmp/dependancy_openenocean_in_progress
apt-get remove -y python-enum
echo 60 > /tmp/dependancy_openenocean_in_progress
apt-get install -y  python-requests python-serial python-pyudev 
echo 75 > /tmp/dependancy_openenocean_in_progress
pip install enum-compat
echo 85 > /tmp/dependancy_openenocean_in_progress
pip install beautifulsoup4
echo 100 > /tmp/dependancy_openenocean_in_progress
echo "********************************************************"
echo "*             Installation terminée                    *"
echo "********************************************************"
rm /tmp/dependancy_openenocean_in_progress