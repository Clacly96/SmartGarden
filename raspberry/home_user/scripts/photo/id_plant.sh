#script che deve recuperare in qualche modo la foto della pianta
# strutturato in modo da prendere come parametro il path della dir contente tutte le dir delle foto delle piante
PATHPHOTOS=$1
NAME_SCRIPT=$(basename $0)
# per capire il nome della pianta parto dal nome dello script nella forma id_pianta.sh usando basename
IFS='.' # IFS  è il carattere separatore, che poi verrà utilizzato dal comando read per creare un array di elementi
read -ra PLANT <<< $NAME_SCRIPT
DATE=$(date +"%Y%m%d%H%M")
PATH_OUT=$PATHPHOTOS/${PLANT[0]}/$DATE
#definito tutto l'output si passa alla parte dello script che recupera effettivamente la foto e la va a piazzare in PATH_OUT
raspistill -t 1  -o $PATH_OUT.jpg
# deve essere uniforme per tutti questi script l'output, cioè devono caricare la foto nella cartella foto/id_plant/ con naming YYYYMMDDHHMM.jpg
