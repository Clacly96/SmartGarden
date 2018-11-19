#ha dentro un ciclo for che lancia n volte il comando sync photos, necessario un ls per sapere quante e quali  cartelle vanno sincronizzate, valutare parametrizzazione path_key foto
PATH_PHOTOS=$1
OUT=$2 #sarebbe bucket/key
plants=($(ls $PATH_PHOTOS))
for plant in ${plants[@]}; do
  aws s3 sync $PATH_PHOTOS/$plant  s3://$OUT/$plant
done

# es, questo va fatto per ogni pianta
