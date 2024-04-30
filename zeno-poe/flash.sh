source $FW/esp-idf/export.sh
clear

DEVICE_PORT=$(ls /dev/cu.usbserial* 2>/dev/null | head -n 1)
if [ -z "$DEVICE_PORT" ]; then
    echo "No device port found. Please connect your device and try again."
    exit 1
fi

ls -al /dev/cu.usbserial-*
while true; do
    echo -n -e "Enter Device Port (default: $DEVICE_PORT): "
    read user_input

    if [ -z "$user_input" ]; then
        DEVICE_PORT=$DEVICE_PORT
        break
    elif [[ ! "$user_input" =~ ^[0-9]+$ ]]; then
        echo "Invalid input. Please enter a number."
    else
        DEVICE_PORT=/dev/cu.usbserial-$user_input
        break
    fi
done

echo "DEVICE_PORT is $DEVICE_PORT ..."
echo ""
esptool.py --chip esp32 --port $DEVICE_PORT --baud 460800 write_flash -z 0x1000 ./bin/mpy_olimex.bin