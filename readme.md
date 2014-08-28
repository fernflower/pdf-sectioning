* Installation
There is a certain problem installing pyqt4 via virtualenv, could not figure out how to get around it yet.
By now everything is installed globally (yep, that sucks).

apt-get install python-poppler-qt4
apt-get install python-qt4
pip install -r requirements.txt

Perhaps a trick in http://stackoverflow.com/questions/1961997/is-it-possible-to-add-pyqt4-pyside-packages-on-a-virtualenv-sandbox may help to settle the matter.

* In order to start you need a config file, you can just copy offline-data/offline_config

cp offline-data/offline_config config
