#fa uno sleep o un wait per 5 minuti, dopodichè effettua uno shutdown -h now in modo da fare un halt, di conseguenza non dovrebbero più esserci problemi che impedivano alla raspberry di spegnersi
sleep 5m
sudo shutdown -h now
