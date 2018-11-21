#script that must somehow retrieve the photo of the plant
# structured so as to take as parameter the path of the dir containing all the dir of the photos of the plants
PATHPHOTOS=$1
NAME_SCRIPT=$(basename $0)
# To understand the plant name start from the script name in the form id_plant.sh using basename
IFS='.' # IFS is the separator character, which will then be used by the read command to create an array of elements
read -ra PLANT <<< $NAME_SCRIPT
DATE=$(date +"%Y%m%d%H%M")
PATH_OUT=$PATHPHOTOS/${PLANT[0]}/$DATE
#defined all the output is passed to the part of the script that actually retrieves the photo and goes to place it in PATH_OUT
raspistill -t 1  -o $PATH_OUT.jpg
# The output must be uniform for all these scripts, i.e. they must upload the photo in the folder photos/id_plant/ with naming YYYYMMDDHHMM.jpg
