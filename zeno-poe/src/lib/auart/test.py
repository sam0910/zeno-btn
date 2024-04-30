file_name = "/images/name.png"
bufarray = bytearray(128)
import gc

gc.collect()

with open(file_name, "rb") as file:
    while True:
        try:
            bufarray = file.read(128)
            blength = len(bufarray)
            print(blength, gc.mem_free())
            if not bufarray:
                print("End of file", bufarray)
                break
        except Exception as e:
            pass

        # finally:
        #     file.close()
        #     print("File closed")

gc.collect()
print("End of program", gc.mem_free())
