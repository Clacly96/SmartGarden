#deve lanciare tutti gli script presenti nella dir script_photo dove per ogni pianta c'è uno script che si chiama come la pianta
path_script=$1
path_photos=$2
cd $path_script
script_photo=$(ls photo)
cd photo # mi posiziono nella cartella dove sono presenti gli script per recuperare le foto
for script in ${script_photo[@]}; do
  ./$script $path_photos
done
